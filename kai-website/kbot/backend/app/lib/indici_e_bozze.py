"""Due blocchi di prompt che si accendono SOLO quando servono: GLOSSARIO DEGLI INDICI e REGOLA DELLE BOZZE.

Misurato il 19/10/2026 (modello locale):
  * dal bilancio allegato il bot calcolava «PFN/EBITDA = 1,06» perché chiamava PFN il capitale circolante netto
    (attivo circolante − passivo circolante); il valore giusto, con debiti finanziari 480.000 + 1.650.000 e liquidità
    140.000, era 2,8. Non è un'inesattezza di arrotondamento: è un indice sbagliato, detto con sicurezza;
  * alla richiesta «scrivimi una lettera di diffida» non scriveva la lettera, chiedeva la data, e citava gli
    interessi legali (art. 1224 c.c.) per un credito tra imprese, dove valgono quelli di mora commerciali.

Le definizioni sono quelle di base dell'analisi di bilancio: la PRASSI varia (leasing, finanziamenti dei soci,
accantonamenti) e per questo il blocco chiede al bot di dire quali voci ha incluso. Contenuto che si ripete su ogni
utente: da far validare a un commercialista (e, per gli interessi di mora, a un avvocato).

KBOT_GLOSSARIO_INDICI=0 e KBOT_REGOLA_BOZZE=0 li spengono.
"""
from __future__ import annotations

import os
import re

from . import documento

_GATE_INDICI = re.compile(
    r"\b(pfn|posizione finanziaria|ebitda|ebit\b|dso|giorni (medi )?di incasso|indic[ei]( di bilancio)?|"
    r"leva finanziaria|copertura (degli )?oneri|capitale circolante|margine operativo|rapporto debiti|"
    r"debiti (finanziari|verso banche)|bilancio|stato patrimoniale|conto economico|redditivit|"
    r"sostenibilit\w+ del debito|merito creditizio|rating)\b", re.I)

_GATE_BOZZA = re.compile(
    r"\b(scrivi|scrivimi|redigi|redigimi|prepara|preparami|stendi|stendimi|compila|compilami|bozza|abbozza|"
    r"stila|fammi|formula|genera|generami)\b.{0,80}\b(lettera|diffida|mail|e-?mail|pec|raccomandata|"
    r"contratto|atto|comunicazione|messaggio|risposta|reclamo|contestazione|verbale|disdetta|recesso|"
    r"preventivo|sollecito|informativa|testo)\b", re.I | re.S)

GLOSSARIO = """
GLOSSARIO DEGLI INDICI (usa SOLO queste definizioni; quando calcoli, mostra i passaggi con i NUMERI del documento
e dì quali voci hai incluso; se manca un dato dì quale, non inventarlo e non ripiegare su un'altra formula):
- PFN (posizione finanziaria netta) = debiti finanziari − disponibilità liquide. Debiti finanziari: debiti verso banche
  (entro E oltre l'esercizio: cerca anche nella nota integrativa), mutui, obbligazioni, leasing finanziario, finanziamenti
  dei soci. NON è il capitale circolante netto e NON è il patrimonio netto.
- EBITDA (margine operativo lordo) = risultato operativo (differenza A−B del conto economico) + ammortamenti e svalutazioni.
- PFN/EBITDA = PFN ÷ EBITDA: gli anni di margine operativo lordo che servirebbero per ripagare il debito netto; è
  l'indice che la banca guarda per valutare il rischio di credito.
- DSO (giorni medi di incasso) = crediti verso clienti ÷ ricavi delle vendite × 365.
- Leva finanziaria = debiti finanziari ÷ patrimonio netto.
- Copertura degli oneri finanziari = EBITDA ÷ oneri finanziari.
- Margine EBITDA % = EBITDA ÷ ricavi delle vendite.
- Capitale circolante netto = (rimanenze + crediti + liquidità) − debiti a breve: misura altro, non è la PFN.
Se la domanda chiede un indice e i dati sono nel documento o nel messaggio, calcolalo SUBITO, senza fare prima domande.
"""

REGOLA_BOZZE = """
BOZZA DI DOCUMENTO RICHIESTA: scrivi SUBITO la bozza completa, pronta da adattare — non fare domande prima di scriverla.
I dati che l'utente non ha dato restano SEGNAPOSTO tra parentesi quadre ([data], [indirizzo PEC del destinatario], [tuo
nome e ruolo]); non inventare nomi, indirizzi, partite IVA, importi o date. Dopo la bozza, poche righe: cosa verificare o
compilare e, se la posta in gioco è alta, di farla rivedere da un professionista prima dell'invio.
Per un credito TRA IMPRESE (o verso la pubblica amministrazione) gli interessi sono quelli di mora delle transazioni
commerciali (D.Lgs. 231/2002), che decorrono dal giorno dopo la scadenza senza bisogno di costituzione in mora; il solo
tasso legale (art. 1284 c.c.) vale per i crediti verso privati e consumatori. Se il debitore ha una forma societaria nel
nome (S.r.l., S.p.A., S.n.c., S.a.s., ecc.) o una partita IVA, è un'impresa: NON chiedere conferma, applica la regola.
"""


def blocchi(testo_recente: str) -> str:
    """I blocchi da aggiungere al prompt per questo turno ('' se nessuno serve)."""
    t = testo_recente or ""
    out = ""
    if os.getenv("KBOT_GLOSSARIO_INDICI", "1") != "0" and _GATE_INDICI.search(t):
        out += GLOSSARIO
    if os.getenv("KBOT_REGOLA_BOZZE", "1") != "0" and (_GATE_BOZZA.search(t) or documento.richiesta_documento(t)):
        out += REGOLA_BOZZE
        if os.getenv("KBOT_DOCUMENTO_SEPARATO", "1") != "0":
            out += "\n" + documento.REGOLA + "\n"
    return out
