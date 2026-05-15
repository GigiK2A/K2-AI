# Google Calendar — sync (stub)

> **Stato**: stub. La sync reale arriva con lo Sprint 9 (agente Giuseppina).
> Questo documento descrive cosa servirà per accenderla.

## Cosa è già pronto

- `app/services/calendar_sync.py` — funzione `sync_meetings_from_google()`
  segnaposto che alza `NotImplementedError`.
- Settings stub in `app/settings.py`:
  - `GOOGLE_CLIENT_ID`
  - `GOOGLE_CLIENT_SECRET`
  - `GOOGLE_REFRESH_TOKEN`

## Cosa serve aggiungere (Sprint 9+)

1. **OAuth client su Google Cloud Console**
   - Crea un progetto (o riusa uno esistente).
   - Abilita *Google Calendar API*.
   - *Credentials* → *Create credentials* → *OAuth client ID* → *Web application*.
   - Authorized redirect URI: `https://board-api.k2-ai.it/api/integrations/google/callback`
     (rotta da implementare).
   - Copia `client_id` e `client_secret` → variabili Railway omonime.

2. **Scopes minimi**
   - `https://www.googleapis.com/auth/calendar.readonly`
   - `https://www.googleapis.com/auth/calendar.events.readonly`

3. **Refresh token (one-shot)**
   - Flusso OAuth da consenso una tantum su account `luigi@k2-ai.it`.
   - Salvare il `refresh_token` in `GOOGLE_REFRESH_TOKEN` (Railway env).

4. **Dipendenze Python da aggiungere**
   ```
   google-api-python-client>=2.140
   google-auth>=2.34
   google-auth-oauthlib>=1.2
   ```
   *Volutamente NON in `requirements.txt` finché non è il momento — per
   tenere l'immagine leggera.*

5. **Implementazione `sync_meetings_from_google()`**
   - Costruisce un client `build("calendar", "v3", credentials=...)`.
   - `events.list(calendarId="primary", timeMin=now, maxResults=50, singleEvents=True, orderBy="startTime")`.
   - Upsert su `board_meetings` (key: `external_id = event.id`).
   - Schedule: chiamata ogni 15 minuti via cron job Railway.

6. **Rotta di callback OAuth** (`app/api/integrations.py` da creare)
   - `GET /api/integrations/google/start` → redirect su consent screen.
   - `GET /api/integrations/google/callback` → scambia code per token, salva
     refresh token (manuale o cifrato in DB).

## Perché stub ora

La sincronizzazione è un asset Sprint 9 (Giuseppina). In questo Sprint
basta non rompere import e tenere lo spazio nello schema settings, così
quando si accende non servono migrazioni.
