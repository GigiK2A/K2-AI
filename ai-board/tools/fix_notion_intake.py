#!/usr/bin/env python3
from __future__ import annotations

import re
from dataclasses import dataclass

from core import notion_board


@dataclass
class FixStats:
    leads_checked: int = 0
    leads_fixed: int = 0
    clients_created: int = 0
    projects_created: int = 0
    leads_patched: int = 0
    tasks_patched: int = 0
    client_links_patched: int = 0
    project_links_patched: int = 0


EMAIL_RE = re.compile(r"Email:\s*([^\s]+)", re.IGNORECASE)


def _plain(props: dict, key: str) -> str:
    prop = props.get(key) or {}
    items = prop.get("rich_text") or prop.get("title") or []
    return "".join(item.get("plain_text", "") for item in items).strip()


def _email_from_notes(notes: str) -> str:
    match = EMAIL_RE.search(notes or "")
    return (match.group(1).strip() if match else "").lower()


def _relation_ids(props: dict, key: str) -> list[str]:
    rel = (props.get(key) or {}).get("relation") or []
    return [item.get("id") for item in rel if item.get("id")]


def _set_rel(page_id: str, prop_name: str, ids: list[str]) -> bool:
    page = notion_board._request("GET", f"/pages/{page_id}")
    props = page.get("properties", {})
    if prop_name not in props:
        return False
    clean_ids = []
    for item in ids:
        if item and item not in clean_ids:
            clean_ids.append(item)
    notion_board._request(
        "PATCH",
        f"/pages/{page_id}",
        json={"properties": {prop_name: {"relation": [{"id": item} for item in clean_ids]}}},
    )
    return True


def _append_rel(page_id: str, prop_name: str, add_id: str) -> bool:
    page = notion_board._request("GET", f"/pages/{page_id}")
    props = page.get("properties", {})
    if prop_name not in props or not add_id:
        return False
    current = _relation_ids(props, prop_name)
    if add_id in current:
        return False
    current.append(add_id)
    notion_board._request(
        "PATCH",
        f"/pages/{page_id}",
        json={"properties": {prop_name: {"relation": [{"id": item} for item in current]}}},
    )
    return True


def run_fix() -> FixStats:
    stats = FixStats()
    lead_pages = [p for p in notion_board._query_database(notion_board.DB_PIPELINE) if not p.get("archived")]
    task_pages = [p for p in notion_board._query_database(notion_board.DB_TASKS) if not p.get("archived")]

    for lead_page in lead_pages:
        stats.leads_checked += 1
        lead_props = lead_page.get("properties", {})
        lead_id = lead_page["id"]
        lead_name = _plain(lead_props, "Nome lead") or "Contatto"
        lead_company = _plain(lead_props, "Azienda")
        lead_sector = notion_board._select_name(lead_props.get("Settore")) or "Altro"
        lead_notes = _plain(lead_props, "Note")
        lead_pain = _plain(lead_props, "Pain point")
        lead_email = _email_from_notes(lead_notes)

        client_rel = _relation_ids(lead_props, "Cliente collegato")
        project_rel = _relation_ids(lead_props, "Commessa creata")
        client_id = client_rel[0] if client_rel else None
        project_id = project_rel[0] if project_rel else None
        changed = False

        if not client_id:
            before_clients = notion_board.count_database_pages(notion_board.DB_CLIENTS)
            client_id = notion_board.create_or_get_client(
                company_name=lead_company or lead_name,
                contact_name=lead_name,
                email=lead_email,
                sector=lead_sector,
                notes=(lead_notes or lead_pain)[:1900],
            )
            after_clients = notion_board.count_database_pages(notion_board.DB_CLIENTS)
            if after_clients > before_clients:
                stats.clients_created += 1
            changed = True

        if not project_id:
            before_projects = notion_board.count_database_pages(notion_board.DB_PROJECTS)
            project_id = notion_board.create_project_for_client(
                client_id=client_id,
                lead_name=lead_name,
                notes=(lead_notes or lead_pain)[:1900],
                offer_type="Consulenza",
            )
            after_projects = notion_board.count_database_pages(notion_board.DB_PROJECTS)
            if after_projects > before_projects:
                stats.projects_created += 1
            changed = True

        if changed:
            if _set_rel(lead_id, "Cliente collegato", [client_id]) or _set_rel(lead_id, "Commessa creata", [project_id]):
                stats.leads_patched += 1

        if _append_rel(client_id, "Lead collegati", lead_id):
            stats.client_links_patched += 1
        if _append_rel(client_id, "Commesse", project_id):
            stats.client_links_patched += 1
        if _append_rel(project_id, "Lead collegati", lead_id):
            stats.project_links_patched += 1

        for task_page in task_pages:
            task_id = task_page["id"]
            task_props = task_page.get("properties", {})
            task_notes = _plain(task_props, "Output")
            task_title = _plain(task_props, "Titolo task")
            task_leads = _relation_ids(task_props, "Lead collegato")
            task_projects = _relation_ids(task_props, "Commessa")

            matched = False
            if lead_id in task_leads:
                matched = True
            elif lead_email and lead_email in task_notes.lower():
                matched = True
            elif lead_name and lead_name.lower() in task_title.lower() and "nuovo lead da sito" in task_title.lower():
                matched = True

            if not matched:
                continue

            new_leads = task_leads if lead_id in task_leads else (task_leads + [lead_id])
            new_projects = task_projects if project_id in task_projects else (task_projects + [project_id])

            patched = False
            if _set_rel(task_id, "Lead collegato", new_leads):
                patched = True
            if _set_rel(task_id, "Commessa", new_projects):
                patched = True
            if patched:
                stats.tasks_patched += 1
            if _append_rel(project_id, "Task", task_id):
                stats.project_links_patched += 1

        if changed:
            stats.leads_fixed += 1

    return stats


def main() -> None:
    if not notion_board.notion_enabled():
        raise SystemExit("Notion non attivo: configura board_data_backend=notion e variabili NOTION_*.")
    stats = run_fix()
    print("fix_complete")
    print(f"leads_checked={stats.leads_checked}")
    print(f"leads_fixed={stats.leads_fixed}")
    print(f"clients_created={stats.clients_created}")
    print(f"projects_created={stats.projects_created}")
    print(f"leads_patched={stats.leads_patched}")
    print(f"tasks_patched={stats.tasks_patched}")
    print(f"client_links_patched={stats.client_links_patched}")
    print(f"project_links_patched={stats.project_links_patched}")
    print(f"clients_total={notion_board.count_database_pages(notion_board.DB_CLIENTS)}")
    print(f"projects_total={notion_board.count_database_pages(notion_board.DB_PROJECTS)}")
    print(f"pipeline_total={notion_board.count_database_pages(notion_board.DB_PIPELINE)}")
    print(f"tasks_total={notion_board.count_database_pages(notion_board.DB_TASKS)}")


if __name__ == "__main__":
    main()
