"""Rendering di grafici Chart.js-style in immagini PNG per Telegram.

Sul sito i blocchi ```grafico``` diventano <canvas> Chart.js.
Su Telegram non c'è un browser: qui li convertiamo in PNG con matplotlib
(libreria locale, nessun SaaS esterno).

Config accettata (compatibile con quanto già prodotto dagli agenti):

    {"type": "bar", "data": {"labels": ["A", "B"],
     "datasets": [{"label": "Serie", "data": [10, 20]}]}}

Tipi supportati: bar, horizontalBar, line, pie, doughnut.
"""

from __future__ import annotations

from io import BytesIO
from typing import Any

from loguru import logger

# Palette coerente e leggibile su sfondo chiaro. Volutamente neutra.
_PALETTE = [
    "#2563eb", "#16a34a", "#f59e0b", "#dc2626", "#7c3aed",
    "#0891b2", "#db2777", "#65a30d", "#ea580c", "#4b5563",
]

_MAX_LABELS = 40
_MAX_DATASETS = 8


def normalize_chart_config(raw: Any) -> dict[str, Any]:
    """Valida e normalizza una config grafico. Solleva ValueError se non valida."""
    if not isinstance(raw, dict):
        raise ValueError("Configurazione grafico non valida")

    chart_type = str(raw.get("type") or "bar").strip().lower()
    data = raw.get("data") or {}
    if not isinstance(data, dict):
        raise ValueError("Il campo 'data' del grafico non è valido")

    labels = data.get("labels") or []
    datasets = data.get("datasets") or []
    if not isinstance(labels, list) or not isinstance(datasets, list):
        raise ValueError("Il grafico richiede 'labels' e 'datasets'")
    if not labels or not datasets:
        raise ValueError("Il grafico richiede almeno una label e un dataset")

    labels = [str(item) for item in labels[:_MAX_LABELS]]

    clean_datasets: list[dict[str, Any]] = []
    for index, dataset in enumerate(datasets[:_MAX_DATASETS]):
        if not isinstance(dataset, dict):
            continue
        values_raw = dataset.get("data") or []
        if not isinstance(values_raw, list):
            continue
        values: list[float] = []
        for value in values_raw[: len(labels)]:
            try:
                values.append(float(value))
            except (TypeError, ValueError):
                values.append(0.0)
        # Pad in caso di dataset più corto delle labels.
        while len(values) < len(labels):
            values.append(0.0)
        clean_datasets.append({
            "label": str(dataset.get("label") or f"Serie {index + 1}"),
            "data": values,
        })

    if not clean_datasets:
        raise ValueError("Nessun dataset numerico valido nel grafico")

    return {
        "type": chart_type,
        "title": str(raw.get("title") or "").strip(),
        "labels": labels,
        "datasets": clean_datasets,
    }


def render_chart_png(raw_config: Any) -> bytes:
    """Renderizza la config in PNG. Solleva ValueError/RuntimeError su errore."""
    config = normalize_chart_config(raw_config)

    # Import lazy: matplotlib è pesante, caricalo solo quando serve davvero.
    import matplotlib
    matplotlib.use("Agg")  # backend headless, nessun display
    import matplotlib.pyplot as plt

    chart_type = config["type"]
    labels = config["labels"]
    datasets = config["datasets"]

    fig, ax = plt.subplots(figsize=(8, 4.5), dpi=130)
    try:
        if chart_type in ("pie", "doughnut"):
            _render_pie(ax, labels, datasets[0], donut=chart_type == "doughnut")
        elif chart_type in ("line", "area"):
            _render_line(ax, labels, datasets)
        elif chart_type in ("horizontalbar", "hbar"):
            _render_bar(ax, labels, datasets, horizontal=True)
        else:  # bar e fallback
            _render_bar(ax, labels, datasets, horizontal=False)

        if config["title"]:
            ax.set_title(config["title"], fontsize=13, fontweight="bold", pad=12)

        fig.tight_layout()
        buffer = BytesIO()
        fig.savefig(buffer, format="png", bbox_inches="tight")
        buffer.seek(0)
        return buffer.getvalue()
    except Exception as exc:  # pragma: no cover - difensivo
        logger.warning(f"Rendering grafico fallito: {exc}")
        raise RuntimeError(f"Impossibile renderizzare il grafico: {exc}") from exc
    finally:
        plt.close(fig)


def _color(index: int) -> str:
    return _PALETTE[index % len(_PALETTE)]


def _render_bar(ax, labels, datasets, horizontal: bool) -> None:
    import numpy as np

    n_groups = len(labels)
    n_series = len(datasets)
    positions = np.arange(n_groups)
    total_width = 0.8
    bar_width = total_width / max(n_series, 1)

    for series_index, dataset in enumerate(datasets):
        offset = (series_index - (n_series - 1) / 2) * bar_width
        color = _color(series_index)
        if horizontal:
            ax.barh(positions + offset, dataset["data"], height=bar_width,
                    label=dataset["label"], color=color)
        else:
            ax.bar(positions + offset, dataset["data"], width=bar_width,
                   label=dataset["label"], color=color)

    if horizontal:
        ax.set_yticks(positions)
        ax.set_yticklabels(labels)
    else:
        ax.set_xticks(positions)
        ax.set_xticklabels(labels, rotation=30 if n_groups > 5 else 0, ha="right" if n_groups > 5 else "center")

    ax.grid(axis="x" if horizontal else "y", linestyle="--", alpha=0.3)
    if n_series > 1:
        ax.legend(fontsize=9)


def _render_line(ax, labels, datasets) -> None:
    for series_index, dataset in enumerate(datasets):
        ax.plot(labels, dataset["data"], marker="o", linewidth=2,
                label=dataset["label"], color=_color(series_index))
    ax.grid(linestyle="--", alpha=0.3)
    if len(labels) > 5:
        for tick in ax.get_xticklabels():
            tick.set_rotation(30)
            tick.set_ha("right")
    if len(datasets) > 1:
        ax.legend(fontsize=9)


def _render_pie(ax, labels, dataset, donut: bool) -> None:
    values = [max(0.0, value) for value in dataset["data"]]
    colors = [_color(i) for i in range(len(labels))]
    wedge_props = {"width": 0.42} if donut else None
    ax.pie(
        values,
        labels=labels,
        autopct="%1.0f%%",
        colors=colors,
        startangle=90,
        wedgeprops=wedge_props,
        textprops={"fontsize": 9},
    )
    ax.axis("equal")
