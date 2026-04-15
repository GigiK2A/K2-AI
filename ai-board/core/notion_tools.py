"""
Funzioni Notion esposte come tool agli agenti del board.

Ogni funzione wrappa un'operazione su notion_board con gestione errori,
così gli agenti possono scrivere su Notion in autonomia senza crashare.

Regole output:
- Nessun ID tecnico nei return (né UUID, né page_id, né abbreviazioni)
- Testo naturale, leggibile dall'agente e interpretabile per risposta utente
- Errori chiari: distingui errore pre-write (dati mancanti) da errore write (Notion down)
"""
from __future__ import annotations

from loguru import logger

from core import notion_board


def _validate_required(field_name: str, value: str, label: str = "") -> str | None:
    """Ritorna None se valido, stringa di errore se mancante."""
    if not value or not str(value).strip():
        display = label or field_name
        return f"Campo obbligatorio mancante: '{display}'. Richiedilo al fondatore prima di procedere."
    return None


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
        name: Nome del lead o del referente principale (obbligatorio).
        company: Nome dell'azienda del lead.
        sector: Settore (es. Manifatturiero, Retail, Tecnologia, Sanità, Turismo).
        pain_point: Problema principale o esigenza rilevata.
        next_action: Descrizione della prossima azione commerciale da eseguire.
        notes: Note aggiuntive, contesto, fonti.

    Returns:
        Conferma dell'aggiunta, o messaggio di errore con campo mancante.
    """
    err = _validate_required("name", name, "nome del lead")
    if err:
        return err
    if not notion_board.notion_enabled():
        return "Notion non abilitato — lead non salvato."
    try:
        notion_board.create_pipeline_lead(
            name=name.strip(),
            company=company.strip() if company else "",
            sector=sector or "Altro",
            pain_point=pain_point,
            channel="agent",
            next_action=next_action or "Qualifica iniziale",
            notes=notes,
        )
        company_str = f" ({company.strip()})" if company and company.strip() else ""
        logger.info(f"[notion_tools] Lead '{name}' aggiunto alla pipeline.")
        return f"Lead '{name.strip()}'{company_str} aggiunto alla pipeline Notion."
    except Exception as exc:
        logger.warning(f"[notion_tools] Errore add_lead_to_pipeline: {exc}")
        return f"Errore nell'aggiunta del lead: {exc}"


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
        if len(target_id) in (32, 36):
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
        status_str = f" — stato: {status}" if status else ""
        return f"Lead '{name_or_id}' aggiornato in Notion{status_str}."
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
        title: Titolo chiaro e azionabile del task (obbligatorio, massimo 120 caratteri).
        description: Descrizione dettagliata di cosa fare e perché.
        priority: Priorità numerica: 1=Critica, 2=Alta, 3=Media, 4=Bassa.
        assigned_to: Nome o ruolo a cui assegnare il task (es. "founder", "sales").
        notes: Note aggiuntive o contesto.
        due_date: Data di scadenza in formato YYYY-MM-DD (opzionale).

    Returns:
        Conferma creazione task, o messaggio di errore con campo mancante.
    """
    err = _validate_required("title", title, "titolo del task")
    if err:
        return err
    if not notion_board.notion_enabled():
        return "Notion non abilitato — task non creato."
    try:
        notion_board.create_task(
            title=title[:120].strip(),
            description=description,
            assigned_to=assigned_to or "founder",
            priority=priority,
            status="pending",
            requested_by="ai_agent",
            notes=notes,
            task_type="Operativo",
            due_date=due_date or None,
        )
        logger.info(f"[notion_tools] Task '{title}' creato.")
        return f"Task '{title.strip()[:80]}' creato nel board Notion."
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
    if not task_id or not task_id.strip():
        return "ID task mancante — non posso aggiornare."
    try:
        notion_board.update_task_status(task_id.strip(), status or "running", notes)
        logger.info(f"[notion_tools] Task aggiornato a '{status}'.")
        status_str = f" — stato: {status}" if status else ""
        return f"Task aggiornato in Notion{status_str}."
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
        return f"Memorizzato: '{key}' salvato nella categoria '{category}'."
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
            due_str = f" — scadenza: {t['due_date']}" if t.get("due_date") else ""
            lines.append(f"- [{t.get('status')}] {t.get('title', 'senza titolo')}{due_str}")
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
            next_str = f" → {lead.get('next_action')}" if lead.get("next_action") else ""
            lines.append(
                f"- [{lead.get('status', '?')}] {lead.get('name', '?')}"
                f" · {lead.get('company', '')}{next_str}"
            )
        return "\n".join(lines)
    except Exception as exc:
        logger.warning(f"[notion_tools] Errore list_pipeline_status: {exc}")
        return f"Errore lettura pipeline: {exc}"


def list_clients(limit: int = 20) -> str:
    """
    Legge l'elenco dei clienti dal database Clienti di Notion.
    Usa questa funzione per vedere i clienti esistenti, cercare un cliente per nome o settore.

    Args:
        limit: Numero massimo di clienti da restituire (default 20).

    Returns:
        Elenco clienti con nome, settore, stato relazione e contatto.
    """
    if not notion_board.notion_enabled():
        return "Notion non abilitato."
    try:
        clients = notion_board.list_clients()[:limit]
        if not clients:
            return "Nessun cliente trovato nel database Clienti."
        lines = [f"Clienti ({len(clients)}):"]
        for c in clients:
            name = c.get("company_name") or c.get("name") or "—"
            sector = c.get("sector") or "—"
            status = c.get("relationship_status") or c.get("stato_relazione") or "—"
            contact = c.get("contact_name") or "—"
            email = c.get("email") or ""
            lines.append(
                f"- {name} | settore: {sector} | stato: {status} | referente: {contact}"
                + (f" | {email}" if email else "")
            )
        return "\n".join(lines)
    except Exception as exc:
        logger.warning(f"[notion_tools] Errore list_clients: {exc}")
        return f"Errore lettura clienti: {exc}"


def search_client(name_or_company: str) -> str:
    """
    Cerca un cliente specifico nel database Clienti di Notion per nome o azienda.
    Usa questa funzione quando il fondatore menziona un cliente specifico e vuoi
    verificarne i dati o collegarlo a un task/pipeline.

    Args:
        name_or_company: Nome del cliente o dell'azienda da cercare.

    Returns:
        Dettagli del cliente trovato, o messaggio se non trovato.
    """
    if not notion_board.notion_enabled():
        return "Notion non abilitato."
    try:
        client = notion_board.find_client_by_name(name_or_company)
        if not client:
            return f"Nessun cliente trovato con il nome '{name_or_company}'."
        name = client.get("company_name") or client.get("name") or "—"
        lines = [
            f"Cliente: {name}",
            f"Settore: {client.get('sector') or '—'}",
            f"Referente: {client.get('contact_name') or '—'}",
            f"Email: {client.get('email') or '—'}",
            f"Telefono: {client.get('phone') or '—'}",
            f"Stato relazione: {client.get('relationship_status') or '—'}",
            f"Note: {client.get('notes') or '—'}",
        ]
        return "\n".join(lines)
    except Exception as exc:
        logger.warning(f"[notion_tools] Errore search_client: {exc}")
        return f"Errore ricerca cliente: {exc}"


def create_or_update_client(
    company_name: str,
    contact_name: str = "",
    email: str = "",
    sector: str = "",
    phone: str = "",
    notes: str = "",
) -> str:
    """
    Crea un nuovo cliente in Notion o aggiorna uno esistente se trovato per nome/email.
    Usa questa funzione quando il fondatore dice 'aggiungi cliente', 'crea cliente',
    'inserisci questa azienda nei clienti' o simili.

    Args:
        company_name: Nome dell'azienda (obbligatorio).
        contact_name: Nome del referente principale.
        email: Email aziendale o del referente.
        sector: Settore (es. Manifatturiero, Retail, Hospitality, Tecnologia).
        phone: Numero di telefono.
        notes: Note aggiuntive, contesto, provenienza.

    Returns:
        Conferma creazione/aggiornamento, o messaggio di errore con campo mancante.
    """
    err = _validate_required("company_name", company_name, "nome dell'azienda")
    if err:
        return err
    if not notion_board.notion_enabled():
        return "Notion non abilitato — cliente non salvato."
    try:
        notion_board.create_or_get_client(
            company_name=company_name.strip(),
            contact_name=contact_name,
            email=email,
            sector=sector or "Altro",
            phone=phone,
            notes=notes,
        )
        logger.info(f"[notion_tools] Cliente '{company_name}' creato/aggiornato.")
        return f"Cliente '{company_name.strip()}' salvato nel database Clienti."
    except Exception as exc:
        logger.warning(f"[notion_tools] Errore create_or_update_client: {exc}")
        return f"Errore salvataggio cliente: {exc}"
