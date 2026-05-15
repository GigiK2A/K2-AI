-- H-6: prevent anonymous-session takeover.
-- Anyone who guesses/learns a session UUID could call POST /session/{id}/link-user
-- and claim it. We now require a `link_token` (random secret) returned to the
-- browser at session-creation time; link-user must present a matching token.

ALTER TABLE kbot_sessions
  ADD COLUMN IF NOT EXISTS link_token TEXT;

-- Tokens are random 32-byte URL-safe strings; no index needed (lookups go
-- through id first, then compare token in app code with constant-time compare).

-- H-7: short-lived opaque token for Stripe success_url, so the kbot session
-- UUID never leaks to referrers via query params.
ALTER TABLE kbot_sessions
  ADD COLUMN IF NOT EXISTS success_token TEXT;
