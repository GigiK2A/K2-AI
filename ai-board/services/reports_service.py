from __future__ import annotations

from typing import TypedDict


class ReportListItem(TypedDict):
    id: str
    created_at_label: str
    client: str
    service: str
    service_id: str
    tier: str
    status: str
    status_label: str
    status_badge_class: str


def get_mock_reports() -> list[ReportListItem]:
    return [
        {
            "id": "KAI-RPT-2026-001",
            "created_at_label": "03/05/2026 09:12",
            "client": "Alfa Componenti S.r.l.",
            "service": "Agenti AI Email & CRM",
            "service_id": "P01",
            "tier": "WEB",
            "status": "ready",
            "status_label": "Pronto",
            "status_badge_class": "bg-emerald-50 text-emerald-700 ring-emerald-100",
        },
        {
            "id": "KAI-RPT-2026-002",
            "created_at_label": "02/05/2026 16:40",
            "client": "Studio Rinaldi",
            "service": "Automazioni Amministrative",
            "service_id": "P02",
            "tier": "HOST",
            "status": "sent",
            "status_label": "Inviato",
            "status_badge_class": "bg-blue-50 text-blue-700 ring-blue-100",
        },
        {
            "id": "KAI-RPT-2026-003",
            "created_at_label": "01/05/2026 11:08",
            "client": "Nord Est Hospitality",
            "service": "AI Hospitality & Revenue",
            "service_id": "P20",
            "tier": "HOST",
            "status": "ready",
            "status_label": "Pronto",
            "status_badge_class": "bg-emerald-50 text-emerald-700 ring-emerald-100",
        },
        {
            "id": "KAI-RPT-2026-004",
            "created_at_label": "30/04/2026 14:25",
            "client": "Meccanica Umbra",
            "service": "Integrazione Gestionali & ERP",
            "service_id": "P10",
            "tier": "STUDIO",
            "status": "draft",
            "status_label": "Bozza",
            "status_badge_class": "bg-amber-50 text-amber-700 ring-amber-100",
        },
        {
            "id": "KAI-RPT-2026-005",
            "created_at_label": "29/04/2026 10:16",
            "client": "Lex & Partners",
            "service": "AI Legale & Contratti",
            "service_id": "P03",
            "tier": "WEB",
            "status": "ready",
            "status_label": "Pronto",
            "status_badge_class": "bg-emerald-50 text-emerald-700 ring-emerald-100",
        },
    ]
