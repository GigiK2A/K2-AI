# Skill: teaser-check

Leggi questo articolo come se fossi un imprenditore PMI italiano
tecnico, capace di implementare cose se gli vengono spiegate bene.

Rispondi SOLO in JSON:

```json
{
  "could_implement_alone": true|false,
  "reason": "spiega in 1-2 frasi cosa hai capito che ti permette (o non permette) di implementare la cosa da solo",
  "leaked_details": ["lista di dettagli specifici che l'articolo svela che NON dovrebbe svelare", ...]
}
```

Regole:

- Se l'articolo svela **come configurare**, **quali API chiamare**,
  **quale prompt usare**, **quale tool specifico installare con quale
  parametro** → `could_implement_alone: true`.

- Se l'articolo descrive solo **cosa è il problema**, **perché soluzioni
  generiche non bastano**, **che tipo di sistema serve in generale**
  (senza dettagli operativi) → `could_implement_alone: false`. Questo è
  l'output desiderato.

- Se l'articolo descrive un caso cliente, va bene; ma se descrive
  l'architettura ESATTA che ha implementato lo studio cliente (con
  endpoint, parametri, codice) → `could_implement_alone: true`.

Non aggiungere commento fuori dal JSON.
