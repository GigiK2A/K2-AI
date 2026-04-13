"""
Funzioni Notion esposte come tool agli agenti del board.

Ogni funzione wrappa un'operazione su notion_board con gestione errori,
così gli agenti possono scrivere su Notion in autonomia senza crashare.
"""
from __future__ import annotations

from loguru import logger

from core import notion_board


def add_lead_to_pipeline(
    name: str,
    company: str = "",
    sector: str = "",
    pain_point: str = "",
    next_action: str = "Qualifica iniziale",
    notes: str = "",
) -> str:
    """
    Aggiunge un nuovo lead commerciale alla pipeline Notion.
    Usa questa funzione quando identifichi un prospect o una potenziale opportunità commerciale.

    Args:
        name: Nome del lead o del referente principale.
        company: Nome dell'azienda del lead.
        sector: Settore (es. Manifatturiero, Retail, Tecnologia, Sanità, Turismo).
        pain_point: Problema principale o esigenza rilevata.
        next_action: Descrizione della prossima azione commerciale da eseguire.
        notes: Note aggiuntive, contesto, fonti.

    Returns:
        Conferma con ID Notion del lead creato, o messaggio di errore.
    """
    if not notion_board.notion_enabled():
        return "Notion non abilitato — lead non salvato."
    try:
        lead_id = notion_board.create_pipeline_lead(
            name=name,
            company=company,
            sector=sector or "Altro",
            pain_point=pain_point,
            channel="agent",
            next_action=next_action or "Qualifica iniziale",
            notes=notes,
        )
        logger.info(f"[notion_tools] Lead '{name}' aggiunto alla pipeline. ID: {lead_id}")
        return f"Lead '{name}' ({company}) aggiunto alla pipeline Notion. ID: {lead_id}"
    except Exception as exc:
        logger.warning(f"[notion_tools] Errore add_lead_to_pipeline: {exc}")
        return f"Errore aggiunta lead: {exc}"


def update_pipeline_lead(
    name_or_id: str,
    status: str = "",
    next_action: str = "",
    notes: str = "",
) -> str:
    """
    Aggiorna stato, prossima azione o note di un lead nella pipeline Notion.
    Usa questa funzione dopo una call, una email o un cambiamento di stato del prospect.

    Args:
        name_or_id: ID Notion del lead (preferito) o nome del lead da cercare.
        status: Nuovo stato del lead. Valori ammessi: identified, qualified, contacted,
                call_scheduled, proposal_sent, won, lost.
        next_action: Descrizione della nuova prossima azione commerciale.
        notes: Note aggiuntive da aggiungere al record.

    Returns:
        Conferma dell'aggiornamento o messaggio di errore.
    """
    if not notion_board.notion_enabled():
        return "Notion non abilitato — lead non aggiornato."
    try:
        # Prova prima come ID diretto
        target_id = name_or_id.strip()
        lead = None
        if len(target_id) == 36 or len(target_id) == 32:
            try:
                page = notion_board._request("GET", f"/pages/{target_id}")
                if not page.get("archived"):
                    lead = page
            except Exception:
                pass

        # Se non trovato come ID, cerca per nome
        if lead is None:
            all_leads = notion_board.list_pipeline_leads()
            matches = [
                item for item in all_leads
                if (item.get("name") or "").lower() == target_id.lower()
                or (item.get("company") or "").lower() == target_id.lower()
            ]
            if not matches:
                return f"Lead '{name_or_id}' non trovato nella pipeline."
            target_id = matches[0]["id"]

        props: dict = {}
        if status:
            notion_status = notion_board.PIPELINE_STATUS_TO_NOTION.get(status, status)
            props["Stato"] = notion_board._select(notion_status)
        if next_action:
            props["Prossima azione"] = notion_board._rich_text(next_action)
        if notes:
            existing_notes = notion_board._plain_text(
                notion_board._request("GET", f"/pages/{target_id}").get("properties", {}).get("Note")
            )
            combined = f"{existing_notes}\n\n{notes}".strip() if existing_notes else notes
            props["Note"] = notion_board._rich_text(combined[:1900])

        if props:
            notion_board._request("PATCH", f"/pages/{target_id}", json={"properties": props})

        logger.info(f"[notion_tools] Lead '{name_or_id}' aggiornato.")
        return f"Lead '{name_or_id}' aggiornato in Notion (stato: {status or 'invariato'})."
    except Exception as exc:
        logger.warning(f"[notion_tools] Errore update_pipeline_lead: {exc}")
        return f"Errore aggiornamento lead: {exc}"


def create_board_task(
    title: str,
    description: str = "",
    priority: int = 3,
    assigned_to: str = "",
    notes: str = "",
    due_date: str = "",
) -> str:
    """
    Crea un nuovo task nel board Notion.
    Usa questa funzione per registrare un'azione da fare, un follow-up o un deliverable.

    Args:
        title: Titolo chiaro e azionabile del task (massimo 120 caratteri).
        description: Descrizione dettagliata di cosa fare e perché.
        priority: Priorità numerica: 1=Critica, 2=Alta, 3=Media, 4=Bassa.
        assigned_to: Nome o ruolo a cui assegnare il task (es. "founder", "sales").
        notes: Note aggiuntive o contesto.
        due_date: Data di scadenza in formato YYYY-MM-DD (opzionale).

    Returns:
        Conferma con ID Notion del task creato, o messaggio di errore.
    """
    if not notion_board.notion_enabled():
        return "Notion non abilitato — task non creato."
    try:
        task_id = notion_board.create_task(
            title=title[:120],
            description=description,
            assigned_to=assigned_to or "founder",
            priority=priority,
            status="pending",
            requested_by="ai_agent",
            notes=notes,
            task_type="Operativo",
            due_date=due_date or None,
        )
        logger.info(f"[notion_tools] Task '{title}' creato. ID: {task_id}")
        return f"Task '{title}' creato nel board Notion. ID: {task_id}"
    except Exception as exc:
        logger.warning(f"[notion_tools] Errore create_board_task: {exc}")
        return f"Errore creazione task: {exc}"


def update_board_task(
    task_id: str,
    status: str = "",
    notes: str = "",
) -> str:
    """
    Aggiorna stato o note di un task esistente nel board Notion.

    Args:
        task_id: ID Notion del task da aggiornare.
        status: Nuovo stato. Valori ammessi: pending, running, draft, review,
                approved, done, rejected.
        notes: Note o output da aggiungere al task.

    Returns:
        Conferma dell'aggiornamento o messaggio di errore.
    """
    if not notion_board.notion_enabled():
        return "Notion non abilitato — task non aggiornato."
    try:
        notion_board.update_task_status(task_id, status or "running", notes)
        logger.info(f"[notion_tools] Task '{task_id}' aggiornato a '{status}'.")
        return f"Task {task_id} aggiornato (stato: {status or 'invariato'})."
    except Exception as exc:
        logger.warning(f"[notion_tools] Errore update_board_task: {exc}")
        return f"Errore aggiornamento task: {exc}"


def save_to_memory(
    key: str,
    value: str,
    category: str = "decision",
) -> str:
    """
    Salva una decisione, nota strategica o informazione operativa nella memoria condivisa del board.
    Usa questa funzione per registrare decisioni prese, insight rilevanti o contesto che deve
    persistere per le prossime sessioni di lavoro.

    Args:
        key: Chiave identificativa della memoria (es. "strategia.pricing_2025",
             "cliente.acme_pain_point", "decision.modello_go_to_market").
        value: Contenuto della memoria. Può essere testo libero, lista o struttura.
        category: Categoria. Valori: decision, business, offers, rules, messaging,
                  technical, commercial, client.

    Returns:
        Conferma del salvataggio o messaggio di errore.
    """
    if not notion_board.notion_enabled():
        return "Notion non abilitato — memoria non salvata."
    try:
        from core.memory import set_memory
        set_memory(key, value, category=category, updated_by="ai_agent")
        logger.info(f"[notion_tools] Memoria '{key}' salvata (categoria: {category}).")
        return f"Memoria '{key}' salvata nel board (categoria: {category})."
    except Exception as exc:
        logger.warning(f"[notion_tools] Errore save_to_memory: {exc}")
        return f"Errore salvataggio memoria: {exc}"


def list_open_tasks(limit: int = 10) -> str:
    """
    Legge i task aperti dal board Notion (stato: pending, running, review).
    Usa questa funzione per avere una visione aggiornata di cosa è in corso.

    Args:
        limit: Numero massimo di task da restituire (default 10).

    Returns:
        Lista formattata dei task aperti, o messaggio di errore.
    """
    if not notion_board.notion_enabled():
        return "Notion non abilitato."
    try:
        tasks = notion_board.list_tasks()
        open_tasks = [
            t for t in tasks
            if t.get("status") in ("pending", "running", "review")
        ][:limit]
        if not open_tasks:
            return "Nessun task aperto nel board."
        lines = [f"Task aperti ({len(open_tasks)}):"]
        for t in open_tasks:
            lines.append(
                f"- [{t.get('status')}] {t.get('title', 'senza titolo')}"
                f"{' — scadenza: ' + t['due_date'] if t.get('due_date') else ''}"
            )
        return "\n".join(lines)
    except Exception as exc:
        logger.warning(f"[notion_tools] Errore list_open_tasks: {exc}")
        return f"Errore lettura task: {exc}"


def list_pipeline_status(limit: int = 15) -> str:
    """
    Legge lo stato attuale della pipeline commerciale da Notion.
    Usa questa funzione per avere una visione aggiornata dei lead.

    Args:
        limit: Numero massimo di lead da restituire (default 15).

    Returns:
        Riepilogo della pipeline, o messaggio di errore.
    """
    if not notion_board.notion_enabled():
        return "Notion non abilitato."
    try:
        leads = notion_board.list_pipeline_leads()[:limit]
        if not leads:
            return "Pipeline vuota — nessun lead presente."
        lines = [f"Pipeline commerciale ({len(leads)} lead):"]
        for lead in leads:
            lines.append(
                f"- [{lead.get('status', '?')}] {lead.get('name', '?')}"
                f" · {lead.get('company', '')} · score {lead.get('score', '?')}"
                f"{' → ' + lead.get('next_action', '') if lead.get('next_action') else ''}"
            )
        return "\n".join(lines)
    except Exception as exc:
        logger.warning(f"[notion_tools] Errore list_pipeline_status: {exc}")
        return f"Errore lettura pipeline: {exc}"
