"""Modulo privacy/GDPR/AI su dati visivi (review "app outfit AI").

Test reale: app che genera outfit dalle foto dell'utente. Il bot ha applicato la checklist
GDPR meccanica — foto = biometria = art. 9 = consenso; DPIA «obbligatoria»; «il responsabile
notifica entro 72 ore» (errato: quelle sono del titolare verso il Garante); server UE = ok;
certificazioni ISO quasi obbligatorie; «sei conforme se fai questi punti». Tutto categorico,
niente ricostruzione del trattamento reale.

`privacy_hint(text)` rileva i casi privacy che coinvolgono immagini/AI e inietta il frame di
ragionamento corretto: prima capire il sistema tecnico, poi classificare, con conclusioni
condizionate. Deterministico, fail-open (ritorna "" se il caso non è riconosciuto).
"""
from __future__ import annotations

import re

# tema privacy/protezione dati…
_PRIVACY_RE = re.compile(
    r"\b(?:gdpr|gpdr|gdrp|privacy|dati\s+personali|protezione\s+dei\s+dati|biometr\w+|dpia|"
    r"consenso\s+(?:esplicito|informato)|informativa|garante|data\s+breach|"
    r"trasferiment\w+\s+(?:internazionali|extra\s*.?ue)|server\s+(?:extra|fuori)\s*.?ue)\b", re.I)
# …applicato a dati visivi / d'immagine
_VISUAL_RE = re.compile(
    r"\b(?:foto\w*|fotografi\w+|immagin\w+|volto|viso|facciale|corporatura|"
    r"forma\s+fisica|selfie|avatar|video|riconoscimento|embedding|landmark)\b", re.I)


def is_privacy_ai_case(text: str) -> bool:
    """True se la conversazione tocca privacy/GDPR SU dati visivi (foto, volto, immagini
    generate) — il terreno dove la checklist meccanica produce errori giuridici."""
    t = text or ""
    return bool(_PRIVACY_RE.search(t)) and bool(_VISUAL_RE.search(t))


def privacy_hint(text: str) -> str:
    """Blocco da iniettare nel system prompt per i casi privacy/AI/immagini. Ritorna ""
    quando il caso non è riconosciuto."""
    if not is_privacy_ai_case(text):
        return ""
    return (
        "\nCASO PRIVACY/AI SU IMMAGINI — frame di ragionamento OBBLIGATORIO (niente checklist "
        "GDPR meccanica). Sequenza: capire il sistema tecnico → ricostruire i flussi dei dati → "
        "classificare il trattamento → norme applicabili → rischi → provider/contratti → "
        "conclusioni CONDIZIONATE → azioni. Regole:\n"
        "1) FOTO ≠ BIOMETRIA AUTOMATICA. Una fotografia è un dato personale; diventa dato "
        "biometrico ex art. 9 GDPR SOLO se c'è un trattamento tecnico specifico finalizzato o "
        "idoneo all'IDENTIFICAZIONE UNIVOCA o all'autenticazione della persona. Distingui: foto "
        "semplice / analisi estetica o della corporatura / landmark facciali / embedding tecnico "
        "/ riconoscimento facciale / autenticazione / immagine generata. PRIMA di classificare, "
        "chiedi le domande decisive: viene creato un embedding o template riutilizzabile? il "
        "volto serve a identificare/autenticare o solo a generare l'immagine? si confronta con "
        "altri soggetti? le immagini si usano per training? il servizio è accessibile ai minori? "
        "Vietata l'equazione «foto = biometria = art. 9 = consenso esplicito».\n"
        "2) BASI GIURIDICHE PER FINALITÀ, non una per tutta l'app: generazione outfit richiesta "
        "dall'utente → possibile esecuzione del contratto; conservazione nel profilo → contratto "
        "o consenso; training del modello → finalità SEPARATA da valutare a parte; marketing → "
        "base distinta. Tieni SEPARATE la base ex art. 6 e l'eventuale condizione aggiuntiva ex "
        "art. 9: non confonderle. Valuta se il trattamento è davvero necessario o se esistono "
        "alternative meno invasive.\n"
        "3) DPIA: MAI «obbligatoria per legge» in automatico. Valuta il rischio complessivo "
        "(scala, minori, categorie particolari, profilazione, nuove tecnologie, inferenze "
        "sensibili, trasferimenti, realismo delle immagini generate, re-identificazione) e "
        "concludi su una scala: obbligatoria / altamente consigliata / prudenziale / elementi "
        "insufficienti per decidere — con la motivazione.\n"
        "4) DATA BREACH per ruolo (errore classico da non commettere): il RESPONSABILE notifica "
        "al TITOLARE senza ingiustificato ritardo; è il TITOLARE che valuta la notifica al "
        "Garante entro 72 ore quando ne ricorrono i presupposti (e agli interessati se rischio "
        "elevato). Attribuisci OGNI obbligo al ruolo giusto (titolare/responsabile/"
        "sub-responsabile; verso autorità vs verso interessati).\n"
        "5) TRASFERIMENTI: «server in UE» NON equivale ad assenza di trasferimenti — contano "
        "anche accessi/supporto da paesi terzi, sub-responsabili, backup, telemetria, training. "
        "Meccanismi da distinguere: decisione di adeguatezza / Data Privacy Framework se "
        "applicabile / clausole contrattuali standard + Transfer Impact Assessment / BCR / "
        "deroghe art. 49. MAI «gli USA sono/non sono conformi» in generale: verifica il provider "
        "concreto.\n"
        "6) PROVIDER = PRODOTTO SPECIFICO, non azienda generica: API vs versione consumer vs "
        "Business/Enterprise vs intermediario cambiano termini, retention, uso per training e "
        "DPA. Sequenza: identifica prodotto → consulta la documentazione ufficiale già "
        "pubblicata (DPA standard, elenco sub-responsabili, data residency) → contatta il "
        "provider SOLO per ciò che manca. Non dire «devi contattarli» come primo passo.\n"
        "7) CERTIFICAZIONI (ISO 27001/27018, SOC 2) = evidenze utili di due diligence, NON "
        "obblighi di legge e NON prova di conformità GDPR: non presentarle come requisiti.\n"
        "8) CONCLUSIONE SEMPRE CONDIZIONATA: mai «così sei in regola col GDPR». Usa «sulla base "
        "dei dati disponibili…», «restano da verificare: …», e ricorda i temi che restano fuori "
        "(minori, foto di terzi, diritto all'immagine, uso per training, cancellazione dai "
        "backup, AI Act, sicurezza applicativa). Azioni divise per priorità: bloccanti prima del "
        "lancio / importanti / migliorative.\n"
        "9) SE IL CLIENTE CHIEDE «è in regola?» → MODALITÀ AUDIT GUIDATO su questo caso. "
        "Sequenza tipica delle domande decisive, UNA per turno, con valutazione incrementale e "
        "tabella-semaforo aggiornata: quale provider/prodotto riceve le foto e come ci arrivano "
        "(dal browser o via tuo server) → cosa succede alle foto dopo la generazione "
        "(retention) → si conservano SOLO foto originali+generate o anche embedding/template "
        "riutilizzabili (LA domanda più importante: decide l'art. 9) → età e minori → consensi "
        "e informative al caricamento (separando dichiarazione di titolarità delle foto, presa "
        "visione della privacy policy e consensi facoltativi, mai preselezionati) → quali dati "
        "accompagnano la foto verso il provider (minimizzazione: fascia d'età meglio dell'età "
        "esatta, corporatura qualitativa meglio di peso/altezza) → dove sono storage/DB e quali "
        "sub-responsabili accedono → l'AI estrae/salva caratteristiche sensibili o solo "
        "elementi estetici (attenzione: anche se non le estrai, la FOTO in sé può contenerle — "
        "velo, carrozzina, tatuaggi religiosi: dato sensibile «a riposo» è l'immagine) → "
        "diritti artt. 15/17 esercitabili davvero (export completo, cancellazione reale anche "
        "dallo storage). Chiusura con punteggi separati (es. conformità tecnica vs "
        "documentale) e piano dei prossimi passi.\n")
