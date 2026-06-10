# Checklist dati per VdS iliad COLOC

Lista da consultare prima di generare il file. Per ogni voce:
- ✅ se trovata in cartella → usa quella
- ❓ se non trovata → CHIEDI all'utente
- 🚫 mai inventare

## A. Anagrafica sito (T0)

| Campo | Dove cercare | Esempio Follonica |
|-------|--------------|-------------------|
| `COD_INWIT` | Scheda Rischi I*.pdf nome file, Valutazione_Preesistenze §3.1 | I171GR |
| `NOME_SITO` | Valutazione_Preesistenze T0 riga "Sito", PRG ARC | PRATO RANIERI (FOLLONICA CENTRO) |
| `DATA_SOPRALLUOGO` | Data EXIF/nome foto in SOPRALLUOGO/FOTO/ | 07/05/2026 |
| `COMUNE_PROV` | Valutazione_Preesistenze, formato "COMUNE (PROV)" | FOLLONICA (GR) |
| `INDIRIZZO` | Valutazione_Preesistenze §"Localizzazione" | VIA AMENDOLA, SNC |

## B. Presenti al sopralluogo (T1)

| Campo | Default proponibile (chiedi conferma) |
|-------|---------------------------------------|
| `NOM_PROF` | "Luca Rossi" (titolare K2A) |
| `SOC_PROF` | "Studio K2A Srls" |
| `TEL_PROF` | "3479407540" |
| `NOM_ALTRO` | "—" o nome tecnico Circet se noto |
| `SOC_ALTRO` | "Circet S.p.A." (se commessa iliad/Circet) |
| `TEL_ALTRO` | "N.D." se non noto |

## C. Impianto INWIT (P4-P8)

| Campo | Fonte | Note |
|-------|-------|------|
| TIPOLOGIA_SITO (fisso template) | sempre "RAW-LAND" per i siti standard | per ROOF TOP serve altro template |
| TIPO_APPARATI (fisso template) | sempre "OUTDOOR" | |
| `STRUTTURA` | Valutazione_Preesistenze §4.1 / VS / PE Calzavara | es. "PALO FLANGIATO S355 H=30 m + PENNONE H=5" |
| `GESTORI` | PRG ARC + PDM + osservazione sopralluogo | es. "VODAFONE, altro operatore, WIND" — sempre con i settori |
| `LEGITTIMITA` | Esito verifica preesistenze (richiama skill verifica-pe-terzi se serve) | tre forme: Conforme / Non verificabile (con motivo) / Non conforme (con motivo) |

## D. Ospitalità ILIAD (P10-P17)

| Campo | Fonte | Esempio |
|-------|-------|---------|
| `COD_NOME_SRB_ILIAD` | nome cartella commessa | "GR58022_002 - Follonica Centro" |
| `APPARATI_ILIAD` | scheda radio iliad + standard COLOC | "FCOB + MiniTD + ICA (se contatore autonomo), 3 RRH A settore altezza {CG} mt" |
| `ANTENNE_ILIAD` | scheda radio iliad | "n. 3 antenne iliad — altezza B.A. {BA} mt circa isoquota {gestore}" |
| `PARABOLE_ILIAD` | scheda radio iliad | "parabole iliad — {CP} mt e diametri da scheda radio iliad" |
| `ALIMENTAZIONE` | sempre la DOPPIA SOLUZIONE | "Due soluzioni di adduzione elettrica valutate in sopralluogo: (A) FORNITURA AUTONOMA con nuovo contatore — posizione su strada; (B) SOTTOLETTURA dal quadro elettrico INWIT — posizione QE indicata IN FIGURA." |
| `FO` | osservazione sopralluogo | "Presente" / "Non Presente" / "Da verificare" |
| `NOTE_NB` | Valutazione_Preesistenze + vincoli locali | tipicamente: sedime + struttura sintetica + coord WGS84 + NCT |

## E. Didascalie sezione foto

| Campo | Esempio |
|-------|---------|
| `GESTORE1_SETTORI` | "WINDTRE – 110°- 220° - 330°" |
| `GESTORE2_SETTORI` | "VODAFONE – 80° - 150° - 300°" |
| `GESTORE3_SETTORI` | "Altro Gestore – {azimut} se presente" |
| `ILIAD_FOTOMONTAGGIO_DESC` | "Posizionamento antenne isoquota altro gestore con carpenterie ad Y settori {azimut iliad}" |
| `ILIAD_APPARATI_DESC` | breve descrizione del posizionamento sul sito (es. "entro recinzione esistente, lato sud") |

## F. Foto

### Foto fondamentali (sezioni 1-3)

| Slot | Pattern nome file in `report/` |
|------|--------------------------------|
| Area Antenne — fotomontaggio | `fotomontaggio*` o generato con nano-banana |
| Area Apparati ILIAD — pianta | `area*iliad*pianta*` |
| Area Apparati ILIAD — sito | `area*sito*iliad*` |
| Adduzione A | `*contatori*autonom*` o `*fornitura*autonoma*` |
| Adduzione B pianta | `*QE*sottolettura*` |
| Adduzione B foto | `sottolettura*` |

### Panoramiche (slot 7-14)

Da `SOPRALLUOGO/FOTO/<nome_sito>/` — 8 foto.
Se < 8 disponibili o l'utente preferisce gestirle a mano → lascia gli slot del template.

## G. Cose da MAI inventare

- Codice INWIT (chiedi se incerto: I171GR vs I176GR)
- Gestori esistenti e loro settori (questi vanno verificati su PRG ARC)
- Esito legittimità (se mancano preesistenze, dichiara "non verificabile" e indica cosa manca)
- Quote scheda radio iliad (se manca SR, chiedi all'utente)
- Posizione QE per sottolettura (servono foto chiare o pianta autorizzata)
