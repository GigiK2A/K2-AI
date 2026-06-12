# Report sicurezza + debug — motore 8e e gate K-BOT

**Data**: 2026-06-08 · **Scope**: superficie nuova (motore 8e, gate erogazione W8, entitlement JWT, tabelle Supabase nuove).

---

## 1. Vulnerabilità trovate e CORRETTE

### V-1 (ALTA) — `kbot_preview_consume` eseguibile da utenti via REST
**Trovata da**: Supabase security advisor (`anon_security_definer_function_executable`).
La funzione `SECURITY DEFINER` era chiamabile da `anon`/`authenticated` via
`/rest/v1/rpc/kbot_preview_consume` con `p_user`/`p_limit` arbitrari → un utente
autenticato poteva **manipolare il contatore preview di altri utenti** o
**alzarsi il proprio limite** (`p_limit=9999`), bypassando il gate.
**Fix**: `REVOKE EXECUTE FROM PUBLIC, anon, authenticated` + `GRANT TO service_role`.
Solo il backend (service_role) la invoca. Verificato: lint sparito.

### V-2 (MEDIA) — `search_path` mutabile su SECURITY DEFINER
**Trovata da**: advisor (`function_search_path_mutable`).
Senza `search_path` fisso, una funzione `SECURITY DEFINER` è esposta a
search-path hijacking (privilege escalation).
**Fix**: `SET search_path = public, pg_temp`. Verificato: lint sparito.

Entrambe applicate su Supabase via MCP + riflesse in `migration 005`.

---

## 2. Test di sicurezza 8e — 21/21 PASS (`tests/security_test.py`)

| Categoria | Check |
|---|---|
| **Auth Bearer** | no-auth→401, wrong-key→403, malformed→401 |
| **Entitlement forgery** | valido→202, assente→402, firma-falsa→402, scaduto→402, service-mismatch→402, **alg=none→402**, wrong-aud→402 |
| **Path traversal / injection** | `../../etc/passwd`, `'; DROP TABLE--`, `service/../x` → tutti 422 out_of_catalog (catalogo chiuso) |
| **Gate erogazione** | PREVIEW senza entitlement→202; **PREVIEW non produce PDF (no leak del completo)**; PREVIEW nasconde contenuto (solo titoli); auth_level ignoto→400 |
| **Robustezza** | job inesistente→404, input oversize (200KB)→no 500, prompt-injection negli input→no 500 |

Punti di forza confermati:
- **Catalogo chiuso** (route-or-refuse) neutralizza path traversal e SQLi sul `service_id`.
- **Entitlement JWT HS256** resiste a forgery, replay scaduto, downgrade `alg=none`, mismatch servizio/audience.
- **No-leak preview**: il livello è deciso prima della composizione → l'LLM non vede mai il documento completo in modalità preview.

---

## 3. Entitlement JWT (G1) — verifica unitaria

`app/entitlement.py` (8e) verifica firma + `exp` + `aud=k2a-8e` + `iss=k2a-kbot`
+ `service_id` corrispondente. Test: valido OK; mismatch/scaduto/firma-falsa/
vuoto/alg=none tutti rifiutati. Segreto condiviso `K2A_ENTITLEMENT_SECRET`
(da configurare in produzione, ≥32 byte).

---

## 4. RLS tabelle nuove — OK

- `kbot_purchases`: RLS on, policy `select own` (auth.uid()=user_id). INSERT/UPDATE solo service_role.
- `kbot_preview_usage`: RLS on, policy `select own`. Scrittura solo via funzione hardened (service_role).
- Nessuna delle due compare nei lint `rls_enabled_no_policy` → policy presenti.

---

## 5. Debug / robustezza engine

- **`tests/test_all_boosts.py`**: resolve + L1 su **11 boost** (oltre LegalBoost) → PASS. Valida i path `normativo`/`formula`/`input`/`benchmark`.
- **`tests/smoke_test.py`**: LegalBoost end-to-end (routing→resolve→filiera→L1/L2→output-schema→PDF) → PASS.
- **Filiera resiliente**: risposta Sonnet troncata/JSON incompleto → fallback deterministico (mai deliverable invalido). `route-or-refuse` sul singolo dato deterministico.
- **Stateless**: l'8e regge job concorrenti (job store in-memory per Phase-1; Phase-2 storage esterno).

---

## 6. Finding PRE-ESISTENTI (NON miei) — da girare a Luca

Advisor segnala su Supabase KAI, **fuori dal mio scope** (progetto ai-board/AIOS):
- **~37 tabelle** `aios_*`, `board_*`, `employees`, `invoices`, `legal_documents`, `vendors`… con **RLS abilitato ma NESSUNA policy** → di fatto inaccessibili via API (deny-by-default, "safe" ma probabilmente non intenzionale: quelle tabelle sono inutilizzabili dal client). Da verificare se serve aggiungere policy o se sono solo server-side.
- `extension_in_public` (`pg_trgm` nello schema public) — best practice: spostare.
- `auth_leaked_password_protection` **disabilitato** — consigliato abilitare (check HaveIBeenPwned sulle password).

---

## 7. Aperti / raccomandazioni

1. **Segreto entitlement** `K2A_ENTITLEMENT_SECRET` da generare (≥32 byte) e settare identico in K-BOT backend + 8e (env Railway).
2. **Rate-limiting 8e**: aggiungere rate-limit per chiave Bearer (il K-BOT ha slowapi; l'8e no) — anti-abuse su `/v1/deliverables`.
3. **jti anti-replay**: il claim `jti` è emesso ma l'8e non tiene un registro dei jti usati (stateless). Per Phase-1 ok (exp 15min limita la finestra); Phase-2 valutare cache jti se serve single-use stretto.
4. **Storage cross-service (G2)**: ancora aperto — definire se l'8e ritorna bytes o usa signed-URL del K-BOT (mai service_role del K-BOT nell'8e).
