# Stripe webhook — attivazione post-deploy

Il backend espone `POST /api/webhooks/stripe` (pubblico, senza autenticazione).
La rotta verifica la firma `Stripe-Signature` con la SDK ufficiale e fa upsert
su `board_revenue_events` (idempotente su `external_id`).

Eventi gestiti:

| Stripe event                  | Azione su `board_revenue_events`    |
| ----------------------------- | ----------------------------------- |
| `payment_intent.succeeded`    | upsert con `status='succeeded'`     |
| `payment_intent.payment_failed` | upsert con `status='failed'`      |
| `charge.refunded`             | upsert (PI id) con `status='refunded'` |

## Passi per Luigi (una sola volta, dopo il deploy del backend)

1. **Stripe Dashboard** → *Developers* → *Webhooks* → **Add endpoint**.
2. **Endpoint URL**:
   ```
   https://board-api.k2-ai.it/api/webhooks/stripe
   ```
3. **Events to send** — seleziona:
   - `payment_intent.succeeded`
   - `payment_intent.payment_failed`
   - `charge.refunded`
4. Clicca **Add endpoint**.
5. Nella pagina dell'endpoint appena creato, sezione *Signing secret*, premi
   **Reveal** e copia il valore (`whsec_...`).
6. Su **Railway** → service `k2-board-api` → *Variables* → aggiungi:
   ```
   STRIPE_WEBHOOK_SECRET=whsec_...
   ```
7. Railway ridepoia automaticamente. Aspetta che lo stato torni *Active*.
8. Torna su Stripe → endpoint → **Send test webhook** → scegli
   `payment_intent.succeeded` → conferma. Deve rispondere **200**.
9. Verifica su Supabase: una nuova riga in `board_revenue_events` con
   `external_id = pi_...` e `status = succeeded`.

## Troubleshooting

- **400 invalid_signature** — `STRIPE_WEBHOOK_SECRET` errato o non
  ridepoiato. Controlla che la variabile sia esattamente quella mostrata
  dal dashboard Stripe (incluso il prefisso `whsec_`).
- **503 stripe_webhook_secret_not_configured** — la variabile non è stata
  impostata su Railway. Vedi step 6.
- **200 ma nessuna riga in DB** — controlla che la tabella
  `board_revenue_events` abbia un indice unico su `external_id` (necessario
  per l'upsert). I log struttural del backend (Railway → Logs) tracciano
  ogni evento con `stripe.webhook.received`.

## Test locale (sviluppo)

```bash
# Inoltra eventi dal tuo account Stripe alla macchina locale
stripe listen --forward-to localhost:8000/api/webhooks/stripe
# Imposta nel .env locale il signing secret restituito dal comando sopra
# (è diverso da quello di produzione, formato whsec_...)
```
