# Re-run AdvisorBoost col quant vero — report per Luca

> Da: Luigi · Stato: **quant cablato + correttezza deterministica verificata; live run (varianza/token/latenza) bloccato su chiave+crediti**.

## TL;DR

Ho cablato i 4 tool reali nel ramo AdvisorBoost del PoC e imposto il contratto assunzioni con l'hook. La **correttezza dei numeri** (la metà che si misura senza agente) è verificata sui 4 casi: ke ragionevoli per settore, il recinto fa OK/WARN/FAIL come deve, il g-guard rifiuta g fuori range. La **varianza dell'orchestrazione + token/latenza** (l'altra metà) ha bisogno del live run, **bloccato qui**: in questo repo manca `.env.local` (niente `ANTHROPIC_API_KEY`) e i crediti erano esauriti. Il batch è pronto a un comando appena ho chiave+crediti.

Due note di onestà, sotto.

---

## 1. Cosa ho cablato (swap quant-lite → quant vero)

Solo nel ramo **AdvisorBoost** (`k2a-8e-agent-poc/`). K-BOT live e Boost compilativi intatti, entitlement/paywall nel backend.

- `quant_server.py`: i 4 tool reali sostituiscono gli shim quant-lite:
  - `capm_cost_of_equity` — ke con Hamada + CAPM + size, **beta/rf/erp/size dallo snapshot** (l'agente non li passa più).
  - `ev_from_multiples` — EV da multiplo di settore (snapshot Damodaran).
  - `valida_assunzioni` — il **recinto** (OK/WARN/FAIL).
  - `dcf_enterprise_value_guarded` — DCF col **g-range hard-reject**, wrappa `compute_dcf` del `k2a_quant` vendorizzato.
  - Helper deterministici tenuti (non parte dei 4): `wacc`, `patrimonial_value`, `reconcile_ev`, `indici_bilancio`.
- **Provenienza per call_id** e **hook Stop anti-omissione**: intatti.
- **Contratto assunzioni** (hook PreToolUse, nuovo): il DCF è **negato** se nel trace non c'è una `valida_assunzioni` precedente; ed è negato se l'ultima valida è **FAIL**. OK/WARN → DCF ammesso (WARN va motivato nel deliverable).

Verifica gate (trace simulato, no Claude): DCF senza valida → DENY · dopo FAIL → DENY · dopo OK/WARN → ALLOW · Bash/Write fuori out → DENY. **7/7.**

## 2. Numeri (snapshot reale: italy rf 2,95% / erp 6,69% anti-doppio-conteggio)

Correttezza deterministica sui 4 casi (`phase_a_correctness.py`, nessun LLM):

| Caso | Settore | ke | WACC | EV multipli | EV DCF | recinto |
|---|---|---|---|---|---|---|
| 01 Studio ingegneria | engineering_construction | **11,5%** | 10,0% | 2,91M (9,1×) | 2,57M | OK |
| 02 Meccanica turnaround | machinery | **18,3%** | 9,6% | 3,14M (11,2×) | 2,15M | OK |
| 03 Software (acquisizione) | software_application | **11,7%** | 11,7% | 5,06M (24,1×) | 1,41M | OK |
| 04 Hotel (investimento) | restaurant_hotel | **15,8%** | 9,1% | 6,91M (12,8×) | 4,88M | OK |

- **ke ragionevole per settore** ✓ — meccanica turnaround a leva 1,65 → 18,3% (βL 2,08); ingegneria low-debt → 11,5%; software net-cash → 11,7%; hotel a leva → 15,8%.
- **Nuovo metodo abbassa il ke di ~1,3–1,75pp** vs lo snapshot vecchio (rf 3,85 / erp 7,1): es. hotel 17,44% → 15,83%.
- **Il recinto funziona**: assunzioni ragionevoli (FCF ≈ EBITDA·(1−t)·0,85, crescita = min(CAGR storico, 8%)) → **OK** su tutti e 4. Assunzioni aggressive sul turnaround (margine 5,4% che proietta FCF 14%) → **FAIL** (`traiettoria_margini=FAIL`, `cagr_fcf_vs_storico=WARN`). g 5% → **rifiutato** (`g_fuori_range`, range ammesso [0,5–2,0]).

**Finding da decidere insieme (correttezza "che regge"):** per i settori a multiplo alto l'EV/EBITDA su una PMI piccola **sovrastima** rispetto al DCF — software 24,1× dà 5,06M contro 1,41M di DCF (3,6×). Anche il turnaround: 11,2× su EBITDA depresso gonfia. È corretto che i tool diano questi numeri; il punto è che **il peso che l'agente assegna ai metodi diventa decisivo** (è esattamente il giudizio che il `reconcile_ev` + la motivazione devono reggere). Il DCF a 3 anni espliciti + Gordon 1,5% invece **sottovaluta** un grower al 35% (software): tensione di modello da tenere a mente.

## 3. Cosa NON ho potuto misurare (serve il live run)

Bloccato: niente `.env.local` in questo worktree → niente `ANTHROPIC_API_KEY`; crediti prima esauriti. Quindi **non** ho ancora:
- qualità dell'output del deliverable (l'agente che ragiona la sequenza),
- **varianza dell'orchestrazione** su N run dello stesso caso,
- **token/latenza per caso** vs la pipeline.

`variance_batch.py` è pronto: 4 casi freschi col quant vero + 01 ripetuto 3× (varianza n=3). Un comando appena ho chiave+crediti:
```
set -a; . ../kai-website/kbot/backend/.env.local; set +a
.venv/bin/python variance_batch.py
```

## 4. Due note di onestà

1. **Il quant pubblicato non è vendorizzato in questo repo.** La copia in `kai-website/kbot/backend/vendor/k2a_quant/` è vecchia (niente 4 tool; snapshot italy 3,85/7,1). Ho usato la **mia patch** (= i 4 tool che hai mergiato) + ho allineato rf/erp ai valori che mi hai dato (2,95/6,69) in una copia PoC dello snapshot (`data/snapshot_real.json`, **non** tocca il vendored live). Se nel pubblicato ci sono raffinazioni per-settore oltre a italy rf/erp, i miei numeri possono differire un filo. **Per il live run "vero"-vero conviene vendorizzare qui il `k2a_quant` pubblicato.**
2. **ATECO→settore** dei 4 casi mappato a mano (71.12.10→engineering_construction, 25.62.00→machinery, 62.01.00→software_application, 55.10.00→restaurant_hotel). La mappa completa la benedici tu (cancello #2).

## 5. I due cancelli per il go-live di Advisor

1. **Numeri corretti e stabili** → *correttezza* dimostrata (deterministica); *stabilità/varianza* pendente del live run.
2. **Mappa ATECO benedetta da te** → pendente.

→ Mi serve: (a) chiave+crediti per il live run, e/o vendoring del `k2a_quant` pubblicato; (b) la tua revisione ATECO. Con quelli chiudo il re-run completo (varianza+token+latenza) e decidiamo se Advisor vende.

Luigi
