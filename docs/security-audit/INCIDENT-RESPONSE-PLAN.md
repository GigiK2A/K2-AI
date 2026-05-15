# K2-AI — Incident Response Plan

Last review: 2026-05-15.
Owner: Luca (rluigiluca@gmail.com).
Scope: kai-website, kbot backend, ai-board, any production infrastructure
(Supabase, Railway, Vercel, Stripe, Resend, Anthropic, Notion).

## 1. What counts as an incident

An **incident** is any event that affects (or has credible potential to affect)
the confidentiality, integrity, or availability of K2-AI systems or user data.
Examples (non-exhaustive):

- Leaked credential (API key, DB password, JWT secret) in a public place
  (GitHub, Discord, Slack screenshot, Stack Overflow paste).
- Suspected or confirmed data breach (unauthorized access to Supabase data,
  Notion workspace, customer email/PII).
- Website defacement, malicious code injected into the site or skill bundle.
- Sustained downtime > 4h on production (k2-ai.it, kbot, ai-board).
- Cost-abuse: anomalous API spend (Anthropic, Stripe, Resend) exceeding
  daily baseline by ≥ 5× — signal of credential misuse or infinite loop.
- Stripe disputes / fraud spike (≥ 3 chargebacks in 24h).
- Repeated successful exploits of SSRF, RCE, or auth-bypass attempts logged
  by `app/lib/url_fetcher.py` or rate-limit / CSP violation reports.

If unsure → treat it as an incident and triage. Erring on the side of "yes,
it's an incident" is cheaper than missing one.

## 2. Severity classes

| Class | Definition                                                                                            | Response                       | Comms cadence |
| ----- | ----------------------------------------------------------------------------------------------------- | ------------------------------ | ------------- |
| **P0** | Active data breach in progress, RCE confirmed, customer PII confirmed exfiltrated, payments rerouted. | Drop everything, < 15 min ack. | Hourly        |
| **P1** | Service down (all of k2-ai.it / kbot / ai-board), leaked production credential, abuse causing > 100€/h spend. | < 1h ack, fix-or-mitigate < 4h. | Every 4h     |
| **P2** | Single endpoint broken, partial degradation, leaked low-impact credential (rotated by procedure), suspicious activity not confirmed. | < 4h ack, fix < 24h.           | Daily         |
| **P3** | Non-urgent: stale dep with no known exploit path, low-CVSS vuln, cosmetic data leak (e.g. internal log line). | Next business day.             | At resolution |

GDPR Art. 33 requires notifying the **Garante per la protezione dei dati personali**
within **72 hours** of becoming aware of a personal-data breach that is likely
to result in risk to data subjects. Any P0 or P1 involving user PII triggers
the 72-hour clock immediately.

## 3. Procedure (D-T-C-E-R-P)

### 3.1 Detect

Signals to monitor:

- **PostHog**: error-rate spikes, drop in conversion funnel.
- **Sentry** (`SENTRY_DSN` env, optional): exception bursts on kai-website /
  kbot / ai-board.
- **Railway** alerts: container restart loops, OOM, deploy failures.
- **Supabase** dashboard: slow queries, abnormal row counts, auth log spikes.
- **Stripe**: webhook failure alerts, chargeback notifications.
- **Anthropic console**: daily spend, rate-limit hits.
- **`/api/admin/alert` endpoint**: internal alerts (rate-limit-spike, SSRF
  block triggered, repeated 5xx) → Slack `#alerts` / Telegram chat.
- **External**: user emails to support@k2-ai.it, GitHub security advisories,
  gitleaks scheduled run.

### 3.2 Triage (first 15 min)

Write this down (in a Notion page or scratch doc) — speed matters but a paper
trail matters more.

- **What happened**: one-sentence description.
- **When detected**, **when started** (if known).
- **Severity** (P0–P3).
- **Blast radius**: which systems, how many users, what data.
- **Incident commander** (IC): one named person. For a solo founder, this is Luca.
- **Scribe**: same person if solo; otherwise a separate hand.

Open a dedicated Slack channel `#inc-YYYYMMDD-<slug>` (or a Notion page) for
the running log.

### 3.3 Contain (< 1h for P0/P1)

Goal: stop the bleeding, even if it means accepting downtime.

- Suspected leaked credential → **rotate first, investigate later**.
  See `SECRET-ROTATION-PROCEDURE.md` for per-service steps.
- Suspected compromised host → take it offline (Railway service → stop
  service; Vercel → disable deployment).
- Suspected DB compromise → revoke service-role key, rotate, set Supabase
  project to read-only mode if PII is at risk.
- Stripe abuse → disable the Payment Link in Stripe dashboard.
- DNS / domain hijack → contact registrar (Aruba / current registrar) support
  immediately, set domain lock.

### 3.4 Eradicate

Patch the root cause — not just the symptom.

- Code fix → branch `hotfix/<incident-id>`, PR with description, deploy after
  CI green. For P0, the IC can self-merge with a follow-up review.
- Config fix → update env vars in Railway / Vercel, redeploy.
- Permission fix → tighten RLS, tighten IAM, revoke compromised keys.

### 3.5 Recover

- Re-enable services in reverse order of containment.
- Restore from backup if data was destroyed (`docs/security-audit/BACKUP-PROCEDURE.md`).
- Run smoke tests: kbot chat works, contact form submits, Stripe checkout
  completes, ai-board dashboard loads.
- Monitor for 24h before declaring "incident closed".

### 3.6 Post-mortem (within 5 business days)

Required for every P0 and P1. Optional for P2, recommended.

Template: `docs/security-audit/postmortems/YYYYMMDD-<slug>.md`. Sections:

1. **Summary** (4 lines max).
2. **Timeline** (UTC, every event from first signal to closure).
3. **Impact** (users, data, money, reputation).
4. **Root cause** (5 whys).
5. **What went well**.
6. **What went badly**.
7. **Action items** (each: owner + due date + tracking issue).
8. **Detection lag** (time from start → detect → mitigate → resolve).

**Blameless rule**: post-mortems describe failures of systems and process,
not of people. Names of who-did-what go in if relevant, but only with
neutral language ("X deployed Y at T" not "X carelessly deployed").

## 4. First-hour checklist

Print this. Tape it next to the laptop.

- [ ] T+0 min — Acknowledge alert / read user report. Note current UTC time.
- [ ] T+2 min — Assign severity (P0/P1/P2/P3). Document where.
- [ ] T+5 min — Open running-log doc / Slack channel.
- [ ] T+10 min — Determine blast radius. Anyone need to be told *right now*?
- [ ] T+15 min — If P0/P1 and a credential is suspect: **rotate it now**.
- [ ] T+20 min — Pull logs from PostHog / Railway / Sentry / Supabase audit.
- [ ] T+30 min — Identify mitigation (revert deploy, kill service, rate-limit,
       feature-flag off). Apply.
- [ ] T+45 min — Verify mitigation worked (smoke test).
- [ ] T+60 min — If GDPR-relevant: start drafting Garante notification
       (deadline: T+72h).

## 5. Contacts

| Service / role         | Contact                                                          |
| ---------------------- | ---------------------------------------------------------------- |
| Anthropic support      | https://support.anthropic.com (or email via console)             |
| Stripe support         | https://support.stripe.com (live chat 24/7 for Italy)            |
| Supabase support       | support@supabase.com (priority via dashboard for paid plans)     |
| Railway support        | help@railway.app or in-dashboard chat                            |
| Vercel support         | https://vercel.com/help                                          |
| Resend support         | support@resend.com                                               |
| Notion support         | https://www.notion.so/help/contact-support                       |
| **Garante Privacy IT** | protocollo@gpdp.it / +39 06 696771 / https://servizi.gpdp.it/    |
| Legale (GDPR + 231)    | _da definire — Luca, scegliere studio prima del prossimo incidente_ |
| DNS registrar          | Aruba customer care +39 0575 0500                                |

## 6. GDPR Art. 33 — breach notification template

If a personal-data breach occurs (i.e. accidental or unlawful destruction,
loss, alteration, unauthorized disclosure of, or access to personal data),
and it is **likely to result in a risk to the rights and freedoms of natural
persons**, notify the Garante within 72 hours of becoming aware.

The notification must include (Art. 33 §3):

1. Nature of the breach, categories and approximate number of data subjects
   affected, categories and approximate number of records.
2. Name + contact of the DPO (or other contact point).
3. Likely consequences.
4. Measures taken or proposed to address the breach and mitigate effects.

Use the Garante online form: https://servizi.gpdp.it/databreach/

## 7. User notification template (Italian)

Used when Art. 34 requires notifying affected users (high risk to rights and
freedoms). Email subject: `Comunicazione importante sui tuoi dati K2-AI`.

```
Ciao [Nome],

Ti scrivo per comunicarti che il [data] abbiamo rilevato un evento di sicurezza
che ha riguardato i tuoi dati personali in K2-AI.

Cosa è successo: [descrizione neutra, fattuale]

Quali dati sono stati interessati: [elenco]

Cosa abbiamo fatto: [misure adottate]

Cosa puoi fare tu: [es. cambia password, controlla movimenti carta]

Abbiamo notificato l'evento al Garante per la protezione dei dati personali
in conformità all'art. 33 del Regolamento UE 2016/679.

Per qualsiasi domanda: rluigiluca@gmail.com.

K2A S.R.L.S.
P.IVA IT03655920548
```

## 8. Review

This plan is reviewed:

- After every P0 or P1 incident.
- At least once per year (calendar reminder on 15 May).
- Whenever new infrastructure is added (e.g. a new SaaS vendor, a new
  data-processing flow).
