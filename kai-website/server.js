const http = require('http');
const fs = require('fs');
const path = require('path');

const PORT = process.env.PORT || 4173;
const DIST_DIR = path.join(__dirname, 'dist');
const REDIRECT_HOST = 'k2-ai.it';
const CANONICAL_HOST = 'www.k2-ai.it';

const MIME_TYPES = {
  '.html': 'text/html; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.js': 'application/javascript; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.jpeg': 'image/jpeg',
  '.svg': 'image/svg+xml',
  '.ico': 'image/x-icon',
  '.mp4': 'video/mp4',
  '.woff': 'font/woff',
  '.woff2': 'font/woff2',
  '.ttf': 'font/ttf',
  '.map': 'application/octet-stream'
};

function normalizeHost(req) {
  const xfHost = req.headers['x-forwarded-host'];
  const host = (xfHost || req.headers.host || '').split(',')[0].trim();
  return host.toLowerCase();
}

function shouldRedirect(host) {
  return host === REDIRECT_HOST || host.startsWith(`${REDIRECT_HOST}:`);
}

function send(res, status, headers, body) {
  res.writeHead(status, headers);
  res.end(body);
}

function serveFile(req, res, filePath) {
  fs.stat(filePath, (statErr, stats) => {
    if (statErr || !stats.isFile()) {
      send(res, 404, { 'Content-Type': 'text/plain; charset=utf-8' }, 'Not found');
      return;
    }

    const ext = path.extname(filePath).toLowerCase();
    const contentType = MIME_TYPES[ext] || 'application/octet-stream';
    const range = req.headers.range;

    if (range) {
      const match = range.match(/bytes=(\d*)-(\d*)/);
      const start = match && match[1] ? parseInt(match[1], 10) : 0;
      const end = match && match[2] ? parseInt(match[2], 10) : stats.size - 1;

      if (!match || start >= stats.size || end >= stats.size || start > end) {
        send(res, 416, { 'Content-Range': `bytes */${stats.size}` }, '');
        return;
      }

      res.writeHead(206, {
        'Content-Type': contentType,
        'Content-Length': String(end - start + 1),
        'Content-Range': `bytes ${start}-${end}/${stats.size}`,
        'Accept-Ranges': 'bytes'
      });
      fs.createReadStream(filePath, { start, end }).pipe(res);
      return;
    }

    fs.readFile(filePath, (err, data) => {
    if (err) {
      send(res, 404, { 'Content-Type': 'text/plain; charset=utf-8' }, 'Not found');
      return;
    }
      send(res, 200, {
        'Content-Type': contentType,
        'Content-Length': String(stats.size),
        'Accept-Ranges': 'bytes'
      }, data);
    });
  });
}

const server = http.createServer((req, res) => {
  const host = normalizeHost(req);
  if (shouldRedirect(host)) {
    const location = `https://${CANONICAL_HOST}${req.url || '/'}`;
    send(res, 301, { Location: location }, '');
    return;
  }

  let urlPath = (req.url || '/').split('?')[0];
  if (urlPath === '/') {
    urlPath = '/index.html';
  }

  const safePath = path.normalize(urlPath).replace(/^(\.\.[/\\])+/, '');
  const filePath = path.join(DIST_DIR, safePath);
  serveFile(req, res, filePath);
});

server.listen(PORT, '0.0.0.0', () => {
  console.log(`K2-AI website listening on ${PORT}`);
});
