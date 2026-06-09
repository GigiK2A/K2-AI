# Per Luca — cosa ti resta davvero sul grounding (verificato sui dati)

Ho classificato tutti i 12 boost per *tipo di ancoraggio* leggendo i placeholder reali nello snapshot. La conclusione: **non devi groundare 9 boost**. Ti resta molto meno.

## Copertura reale dei 12

**🟢 Già groundati a norma (verbatim nello snapshot) — 5**
- Legal, Fisco, Safety (pilota) + **BuildBoost** (4 art. `akn_bulk_xml`) + **MEPBoost** (4 art. `override_locale`).
- Su questi: solo **QA vigenze** come hai fatto sul fisco. Build/MEP non li avevi verificati — un check rapido e sono chiusi.

**🔵 Non normativi — a calcolo/formula (dominio Luigi, già nel motore) — 4**
- FinanceBoost (9 formule), ControlBoost (5 formule), AdvisorBoost (2 formule + OIC), StrategyBoost (framework).
- Zero `normativo` nei placeholder: l'ancoraggio è la **formula deterministica nel motore**, non il tuo snapshot. **Non sono lavoro tuo.** (Coerente con quanto dicevi su Advisor: OIC + calcolo, non citazione statutaria.)

**🟡 Servono DATI, non leggi (benchmark) — 2**
- HostBoost → dataset **RevPAR di zona** (`revpar_zona`, oggi gap dichiarato).
- WebBoost/SEO → dataset **keyword** (`keyword_dataset`, gap dichiarato).
- Sono i 2 unici gap nella coverage (55/57). Servono dataset, non grounding normativo — li fornisci tu o una fonte dati, *se* mettiamo questi 2 nel lancio.

**🔴 Decisione di design — 1**
- AgevolazioniBoost: 0 fatti, è **time-bound** (D-047). I numeri (iperammortamento 2026, ecc.) vanno da fonte datata con freshness-gate, **non** congelati nello snapshot. Da decidere insieme come trattarlo — non groundarlo come Legal.

## Quindi a te restano SOLO 3 cose
1. **QA vigenze su Build + MEP** (rapido, come sul fisco).
2. I **2 dataset benchmark** (RevPAR, keyword) — solo se Host/SEO entrano nel lancio.
3. **Scelta su Agevolazioni** (time-bound: come lo gestiamo).

## Cosa NON ti serve fare
- Groundare Finance/Advisor/Control/Strategy → sono a calcolo, motore mio.
- Rifare Fisco/Safety/Legal → già fatti e ora **freshness-gated in CI** (7/7).

## Dalla mia parte (Luigi)
- Iniezione verbatim già attiva (appendice "Testi normativi" confermata su PDF reale).
- Freshness-gate in CI.
- Determinismo formule per i 4 a calcolo (motore).
- Manca solo l'URL 8e a deploy.

**Pilota go-live (Legal+Fisco+Safety) non dipende da nulla di tutto questo: è pronto.** Il resto è la roadmap per estendere oltre il pilota.
