from __future__ import annotations

from typing import Any

import psycopg


def _rows(conn: "psycopg.Connection", sql: str) -> list[dict[str, Any]]:
    with conn.cursor() as cur:
        cur.execute(sql)
        cols = [c.name for c in cur.description]
        return [dict(zip(cols, row)) for row in cur.fetchall()]


def read_servizi(conn: "psycopg.Connection") -> list[dict[str, Any]]:
    return _rows(conn, 'select id, "Servizio", "Categoria", "Descrizione", '
                       '"Risultati_KPI", "Agevolazione", "URL", "Stato", "Data" '
                       'from public.servizi order by id')


def read_topics(conn: "psycopg.Connection") -> list[dict[str, Any]]:
    return _rows(conn, 'select id, "Tema", "Descrizione", "Pillar", "Stato", "Data" '
                       'from public.topics order by id')
