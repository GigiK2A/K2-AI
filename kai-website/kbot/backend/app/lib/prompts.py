"""V2 system prompt builder — Python mirror of buildSystemPromptV2 in api/kbot/_shared.ts."""
from __future__ import annotations

import json
import re
from typing import List, Optional

from ..settings import CHAT_SYSTEM_MAX_CHARS
from .skills import load_skill_bundle

SERVICES_OVERVIEW_COMPACT = """SERVIZI K2-AI DISPONIBILI (usa per raccomandare il più adatto):
P01 · Agenti AI Email & CRM — HOST/WEB · automatizza follow-up, triage email, aggiornamento CRM
P02 · Automazioni Amministrative — HOST · fatture, riconciliazioni, documenti contabili ripetitivi
P03 · AI Legale & Contratti — WEB · analisi contratti, ricerca giurisprudenziale, redazione clausole
P04 · AI Ingegneria & Progettazione — WEB · relazioni tecniche, computi, tavole, documentazione progettuale
P05 · Microapp Documenti Tecnici — HOST · generazione documenti tecnici da template, perizie, capitolati
P06 · AI Customer Service & Ticket — HOST/WEB · triage ticket, risposta automatica, escalation intelligente
P07 · RAG Knowledge Base — WEB/STUDIO · base di conoscenza interrogabile su documenti aziendali
P08 · AI Compliance & Audit — WEB · verifica conformità, audit trail, checklist normative
P09 · AI Controllo di Gestione — WEB · reporting automatico, KPI, budget vs consuntivo
P10 · Integrazione Gestionali & ERP — STUDIO · connettori API, sync dati, automazioni tra gestionali
P11 · AI Marketing & Contenuti — HOST/WEB · copy, SEO, newsletter, campagne
P12 · Diagnosi Strategica PMI — WEB · analisi processi, gap operativi, roadmap AI
P13 · Agevolazioni & Finanza Agevolata — WEB · identificazione bandi, pratiche, documentazione
P14 · AI Edilizia & Appalti Pubblici — WEB · gare, pratiche, documentazione tecnica appalti
P15 · AI HR & Recruiting — HOST/WEB · screening CV, job description, onboarding automatico
P16 · AI Real Estate & Tokenizzazione — STUDIO · dossier immobiliari, due diligence, tokenizzazione
P17 · AI Data Analytics & BI — STUDIO · dashboard, report automatici, anomaly detection
P18 · AI UX & Design System — WEB · audit UX, design system, accessibilità
P19 · AI Efficienza Energetica — WEB · analisi consumi, report energetico, certificazioni
P20 · AI Hospitality & Revenue — HOST/WEB · revenue management, risposta OTA, upselling automatico

TIER:
HOST: <1.500€/mese — automazioni singole, microapp, agenti email
WEB: 1.500–4.000€/mese — sistemi integrati, RAG, customer service AI
STUDIO: >4.000€/mese — progetti custom, ERP, multi-sistema, analytics avanzato"""


def build_system_prompt_v2(skill_names: List[str], session: dict) -> str:
    skill_content = load_skill_bundle(
        skill_names,
        max_total_chars=CHAT_SYSTEM_MAX_CHARS,
        max_per_skill_chars=5500,
        include_references=False,
    )

    collected = session.get("collected_data") or {}
    mode = collected.get("mode") or session.get("mode") or "report"
    service_id = collected.get("service_id")
    service_context = (
        f"\nSERVIZIO SELEZIONATO DALL'UTENTE: {service_id} — orienta la conversazione su questo ambito.\n"
        if service_id else ""
    )

    uploaded_files = collected.get("uploaded_files") or []
    has_files = len(uploaded_files) > 0
    has_extracted_text = any(
        len(str(f.get("extractedText") or f.get("extractedSummary") or "").strip()) > 80
        for f in uploaded_files
    )

    attachments_state = (
        "estratti testuali disponibili — usali, non fare domande già rispondibili dai file"
        if has_extracted_text
        else "file caricati ma senza testo estraibile"
        if has_files
        else "nessun allegato"
    )

    analyzed_urls = collected.get("analyzed_urls") or []
    url_context = ""
    if analyzed_urls:
        url_lines = []
        for u in analyzed_urls[-3:]:  # last 3 only
            summary = str(u.get("summary") or u.get("url") or "").strip()
            if summary:
                url_lines.append(f"- {summary[:600]}")
        if url_lines:
            url_context = "\nURL ANALIZZATI DALL'UTENTE:\n" + "\n".join(url_lines) + "\n"

    next_step_hint = (
        "Apri il servizio Suite consigliato se il caso combacia; altrimenti compila il form contatti precompilato per definire il perimetro custom"
        if mode == "lead"
        else "Scarica il report operativo con priorità, tempi e template pronti"
    )

    base_prompt = f"""Sei K-BOT, il consulente AI di K2-AI per PMI italiane.
Il tuo ruolo: capire il problema operativo dell'utente con domande naturali, raccogliere il contesto necessario, poi produrre un riepilogo strutturato.
{service_context}{url_context}
COMPORTAMENTO:
- Fai UNA sola domanda per volta, specifica e contestuale a ciò che l'utente ha già detto
- Se l'utente ha già risposto a qualcosa, non richiederlo
- Se l'utente fa una domanda, rispondi prima di fare la tua
- Accetta risposte vaghe e prosegui senza forzare dettagli
- Tono: diretto, professionale, da pari a pari — non commerciale
- Niente elenchi di domande multiple in un singolo messaggio
- Niente markdown strutturale in chat (no #, tabelle, blocchi code)
- Risposte brevi in fase raccolta (max 4 righe)
- Usa sempre caratteri italiani corretti (è, à, ì, ò, ù)
- Nessuna risposta è obbligatoria: se l'utente non sa, accetta e prosegui
- STATO ALLEGATI: {attachments_state}

CAMPI DA RACCOGLIERE (naturalmente, non come modulo):
businessType · problem · currentProcess · goal · urgency (alta/media/bassa)
dataAvailable · integrations · budget (solo se lo menziona) · notes

QUANDO GENERARE IL RIEPILOGO:
Dopo 3-5 turni, quando conosci almeno businessType + problem + goal (anche in modo approssimativo), oppure quando l'utente dice di procedere.
Prima del blocco scrivi 1-2 frasi di chiusura naturale. Poi aggiungi il blocco ESATTO:

CONSULENZA_SUMMARY_START
{{"businessType":"...","problem":"...","currentProcess":"...","goal":"...","urgency":"alta|media|bassa","dataAvailable":"...","integrations":"...","budget":"...","notes":"...","summary":"2-3 frasi specifiche e concrete che descrivono il caso","recommendedServiceId":"PXX","recommendedServiceName":"Nome completo servizio","recommendedTier":"HOST|WEB|STUDIO","nextStep":"{next_step_hint}"}}
CONSULENZA_SUMMARY_END

Il blocco sarà estratto automaticamente e non mostrato all'utente.

{SERVICES_OVERVIEW_COMPACT}
"""
    return f"{base_prompt}\n\n{skill_content}"


_SUMMARY_RE = re.compile(r"CONSULENZA_SUMMARY_START\s*\n([\s\S]*?)\nCONSULENZA_SUMMARY_END")


def extract_summary(text: str) -> Optional[dict]:
    match = _SUMMARY_RE.search(text or "")
    if not match:
        return None
    try:
        return json.loads(match.group(1).strip())
    except json.JSONDecodeError:
        return None


def strip_summary_block(text: str) -> str:
    return _SUMMARY_RE.sub("", text or "").strip()


def normalize_assistant_reply(raw: str) -> str:
    text = (raw or "").strip()
    if not text:
        return "Ricevuto. Procedo con il prossimo passaggio."
    # Strip markdown noise (mirror normalizeAssistantReply in chat.ts).
    text = re.sub(r"```[\s\S]*?```", "", text)
    text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*\|.*\|\s*$", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*[-=_]{3,}\s*$", "", text, flags=re.MULTILINE)
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    if not text:
        return "Ricevuto. Procedo con il prossimo passaggio."
    if len(text) > 1200:
        return text[:1197].rstrip() + "..."
    return text


def compact_messages(messages: List[dict], max_messages: int, max_chars_per_message: int) -> List[dict]:
    """Take last N messages and truncate each."""
    out = []
    for m in messages[-max_messages:]:
        content = str(m.get("content") or "")
        if len(content) > max_chars_per_message:
            content = content[: max_chars_per_message - 1].rstrip() + "…"
        role = m.get("role")
        if role not in ("user", "assistant"):
            continue
        out.append({"role": role, "content": content})
    return out
