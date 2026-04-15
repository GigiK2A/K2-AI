"""
Funzioni Notion esposte come tool agli agenti del board.

Ogni funzione wrappa un'operazione su notion_board con:
- gestione errori
- business audit trail
- undo stack (per operazioni reversibili)
- risk level check (L3 = conferma esplicita richiesta)

Regole output:
- Nessun ID tecnico nei return (né UUID, né page_id, né abbreviazioni)
- Testo naturale, leggibile dall'agente e interpretabile per risposta utente
- Errori chiari: distingui errore pre-write (dati mancanti) da errore write (Notion down)

Session context:
- Telegram handler deve chiamare set_current_session(chat_id) prima di ogni invocazione agente
- Così i tool sanno a quale sessione associare undo stack e conferme L3
"""
from __future__ import annotations

import threading
from typing import Any

from loguru import logger

from core import notion_board
from core.action_guard import (
    ActionRisk,
    build_confirmation_prompt,
    get_action_risk,
    store_pending_confirmation,
)
from core.business_audit import log_business_action
from core.undo import push_undo


# ─── Session context thread-safe ────────────────────────────────────────────
_tls = threading.local()


def set_current_session(session_id: str | int) -> None:
    """
    Imposta la sessione corrente per questo thread.
    Deve essere chiamato dal Telegram handler prima di ogni GiuseppinaAgent.chat().
    """
    _tls.session_id = str(session_id)


def get_current_session() -> str | None:
    return getattr(_tls, "session_id", None)


def clear_current_session() -> None:
    _tls.session_id = None


# ─── Helpers interni ─────────────────────────────────────────────────────────
def _validate_required(field_name: str, value: str, label: str = "") -> str | None:
    """Ritorna None se valido, stringa di errore se mancante."""
    if not value or not str(value).strip():
        display = label or field_name
        return f"Campo obbligatorio mancante: '{display}'. Richiedilo al fondatore prima di procedere."
    return None


def _check_l3_confirmation(func_name: str, kwargs: dict[str, Any], summary: str) -> str | None:
    """
    Se l'azione è L3 (WRITE_SENSITIVE), salva pending confirmation e ritorna prompt.
    Ritorna None se L1/L2 (procedi normalmente).
    """
    risk = get_action_risk(func_name, kwargs)
    if risk != ActionRisk.WRITE_SENSITIVE:
        return None

    session = get_current_session()
    if not session:
        # Nessuna sessione Telegram → non possiamo fare il gate, procedi comunque
        logger.warning(f"[notion_tools] Azione L3 '{func_name}' eseguita senza sessione Telegram attiva")
        return None

    store_pending_confirmation(session, func_name, kwargs, summary)
    return build_confirmation_prompt(func_name, kwargs)


# ─── Tool: add_lead_to_pipeline ──────────────────────────────────────────────
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
        result = notion_board.create_pipeline_lead(
            name=name.strip(),
            company=company.strip() if company else "",
            sector=sector or "Altro",
            pain_point=pain_point,
            channel="agent",
            next_action=next_action or "Qualifica iniziale",
            notes=notes,
        )
        entity_id = result.get("id", "") if isinstance(result, dict) else ""
        company_str = f" ({company.strip()})" if company and company.strip() else ""
        label = f"{name.strip()}{company_str}"

        # Undo: creazione → archivia se undo
        session = get_current_session()
        if session and entity_id:
            push_undo(
                session_id=session,
                action_type="create",
                entity_type="lead",
                entity_id=entity_id,
                entity_name=label,
                action_description=f"Lead '{label}' aggiunto alla pipeline",
            )

        log_business_action(
            action=f"Lead '{label}' aggiunto alla pipeline Notion",
            entity_type="lead",
            entity_name=label,
            outcome="success",
        )
        logger.info(f"[notion_tools] Lead '{name}' aggiunto alla pipeline.")
        return f"Lead '{name.strip()}'{company_str} aggiunto alla pipeline Notion."
    except Exception as exc:
        log_business_action(
            action=f"Tentativo aggiunta lead '{name}' — fallito",
            entity_type="lead",
            entity_name=name,
            outcome="error",
            details={"error": str(exc)},
        )
        logger.warning(f"[notion_tools] Errore add_lead_to_pipeline: {exc}")
        return f"Errore nell'aggiunta del lead: {exc}"


# ─── Tool: update_pipeline_lead ─────────────────────────────────────────────
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

    # Check L3 (status won/lost richiede conferma)
    kwargs = {"name_or_id": name_or_id, "status": status, "next_action": next_action, "notes": notes}
    confirmation_prompt = _check_l3_confirmation("update_pipeline_lead", kwargs, f"Aggiorna lead '{name_or_id}' → {status}")
    if confirmation_prompt:
        return confirmation_prompt

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
            matched_lead = matches[0]
            target_id = matched_lead["id"]

            # Cattura pre-state per undo
            session = get_current_session()
            if session and (status or next_action):
                pre_state: dict[str, Any] = {}
                if status and matched_lead.get("status"):
                    pre_state["status"] = matched_lead["status"]
                if next_action and matched_lead.get("next_action"):
                    pre_state["next_action"] = matched_lead["next_action"]
                if notes and matched_lead.get("notes"):
                    pre_state["notes"] = matched_lead["notes"]
                if pre_state:
                    push_undo(
                        session_id=session,
                        action_type="update",
                        entity_type="lead",
                        entity_id=target_id,
                        entity_name=matched_lead.get("name", name_or_id),
                        pre_state=pre_state,
                        action_description=f"Lead aggiornato: status={status or '—'}",
                    )

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

        status_str = f" — stato: {status}" if status else ""
        log_business_action(
            action=f"Lead '{name_or_id}' aggiornato{status_str}",
            entity_type="lead",
            entity_name=name_or_id,
            outcome="success",
            details={"status": status, "next_action": next_action},
        )
        logger.info(f"[notion_tools] Lead '{name_or_id}' aggiornato.")
        return f"Lead '{name_or_id}' aggiornato in Notion{status_str}."
    except Exception as exc:
        log_business_action(
            action=f"Tentativo aggiornamento lead '{name_or_id}' — fallito",
            entity_type="lead",
            entity_name=name_or_id,
            outcome="error",
            details={"error": str(exc)},
        )
        logger.warning(f"[notion_tools] Errore update_pipeline_lead: {exc}")
        return f"Errore aggiornamento lead: {exc}"


# ─── Tool: create_board_task ─────────────────────────────────────────────────
def create_board_task(
    title: str,
    description: str = "",
    priority: int = 3,
    assigned_to: str = "",
    notes: str = "",
    due_date: str = "",
    client_name: str = "",
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
        client_name: Nome dell'azienda cliente da collegare al task (opzionale ma consigliato).

    Returns:
        Conferma creazione task, o messaggio di errore con campo mancante.
    """
    err = _validate_required("title", title, "titolo del task")
    if err:
        return err
    if not notion_board.notion_enabled():
        return "Notion non abilitato — task non creato."
    try:
        client_id: str | None = None
        if client_name and client_name.strip():
            client = notion_board.find_client_by_name(client_name.strip())
            if client:
                client_id = client["id"]
            else:
                logger.warning(f"[notion_tools] Cliente '{client_name}' non trovato — task creato senza link cliente.")

        result = notion_board.create_task(
            title=title[:120].strip(),
            description=description,
            assigned_to=assigned_to or "founder",
            priority=priority,
            status="pending",
            requested_by="ai_agent",
            notes=notes,
            task_type="Operativo",
            due_date=due_date or None,
            client_id=client_id,
        )
        entity_id = result if isinstance(result, str) else (result.get("id", "") if isinstance(result, dict) else "")
        client_str = f" (collegato a '{client_name.strip()}')" if client_id else ""

        # Undo: creazione task
        session = get_current_session()
        if session and entity_id:
            push_undo(
                session_id=session,
                action_type="create",
                entity_type="task",
                entity_id=entity_id,
                entity_name=title[:80],
                action_description=f"Task '{title[:80]}' creato",
            )

        log_business_action(
            action=f"Task '{title[:80]}' creato nel board{client_str}",
            entity_type="task",
            entity_name=title[:80],
            outcome="success",
            details={"priority": priority, "client": client_name},
        )
        logger.info(f"[notion_tools] Task '{title}' creato{client_str}.")
        return f"Task '{title.strip()[:80]}' creato nel board Notion{client_str}."
    except Exception as exc:
        log_business_action(
            action=f"Tentativo creazione task '{title[:80]}' — fallito",
            entity_type="task",
            entity_name=title[:80],
            outcome="error",
            details={"error": str(exc)},
        )
        logger.warning(f"[notion_tools] Errore create_board_task: {exc}")
        return f"Errore creazione task: {exc}"


# ─── Tool: update_board_task ─────────────────────────────────────────────────
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

    # Check L3 (done/rejected richiede conferma)
    kwargs = {"task_id": task_id, "status": status, "notes": notes}
    confirmation_prompt = _check_l3_confirmation("update_board_task", kwargs, f"Aggiorna task → {status}")
    if confirmation_prompt:
        return confirmation_prompt

    try:
        # Cattura pre-state per undo se cambio status
        if status:
            session = get_current_session()
            if session:
                try:
                    page = notion_board._request("GET", f"/pages/{task_id.strip()}")
                    current_notion_status = page.get("properties", {}).get("Stato", {}).get("select", {}).get("name", "")
                    current_status = notion_board.TASK_STATUS_FROM_NOTION.get(current_notion_status, current_notion_status)
                    if current_status:
                        push_undo(
                            session_id=session,
                            action_type="update",
                            entity_type="task",
                            entity_id=task_id.strip(),
                            entity_name=task_id[:20],
                            pre_state={"status": current_status},
                            action_description=f"Task portato a stato '{status}'",
                        )
                except Exception:
                    pass  # Pre-state capture non bloccante

        notion_board.update_task_status(task_id.strip(), status or "running", notes)

        status_str = f" — stato: {status}" if status else ""
        log_business_action(
            action=f"Task aggiornato{status_str}",
            entity_type="task",
            entity_name=task_id[:20],
            outcome="success",
            details={"status": status},
        )
        logger.info(f"[notion_tools] Task aggiornato a '{status}'.")
        return f"Task aggiornato in Notion{status_str}."
    except Exception as exc:
        log_business_action(
            action=f"Tentativo aggiornamento task — fallito",
            entity_type="task",
            entity_name=task_id[:20],
            outcome="error",
            details={"error": str(exc)},
        )
        logger.warning(f"[notion_tools] Errore update_board_task: {exc}")
        return f"Errore aggiornamento task: {exc}"


# ─── Tool: save_to_memory ────────────────────────────────────────────────────
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
        log_business_action(
            action=f"Memoria salvata: '{key}' (categoria: {category})",
            entity_type="memory",
            entity_name=key,
            outcome="success",
        )
        logger.info(f"[notion_tools] Memoria '{key}' salvata (categoria: {category}).")
        return f"Memorizzato: '{key}' salvato nella categoria '{category}'."
    except Exception as exc:
        logger.warning(f"[notion_tools] Errore save_to_memory: {exc}")
        return f"Errore salvataggio memoria: {exc}"


# ─── Tool: list_open_tasks ───────────────────────────────────────────────────
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


# ─── Tool: list_pipeline_status ─────────────────────────────────────────────
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


# ─── Tool: list_clients ──────────────────────────────────────────────────────
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


# ─── Tool: search_client ─────────────────────────────────────────────────────
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


# ─── Tool: create_or_update_client ───────────────────────────────────────────
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
        result = notion_board.create_or_get_client(
            company_name=company_name.strip(),
            contact_name=contact_name,
            email=email,
            sector=sector or "Altro",
            phone=phone,
            notes=notes,
        )
        entity_id = result.get("id", "") if isinstance(result, dict) else ""

        # Undo: creazione cliente
        session = get_current_session()
        if session and entity_id:
            push_undo(
                session_id=session,
                action_type="create",
                entity_type="client",
                entity_id=entity_id,
                entity_name=company_name.strip(),
                action_description=f"Cliente '{company_name.strip()}' creato",
            )

        log_business_action(
            action=f"Cliente '{company_name.strip()}' salvato nel database Clienti",
            entity_type="client",
            entity_name=company_name.strip(),
            outcome="success",
            details={"sector": sector, "contact": contact_name},
        )
        logger.info(f"[notion_tools] Cliente '{company_name}' creato/aggiornato.")
        return f"Cliente '{company_name.strip()}' salvato nel database Clienti."
    except Exception as exc:
        log_business_action(
            action=f"Tentativo salvataggio cliente '{company_name}' — fallito",
            entity_type="client",
            entity_name=company_name,
            outcome="error",
            details={"error": str(exc)},
        )
        logger.warning(f"[notion_tools] Errore create_or_update_client: {exc}")
        return f"Errore salvataggio cliente: {exc}"
