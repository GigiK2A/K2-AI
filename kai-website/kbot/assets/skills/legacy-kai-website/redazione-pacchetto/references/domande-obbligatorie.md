# Domande Obbligatorie — Prima di Iniziare la Redazione

Se un dato non è esplicitamente fornito dall'utente nei materiali caricati, **chiedere PRIMA di iniziare**. Non procedere con valori dedotti o placeholder.

L'obiettivo è finire con un pacchetto pronto in una sola iterazione, senza revisioni multiple.

Usa il tool `AskUserQuestion` per porre queste domande in modo strutturato (multiple choice quando possibile).

---

## Blocco 1 — Identificazione sito (bloccante)

1. **Codice sito** (es. `RM00182_009`) — SE non fornito
2. **Nome sito** (es. `STAZIONE TUSCOLANA`) — SE non fornito
3. **Indirizzo completo** (via, n. civico, Comune, Municipio) — SE non fornito
4. **Tipo sito**: Roof Top / Raw Land / Palo su edificio — SE non chiaro dai materiali
5. **Proprietà infrastruttura**: SITE S.p.A. / Cellnex Italia / INWIT / Rai Way / Altro — SE non chiaro

## Blocco 2 — Tipo intervento (bloccante)

6. **Tipologia intervento**: Nuovo impianto / Modifica radioelettrica / Modifica infrastrutturale
7. **Sistema radiomobile**: quali tecnologie (es. UMTS900/LTE1800/LTE2100/LTE2300/5G700/5G3700/mmWave)
8. **Preesistenza**: il sito è già autorizzato? Se sì → richiedere:
   - Data invio SCIA preesistente
   - Protocollo SCIA DPU Roma + data assunzione
   - Protocollo parere ARPA Lazio + data
   - Protocollo parere VAP + data (se applicabile)

## Blocco 3 — Figure professionali (bloccante)

9. **Progettista** (firma RT, Asseverazioni, Dich. ALPHA24):
   - Ing. Jessica Romanelli
   - Ing. Luca Rossi
   - Altro
10. **Direttore dei Lavori** (se diverso dal progettista):
    - Ing. Jessica Romanelli
    - Ing. Luca Rossi
    - Altro
11. **Delegato alla presentazione** (firma la Delega): tipicamente Jessica dello studio

## Blocco 3B — Permit Coordinator (bloccante — L14)

12. **Permit Coordinator** (da preesistenza): nome, telefono, email
    - Se preesistenza disponibile → estrarre direttamente
    - Se non disponibile → chiedere esplicitamente all'utente
    - Il Permit compare in doc 1 (SCIA), doc 9 (DICH. SOSTITUTIVA α24), doc 10 (Atto d'obbligo)

## Blocco 3C — Codice reversale (bloccante — L15)

13. **Codice reversale pagamento diritti** per la SCIA. Se l'utente non lo ha ancora → segnare `[DA COMPILARE]`

## Blocco 4 — Dati urbanistici (NON copiare ciecamente dal template)

14. **Destinazione PRG (Sistemi e regole)**: verificare via WebGIS Roma, non assumere
15. **Destinazione PRG (Rete ecologica)**: chiave per determinare applicabilità VAP
16. **Destinazione PRG (Carta per la qualità)**
17. **Codice tavola PRG** (es. Tav. 3_12, Tav. 3_22 — L18): verificare che corrisponda alla cartografia PDF allegata
18. **Didascalia PRG corretta** (L19): testo esatto della zona (NON lasciare il sample del template)
19. **Destinazione PTPR (Sistemi ed ambiti)**, Beni Paesaggistici (Tav. B), Beni culturali (Tav. C)
20. **Zona sismica** (L20): dal PE (relazione strutturale) o verifica Regione Lazio — Roma = Zona 2B

## Blocco 5 — Vincoli (SOLO da preesistenza — se non c'è, chiedere)

17. **Vincolo paesaggistico D.Lgs. 42/2004**: presente?
18. **Vincolo monumentale art. 21 D.Lgs. 42/2004**: presente?
19. **Vincolo archeologico art. 142 lett. m**: presente?
20. **Vincolo ex art. 16 NTA del PRG**: presente?
21. **Aeronautica Militare**: presente?
22. **Altri vincoli** (SIC, ZPS, idrogeologico): presenti?

## Blocco 6 — VAP (critico per Roma, vedi Delibera 78/2024)

23. **Il sito rientra in una delle zone art. 5 co. 5 Delibera 78/2024?**
    (Rete Ecologica, Aree a Verde privato Città consolidata, Ambiti strategici, Agro Romano, Servizi)
    - Sì → richiedere protocollo VAP preesistente o segnalare necessità VAP
    - No → cancellare ogni riferimento VAP nei documenti

## Blocco 7 — ENAC / Aeroporti

24. **Aeroporto di riferimento** (da PDM tavole 7.x): Ciampino / Fiumicino / Urbe
25. **Il sito rientra in una superficie di limitazione ENAC?** (`Area interessata` vs `Area non interessata`)

## Blocco 8 — Alpha24

26. **Reference site alpha24 5G**: leggere SEMPRE dalla Scheda Radio alla voce `"Reference Site alpha24 5G:"`. Non assumere self-reference.

## Blocco 9 — Foto sito (L16)

27. **Foto del sito**: l'utente ha fornito la foto reale? Dov'è il file? (Il template ha una foto sample da sostituire)
28. **Dimensioni originali foto template**: verificare in Fase 0-TER per evitare deformazione — se la nuova foto ha aspect ratio diverso, ridimensionare PRIMA di iniettarla

## Blocco 10 — Ospitalità / Nulla Osta

29. **Se sito in ospitalità Cellnex/INWIT/PTI**: Nulla Osta del proprietario è allegato? Qual è il protocollo?

## Blocco 11 — Proprietà e Descrizione Area (L17, L21)

30. **Proprietario infrastruttura** (L17): es. Cellnex Italia S.p.A., SITE S.p.A., INWIT, privato — da preesistenza, NON dal template
31. **Descrizione area di intervento** (L21): quartiere, contesto edilizio, tipo infrastruttura. Se non fornito → derivare da Street View/PE/preesistenza e chiedere conferma

## Blocco 12 — Parabole / Ponti Radio (L22)

32. **Il sito ha parabole/ponti radio?**
    - Sì → fornire dati: diametro, frequenza, azimuth, tilt, altezza centro fase (dalla Scheda Radio)
    - No → annotare "Nessuna parabola prevista" per gestire correttamente la tabella in RT

---

## Flusso Decisionale

```
Utente carica materiali (Scheda Radio, PE, Preesistenza, Template)
        ↓
[1] Leggi i materiali ed estrai tutto l'estraibile (RT preesistente come primaria)
        ↓
[2] Compila la checklist di `checklist-compilazione-rt.md`
        ↓
[3] Per ogni campo mancante → chiedi con AskUserQuestion (blocco per blocco)
        ↓
[4] PRESENTA la checklist compilata all'utente PER CONFERMA
        ↓
[5] Solo dopo conferma esplicita → parti con la generazione dei documenti
```

**Regola**: se un campo è ambiguo o se ci sono discordanze tra fonti, NON procedere. Chiedere all'utente quale valore adottare.

**Caso tipico di errore**: "ho assunto X dalla preesistenza del sito precedente" → NO. Ogni sito ha i suoi dati, mai riciclare tra sessioni.
