"""Layer 4 — Composer: genera Allegato H (DOCX) + relazione tecnica (markdown).

Numeri tutti deterministici da Layer 3 (ExecutionResult), formattati con typography
italiana. La narrativa testuale viene dal Narrator (LLM, con fallback). Ogni grandezza
è tracciata agli step_id del Layer 3 (appendice + JSON di tracciabilità).
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from importlib import resources
from pathlib import Path

from jinja2 import Environment

from . import typography as ty
from .exceptions import IncompleteSchemaError, TemplateNotFoundError
from .narrator import Narrator

_NORME_CABINA = [
    "CEI 0-16:2025-04 (connessione MT)", "CEI 64-8:2024 (impianti BT)",
    "CEI 11-25 / IEC 60909 (correnti di cortocircuito)",
    "CEI 64-12 (impianti di terra)", "CEI EN 62305-2 (rischio fulmine)",
    "IEC 61439-1:2020 (quadri BT)", "CEI-UNEL 35024/1 (portate cavi)",
    "DM 37/2008 (dichiarazione di conformità)",
]

# Differenze per tipologia: norme aggiuntive ed etichetta.
_TIPOLOGIE = {
    "cabina_industriale": {
        "label": "Cabina MT/BT industriale", "norme_extra": []},
    "cabina_terziario": {
        "label": "Cabina MT/BT terziario (uffici/retail/hotel)",
        "norme_extra": ["CEI EN 50171 (illuminazione di emergenza / sistemi di sicurezza)"]},
    "bt_residenziale": {
        "label": "Impianto elettrico residenziale BT",
        "norme_extra": ["CEI 64-8 parte 7 (ambienti residenziali)"]},
    "bt_commerciale": {
        "label": "Impianto elettrico commerciale BT",
        "norme_extra": []},
    "fv_bt": {
        "label": "Impianto fotovoltaico connesso in BT (CEI 0-21)",
        "norme_extra": ["CEI 0-21:2025-04 (utente attivo)", "Regola tecnica anti-islanding (SPI)"]},
    "fv_mt": {
        "label": "Impianto fotovoltaico connesso in MT (CEI 0-16)",
        "norme_extra": ["CEI 0-16:2025-04 (utente attivo MT)",
                        "Regola tecnica anti-islanding (SPG)", "CEI EN 62305-2 (rischio fulmine)"]},
    "multisorgente_ats": {
        "label": "Impianto multisorgente con ATS (continuità di servizio)",
        "norme_extra": ["CEI EN 50438 (GE)", "CEI EN 60947-6-1 (ATS)"]},
    "cantiere_temporaneo": {
        "label": "Impianto elettrico di cantiere temporaneo (CEI 64-8 sez.706)",
        "norme_extra": ["CEI 64-8 sez.706 (cantieri)", "CEI 64-17",
                        "CEI 11-27 (PES/PAV)", "D.Lgs. 81/2008"]},
    "impianto_agricolo": {
        "label": "Impianto elettrico agricolo/zootecnico (CEI 64-8 sez.705)",
        "norme_extra": ["CEI 64-8 sez.705 (ambienti agricoli)",
                        "CEI 0-21:2025-04 (FV autoconsumo)"]},
    "edificio_critico_sanitario": {
        "label": "Impianto elettrico sanitario / locali ad uso medico (CEI 64-8 sez.710)",
        "norme_extra": ["CEI 64-8 sez.710 (locali ad uso medico)",
                        "CEI EN 60601 (apparecchi medicali)", "DM 18/09/2002 (incendio ospedali)"]},
    "cabina_mt_industriale_grande": {
        "label": "Cabina MT/BT industriale grande potenza (multi-trafo)",
        "norme_extra": ["CEI 99-2 (cabine MT/BT)", "CEI 11-1 (impianti MT)",
                        "CEI EN 60076-8 (parallelo trafi)"]},
    "datacenter": {
        "label": "Server room / datacenter (categoria DIMOSTRATIVA — EN 50600 non vincolante)",
        "norme_extra": ["CEI 99-2 (locali tecnici)", "IEC 60364 (best practices)",
                        "NOTA: EN 50600 non in KB — non valida per certificazione Tier III/IV"]},
}


@dataclass
class ComposerResult:
    docx_path: str
    markdown_path: str
    tracciabilita_path: str
    gemini_status: str
    mode: str
    warnings: list[str] = field(default_factory=list)
    cad_paths: dict = field(default_factory=dict)  # {svg, dxf, xlsx} se genera_cad


_MARK = "__REVIEW__"  # sostituito a runtime con un run rosso "(REVIEW)"


def _slug(s: str) -> str:
    s = (s or "progetto").lower()
    s = re.sub(r"[^a-z0-9]+", "_", s).strip("_")
    return s or "progetto"


def _v(schema: dict, path: str, default=None):
    node = schema
    for p in path.split("."):
        if not isinstance(node, dict) or p not in node:
            return default
        node = node[p]
    if isinstance(node, dict) and "valore" in node:
        return node["valore"] if node["valore"] is not None else default
    return node if node is not None else default


def _node_review(schema: dict, path: str) -> bool:
    node = schema
    for p in path.split("."):
        if not isinstance(node, dict) or p not in node:
            return False
        node = node[p]
    return bool(isinstance(node, dict) and node.get("review_richiesta"))


def _review_richieste(schema: dict) -> list[dict]:
    out: list[dict] = []

    def walk(obj, path=""):
        if isinstance(obj, dict):
            if "stato" in obj and "valore" in obj:
                if obj.get("review_richiesta") and obj.get("stato") in ("DEFAULT", "RICHIESTO"):
                    out.append({"campo": path, "norma_ref": obj.get("norma_ref")})
                return
            for k, val in obj.items():
                walk(val, f"{path}.{k}" if path else k)
        elif isinstance(obj, list):
            for i, it in enumerate(obj):
                walk(it, f"{path}[{i}]")

    walk(schema)
    return out


class AsseverazioneComposer:
    def __init__(self, execution_result, schema_arricchito: dict,
                 profilo_professionista: dict | None = None, mode: str = "draft",
                 api_key: str | None = None, narrator: Narrator | None = None,
                 output_dir: str = "output", tipologia: str = "cabina_industriale",
                 con_grafici: bool = True, genera_cad: bool = False):
        self.ex = execution_result
        self.con_grafici = con_grafici
        self.genera_cad = genera_cad
        self.schema = schema_arricchito
        self.profilo = profilo_professionista or _profilo_placeholder()
        self.mode = mode
        self.output_dir = Path(output_dir)
        self.narrator = narrator if narrator is not None else Narrator(api_key=api_key)
        if tipologia not in _TIPOLOGIE:
            raise TemplateNotFoundError(f"Tipologia non supportata dal composer: {tipologia}")
        self.tipologia = tipologia
        self._meta = _TIPOLOGIE[tipologia]

    # --- API ---
    def componi(self) -> ComposerResult:
        review = _review_richieste(self.schema)
        if self.mode == "final" and review:
            raise IncompleteSchemaError(
                f"Modalità 'final': {len(review)} voci DEFAULT non confermate. "
                "Confermarle o usare mode='draft'.")

        ctx = self._build_context(review)
        warnings = list(ctx["narrativa_note"])

        committente = ctx["committente"]["ragione_sociale"]
        slug = _slug(f"{committente}_{ctx['ubicazione']['comune']}")
        outdir = self.output_dir / slug
        outdir.mkdir(parents=True, exist_ok=True)

        docx_path = outdir / "allegato_h.docx"
        md_path = outdir / "relazione_tecnica.md"
        trac_path = outdir / "tracciabilita.json"

        self._render_docx(ctx, docx_path)
        self._render_markdown(ctx, md_path)
        trac_path.write_text(json.dumps(ctx["tracciabilita"], indent=2, ensure_ascii=False),
                             encoding="utf-8")

        cad_paths: dict = {}
        if self.genera_cad:
            cad_paths = self._genera_cad(outdir.parent, slug, warnings)

        return ComposerResult(docx_path=str(docx_path), markdown_path=str(md_path),
                              tracciabilita_path=str(trac_path),
                              gemini_status=ctx["gemini_status"], mode=self.mode,
                              warnings=warnings, cad_paths=cad_paths)

    def _genera_cad(self, output_dir: Path, slug: str, warnings: list[str]) -> dict:
        """Genera artefatti CAD (SVG/DXF/XLSX) dai risultati Layer 3. Graceful per dep."""
        from dataclasses import asdict
        from k2a_elettrico.generatori_cad.unifilare_svg import (
            GeneraUnifilareInput, genera_unifilare_svg)
        from k2a_elettrico.generatori_cad.layout_dxf import (
            GeneraLayoutDxfInput, genera_layout_dxf)
        from k2a_elettrico.generatori_cad.computo_xlsx import (
            GeneraComputoMetricoInput, genera_computo_metrico_xlsx)

        dim = asdict(self.ex.dimensioni)
        base = dict(dimensioni=dim, schema_arricchito=self.schema,
                    output_dir=str(output_dir), slug=slug)
        paths: dict = {}
        try:
            svg = genera_unifilare_svg(GeneraUnifilareInput(**base))
            paths["svg"] = svg.file_path; warnings.extend(svg.warnings)
            dxf = genera_layout_dxf(GeneraLayoutDxfInput(**base))
            paths["dxf"] = dxf.file_path; warnings.extend(dxf.warnings)
            xlsx = genera_computo_metrico_xlsx(GeneraComputoMetricoInput(**base))
            paths["xlsx"] = xlsx.file_path
        except Exception as e:  # pragma: no cover — CAD è accessorio, non blocca il DOCX
            warnings.append(f"Generazione CAD parziale/fallita: {e}")
        return paths

    # --- context ---
    def _build_context(self, review: list[dict]) -> dict:
        s = self.schema
        committente = _v(s, "A_anagrafica_contesto.committente", "n.d.")
        comune = _v(s, "A_anagrafica_contesto.comune", "n.d.")
        prov = _v(s, "A_anagrafica_contesto.provincia", "")
        coord = _v(s, "A_anagrafica_contesto.coordinate", {})
        coord_str = (f"lat {coord.get('lat')}, lon {coord.get('lon')}"
                     if isinstance(coord, dict) else "n.d.")
        tens_mt = _v(s, "B_allacciamento_sistema.tensione_MT_kV")
        P = _v(s, "C_sorgenti_carichi.carico.P_kW")
        sistema = _v(s, "B_allacciamento_sistema.sistema_distribuzione_BT", "n.d.")

        trafi_raw = _v(s, "C_sorgenti_carichi.trasformatori", []) or []
        trasformatori = []
        for t in trafi_raw:
            tv = t.get("valore", {}) if isinstance(t, dict) else {}
            mark = _MARK if (isinstance(t, dict) and t.get("review_richiesta")) else ""
            trasformatori.append({
                "Sn": ty.format_potenza_apparente(tv.get("Sn_kVA")),
                "vcc": ty.format_percentuale(tv.get("vcc_pct")),
                "tensioni": f"{ty.format_tensione((tv.get('V1_kV') or 0)*1000)} / "
                            f"{ty.format_tensione(tv.get('V2_V'))}",
                "gruppo": f"{tv.get('gruppo', 'n.d.')}{mark}"})

        dim = self.ex.dimensioni
        # Tabella Icc (3 colonne) da tutti i calcoli, mappando le grandezze note.
        _icc_keymap = [
            ("Icc_MT_kA", "Corrente di cortocircuito MT trifase", "kA", 2),
            ("Icc_BT_kA", "Corrente di cortocircuito BT trifase", "kA", 2),
            ("In_secondario_A", "Corrente nominale secondario trafo", "A", 0),
            ("In_primario_A", "Corrente nominale primario trafo", "A", 0),
            ("Ik3max_kA", "Icc trifase BT massima (multisorgente)", "kA", 2),
            ("Ik3min_kA", "Icc trifase BT minima (multisorgente)", "kA", 2),
        ]
        icc_mt_review = _node_review(s, "B_allacciamento_sistema.Icc_MT_kA")
        icc_table, _seen = [], set()
        for c in dim.icc_calculations:
            for key, label, unit, dec in _icc_keymap:
                if key in c and key not in _seen and c[key] is not None:
                    val = ty._fmt(float(c[key]), dec)
                    if key == "Icc_MT_kA" and icc_mt_review:
                        val += _MARK
                    icc_table.append({"grandezza": label, "valore": val, "unita": unit})
                    _seen.add(key)
        icc = ["; ".join(f"{r['grandezza']} = {r['valore']} {r['unita']}"
                         for r in icc_table)] if icc_table else ["calcolo Icc eseguito"]

        linee = []
        for l in dim.dimensionamento_linee:
            dc = l.dimensionamento_cavo or {}
            cv = l.caduta_tensione or {}
            vp = l.verifica_protezione or {}
            linee.append({
                "linea_id": l.linea_id,
                "sezione": ty.format_sezione(dc.get("sezione_minima_mm2")),
                "Iz": ty.format_corrente(dc.get("Iz_corretta")),
                "caduta": ty.format_percentuale(cv.get("delta_V_percento")),
                "In": ty.format_corrente(l.protezione_In),
                "esito_protezione": ("OK" if vp.get("verifica_sovraccarico_433_1")
                                     else "DA VERIFICARE"),
                "coerente": l.coerente})

        norme = _NORME_CABINA + self._meta["norme_extra"]
        contesto_narr = {"denominazione": f"{self._meta['label']} — {committente}",
                         "committente": committente,
                         "ubicazione": f"{comune} ({prov})", "tipologia": self._meta["label"]}
        esiti = {"safety_critical_pieno": self.ex.safety_critical_pieno,
                 "n_step_ok": self.ex.n_step_ok, "n_step_failed": self.ex.n_step_failed}
        narr = self.narrator.narra(contesto_narr, norme, esiti)

        tracciabilita = [{"step_id": st.step_id, "tool": st.tool,
                          "dimensione": st.iterazione or "globale",
                          "timestamp": st.timestamp, "stato": st.stato.value}
                         for st in self.ex.pipeline_steps]

        def _descr(obj, label):
            return f"{label}: dati disponibili." if obj else "Non applicabile / non valutato."

        return {
            "mode": self.mode,
            "timestamp_generazione": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
            "safety_critical_pieno": self.ex.safety_critical_pieno,
            "gemini_status": narr.gemini_status,
            "narrativa_note": narr.note,
            "professionista": self.profilo,
            "progetto": {"denominazione": contesto_narr["denominazione"],
                         "tipologia": self._meta["label"]},
            "committente": {"ragione_sociale": committente,
                            "sede": _v(s, "A_anagrafica_contesto.indirizzo", "n.d."),
                            "partita_iva": _v(s, "A_anagrafica_contesto.piva", "n.d.")},
            "ubicazione": {"comune": comune, "provincia": prov,
                           "indirizzo": _v(s, "A_anagrafica_contesto.indirizzo", "n.d."),
                           "coordinate": coord_str, "destinazione": "industriale"},
            "impianto": {"tensione_MT": ty.format_tensione((tens_mt or 0) * 1000),
                         "potenza": ty.format_potenza_attiva(P), "sistema": sistema},
            "trasformatori": trasformatori,
            "norme_applicabili": norme,
            "icc": icc,
            "icc_table": icc_table,
            "linee": linee,
            "protezione_terra_descr": _descr(dim.protezione_terra, "Impianto di terra"),
            "rischio_fulmine_descr": (
                "Valutazione del rischio di perdita di vite umane R1 = "
                f"{ty.format_scientific_italian(dim.rischio_fulmine.get('R1_rischio_perdite_vite'))}"
                f" (rif. CEI EN 62305-2)."
                if dim.rischio_fulmine else "Non applicabile / non valutato."),
            "fv_descr": _descr(dim.fv_specifico, "Generazione FV (SPI CEI 0-21)"),
            "ats_descr": _descr(dim.ats_coordinamento, "Coordinamento ATS"),
            "sorgenti_descr": "Vedi schema sorgenti accessorie.",
            "review_richieste": review,
            "tracciabilita": tracciabilita,
            "narrativa": {"premessa": narr.premessa, "conclusioni": narr.conclusioni,
                          "sintesi_normativa": narr.sintesi_normativa},
        }

    # --- render ---
    def _render_docx(self, ctx: dict, path: Path) -> None:
        from docxtpl import DocxTemplate
        try:
            tpl_path = (resources.files(f"k2a_elettrico.tappa3.templates.{self.tipologia}")
                        .joinpath("allegato_h_template.docx"))
        except ModuleNotFoundError as e:
            raise TemplateNotFoundError("Template DOCX non trovato") from e
        with resources.as_file(tpl_path) as p:
            if not Path(p).exists():
                raise TemplateNotFoundError(f"Template DOCX assente: {p}")
            doc = DocxTemplate(str(p))
            doc.render(ctx)
            self._fill_tables(doc.docx, ctx)
            self._apply_review_markers(doc.docx)
            if self.con_grafici:
                self._append_grafici(doc.docx, Path(path).parent / "grafici")
            doc.save(str(path))

    def _append_grafici(self, document, dest_dir: Path) -> None:
        """Appende la sezione 'Grafici' con i PNG generati dal Layer 3 (se disponibili)."""
        from docx.shared import Inches

        from .grafici import genera_grafici
        grafici = genera_grafici(self.ex, dest_dir)
        if not grafici:
            return
        document.add_heading("Allegato — Grafici (generati da K2A, Layer 3)", level=1)
        for didascalia, png in grafici:
            document.add_picture(str(png), width=Inches(5.6))
            cap = document.add_paragraph(didascalia)
            cap.runs[0].italic = True if cap.runs else None

    @staticmethod
    def _fill_tables(document, ctx: dict) -> None:
        """Popola le tabelle (trafo, Icc) aggiungendo una riga per item; le tabelle
        nel template hanno solo l'header e si individuano dalla prima cella."""
        for table in document.tables:
            intest = table.rows[0].cells[0].text.strip().lower()
            if intest == "potenza":  # trasformatori
                for tr in ctx.get("trasformatori", []):
                    c = table.add_row().cells
                    c[0].text = str(tr.get("Sn", ""))
                    c[1].text = str(tr.get("vcc", ""))
                    c[2].text = str(tr.get("tensioni", ""))
                    c[3].text = str(tr.get("gruppo", ""))
            elif intest == "grandezza":  # Icc
                for r in ctx.get("icc_table", []):
                    c = table.add_row().cells
                    c[0].text = str(r.get("grandezza", ""))
                    c[1].text = str(r.get("valore", ""))
                    c[2].text = str(r.get("unita", ""))

    @staticmethod
    def _apply_review_markers(document) -> None:
        """Sostituisce il marker testuale _MARK con un run '(REVIEW)' rosso grassetto.
        Post-processing python-docx dopo il rendering docxtpl."""
        from docx.shared import Pt, RGBColor

        def process(par):
            if _MARK not in par.text:
                return
            parts = par.text.split(_MARK)
            for r in list(par.runs):
                r._element.getparent().remove(r._element)
            for i, part in enumerate(parts):
                if part:
                    par.add_run(part)
                if i < len(parts) - 1:
                    run = par.add_run(" (REVIEW)")
                    run.bold = True
                    run.font.color.rgb = RGBColor(0xC0, 0x00, 0x00)
                    run.font.size = Pt(9)

        for par in document.paragraphs:
            process(par)
        for table in document.tables:
            for row in table.rows:
                for cell in row.cells:
                    for par in cell.paragraphs:
                        process(par)

    def _render_markdown(self, ctx: dict, path: Path) -> None:
        try:
            tpl_text = (resources.files(f"k2a_elettrico.tappa3.templates.{self.tipologia}")
                        .joinpath("relazione_tecnica.md.j2").read_text(encoding="utf-8"))
        except (ModuleNotFoundError, FileNotFoundError) as e:
            raise TemplateNotFoundError("Template markdown non trovato") from e
        env = Environment(autoescape=False)  # markdown, non HTML
        rendered = env.from_string(tpl_text).render(**ctx)
        path.write_text(rendered, encoding="utf-8")


def _profilo_placeholder() -> dict:
    return {"nome": "DA COMPILARE (REVIEW RICHIESTA)", "albo": "—", "iscrizione": "—",
            "codice_fiscale": "—", "partita_iva": "—", "indirizzo": "—"}


def carica_profilo() -> dict:
    p = Path.home() / ".k2a" / "profile.json"
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            pass
    return _profilo_placeholder()
