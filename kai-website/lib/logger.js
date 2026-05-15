// lib/logger.js — minimal structured logger for kai-website (Node).
//
// Usage:
//   const log = require('./lib/logger');
//   log.info('newsletter.subscribe', { email_hash: h, ip });
//   log.warn('rate_limit.hit', { endpoint, key, bucket });
//   log.error('handler.crashed', { err: String(err), stack: err.stack });
//
// In production (LOG_FORMAT=json or NODE_ENV=production) the output is
// single-line JSON on stderr/stdout. Locally (LOG_FORMAT=pretty) it falls
// back to console.* so dev output stays readable.
//
// Also exposes captureException(err, extra) which forwards to Sentry when
// SENTRY_DSN is configured, otherwise no-ops.

'use strict';

const LEVEL_PRIORITY = { debug: 10, info: 20, warn: 30, error: 40 };
const CONFIGURED_LEVEL = (process.env.LOG_LEVEL || 'info').toLowerCase();
const MIN_LEVEL = LEVEL_PRIORITY[CONFIGURED_LEVEL] ?? 20;
const USE_JSON =
  (process.env.LOG_FORMAT || (process.env.NODE_ENV === 'production' ? 'json' : 'pretty'))
    .toLowerCase() === 'json';

let sentry = null;
const SENTRY_DSN = (process.env.SENTRY_DSN || '').trim();
if (SENTRY_DSN) {
  try {
    // eslint-disable-next-line global-require
    sentry = require('@sentry/node');
    sentry.init({
      dsn: SENTRY_DSN,
      environment: process.env.APP_ENV || 'production',
      release: process.env.APP_RELEASE || 'kai-website@local',
      tracesSampleRate: Number(process.env.SENTRY_TRACES_SAMPLE_RATE || 0),
      // PII off by default — never auto-attach user emails or request bodies.
      sendDefaultPii: false,
    });
  } catch (err) {
    // eslint-disable-next-line no-console
    console.warn('[logger] SENTRY_DSN set but @sentry/node not installed:', err.message);
    sentry = null;
  }
}

function emit(level, event, fields) {
  if ((LEVEL_PRIORITY[level] ?? 0) < MIN_LEVEL) return;
  const payload = {
    ts: new Date().toISOString(),
    level,
    msg: event,
    ...(fields && typeof fields === 'object' ? fields : {}),
  };
  const line = USE_JSON ? JSON.stringify(payload) : `[${level}] ${event} ${JSON.stringify(fields || {})}`;
  if (level === 'error') {
    // eslint-disable-next-line no-console
    console.error(line);
  } else if (level === 'warn') {
    // eslint-disable-next-line no-console
    console.warn(line);
  } else {
    // eslint-disable-next-line no-console
    console.log(line);
  }
}

module.exports = {
  debug: (event, fields) => emit('debug', event, fields),
  info: (event, fields) => emit('info', event, fields),
  warn: (event, fields) => emit('warn', event, fields),
  error: (event, fields) => emit('error', event, fields),
  captureException(err, extra) {
    if (sentry) {
      try {
        sentry.captureException(err, { extra });
      } catch (_) {
        /* ignore — Sentry must never crash the host */
      }
    }
    emit('error', 'exception', {
      err: err && err.message ? err.message : String(err),
      stack: err && err.stack ? err.stack.split('\n').slice(0, 10).join('\n') : undefined,
      ...(extra || {}),
    });
  },
  sentryEnabled: Boolean(sentry),
};
