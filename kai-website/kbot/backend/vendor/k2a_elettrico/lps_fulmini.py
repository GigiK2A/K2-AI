"""Valutazione rischio fulmini + LPS — CEI EN 62305-2 (rischio) + 62305-3 (LPS).

v0.6 — Refactoring debiti tecnici:
  - Sentinel _UNSET (Pydantic model_validator) sostituisce l'euristica "== default"
    per distinguere override esplicito utente da default normativo.
  - Default LA/LB/LU/LV cablati ai literal delle costanti del modulo
    (LT_CONTATTO_PASSO, LF_DANNO_FISICO["industriale_commerciale"] come worst-case plausibile).
  - Esposizione parametri presenza persone nz/nt e tz/8760 (CEI EN 62305-2 §A.2),
    default 1.0 (conservativo) = comportamento v0.5 invariato.

v0.5 — Estensione modello completo R1 (perdita vite umane):
  - modalita="semplificato": comportamento v0.2 invariato (sola componente RA).
  - modalita="completo_62305": calcolo a 3 stadi (iniziale / dopo LPS / finale con SPD)
    con componenti RA + RB + RU + RV, fattori di probabilità (PB, PSPD) e di perdita
    (rp antincendio, rf rischio incendio, hz pericolo speciale) da tabelle CEI EN 62305-2.

Retrocompatibilità: nomi parametro v0.2 invariati (Nt_fulmini_km2_anno, Ce_ambiente,
valore_servizio, Cd_posizione). I campi v0.5 sono opzionali con default = comportamento v0.2.
"""
from __future__ import annotations
import math
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, PrivateAttr, model_validator


# ====================================================================
# SENTINEL _UNSET (v0.6) — distingue default normativo da override esplicito
# ====================================================================

class _UnsetType:
    """Sentinel singleton per distinguere 'default non passato' da 'override esplicito'."""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __repr__(self) -> str:
        return "_UNSET"

    def __bool__(self) -> bool:
        return False


_UNSET = _UnsetType()


# ====================================================================
# TABELLE CEI EN 62305-2
# ====================================================================

# Tab. B.2 — Probabilità PB di danno fisico in funzione della classe di LPS
PB_LPS: dict[str, float] = {"nessuno": 1.0, "IV": 0.2, "III": 0.1, "II": 0.05, "I": 0.02}

# Tab. B.3 — Probabilità PSPD in funzione del livello di protezione degli SPD coordinati
PSPD_COORD: dict[str, float] = {"nessuno": 1.0, "III-IV": 0.05, "II": 0.02, "I": 0.01}

# Tab. C.5 — Fattore rp di riduzione perdita in funzione delle misure antincendio
RP_ANTINCENDIO: dict[str, float] = {"nessuna": 1.0, "manuale": 0.5, "automatico": 0.2}

# Tab. C.4 — Fattore rf di rischio incendio/esplosione della struttura
# Blitzplaner DEHN 2016 ed. italiana, Tab. 3.2.5.3 (pag. 45)
# Riferimento normativo: CEI EN 62305-2 (CEI 81-10/2), Allegato C
# NB: "esplosivo" = Zona 0/20 ed esplosivi solidi (=1.0).
RF_INCENDIO: dict[str, float] = {
    "no": 0.0, "basso": 1e-3, "ordinario": 1e-2, "elevato": 1e-1, "esplosivo": 1.0,
    "zona_esplosione_1_21": 1e-1, "zona_esplosione_2_22": 1e-3,
}

# Tab. C.6 — Fattore hz di aumento perdita in presenza di pericolo speciale
# Blitzplaner DEHN 2016 ed. italiana, Tab. 3.2.5.4 (pag. 45)
# Riferimento normativo: CEI EN 62305-2 (CEI 81-10/2), Allegato C
HZ_PERICOLO: dict[str, float] = {
    "nessuno": 1.0, "panico_basso": 2.0, "panico_medio": 5.0,
    "evacuazione_difficile": 5.0, "panico_alto": 10.0,
}

# Cd_l fattore posizione linea (Tab. A.2) — interrata schermo terra vs aerea
CD_LINEA_POSA: dict[str, float] = {"aerea": 1.0, "interrata": 0.5}

# Tab. C.3 — Fattore rt di riduzione effetti tensioni di contatto/passo (tipo superficie)
# Blitzplaner DEHN 2016 ed. italiana, Tab. 3.2.5.1 (pag. 44)
# Riferimento normativo: CEI EN 62305-2 (CEI 81-10/2), Allegato C
RT_SUPERFICIE: dict[str, float] = {
    "agricola_calcestruzzo": 1e-2,   # resistenza di contatto ≤ 1 kΩ
    "marmo_ceramica": 1e-3,          # 1-10 kΩ
    "ghiaia_moquette_tappeti": 1e-4, # 10-100 kΩ
    "asfalto_linoleum_legno": 1e-5,  # ≥ 100 kΩ
}

# Tab. C.2 — Valore di perdita LT per lesioni da tensioni di contatto/passo (danno D1)
# Blitzplaner DEHN 2016 ed. italiana, Tab. 3.2.5.5 riga D1 (pag. 45)
# Riferimento normativo: CEI EN 62305-2 (CEI 81-10/2), Allegato C
# Valore unico per TUTTI i tipi di struttura (non varia per destinazione).
LT_CONTATTO_PASSO: float = 1e-2

# Tab. C.2 — Valore di perdita LF per danno fisico (danno D2), per destinazione struttura
# Blitzplaner DEHN 2016 ed. italiana, Tab. 3.2.5.5 riga D2 (pag. 45)
# Riferimento normativo: CEI EN 62305-2 (CEI 81-10/2), Allegato C
# NB: LF è il valore PURO; rp/rf/hz sono applicati separatamente (componente_RB/RV).
LF_DANNO_FISICO: dict[str, float] = {
    "rischio_esplosione": 1e-1,
    "ospedale_albergo_scuola_pubblico": 1e-1,
    "intrattenimento_chiesa_museo": 5e-2,
    "industriale_commerciale": 2e-2,
    "altri": 1e-2,
}

# Tab. C.7 — Valore di perdita LO per guasto impianti interni (danno D3)
# Blitzplaner DEHN 2016 ed. italiana, Tab. 3.2.5.5 riga D3 (pag. 45)
# Riferimento normativo: CEI EN 62305-2 (CEI 81-10/2), Allegato C
# Placeholder: NON usato in R1 base (RA+RB+RU+RV). Riservato a estensione futura
# delle componenti RC/RM/RW/RZ (guasto sistemi interni).
LO_GUASTO_INTERNI: dict[str, float] = {
    "rischio_esplosione": 1e-1,
    "ospedale_terapia_intensiva_sala_operatoria": 1e-2,
    "ospedale_altre_zone": 1e-3,
}


# ====================================================================
# HELPER COMPONENTI (riusabili — CEI EN 62305-2 §A-B)
# ====================================================================

def calcola_Ad(L_m: float, W_m: float, H_m: float) -> float:
    """Area di raccolta struttura. CEI EN 62305-2 §A.2: Ad = L·W + 6H·(L+W) + 9π·H²."""
    return L_m * W_m + 6 * H_m * (L_m + W_m) + 9 * math.pi * H_m ** 2


def calcola_Nd(Ng: float, Ad_m2: float, Cd: float = 1.0) -> float:
    """N. eventi/anno fulminazione diretta struttura. CEI EN 62305-2 §A.2.1."""
    return Ng * Ad_m2 * Cd * 1e-6


def calcola_Nl(Ng: float, Al_m2: float, Cd_l: float = 1.0, Ct: float = 1.0) -> float:
    """N. eventi/anno fulminazione diretta linea entrante. CEI EN 62305-2 §A.4."""
    return Ng * Al_m2 * Cd_l * Ct * 1e-6


def calcola_Ni(Ng: float, Ai_m2: float, Ce: float = 1.0, Ct: float = 1.0) -> float:
    """N. eventi/anno fulminazione in prossimità della linea. CEI EN 62305-2 §A.5."""
    return Ng * Ai_m2 * Ce * Ct * 1e-6


def componente_RA(Nd: float, PA: float, LA: float) -> float:
    """R_A: tensioni di contatto/passo da fulmine diretto su struttura. §B.1."""
    return Nd * PA * LA


def componente_RB(Nd: float, PB: float, LB: float,
                  rp: float = 1.0, rf: float = 1.0, hz: float = 1.0) -> float:
    """R_B: danno fisico/incendio da fulmine diretto su struttura. §B.2."""
    return Nd * PB * LB * rp * rf * hz


def componente_RU(Nl: float, PU: float, LU: float, PEB: float = 1.0) -> float:
    """R_U: tensioni di contatto/passo da fulmine su linea entrante. §B.5."""
    return Nl * PU * LU * PEB


def componente_RV(Nl: float, PV: float, LV: float,
                  rp: float = 1.0, rf: float = 1.0, hz: float = 1.0) -> float:
    """R_V: danno fisico da fulmine su linea entrante. §B.6."""
    return Nl * PV * LV * rp * rf * hz


# ====================================================================
# MODELLI I/O
# ====================================================================

class LineaEntrante(BaseModel):
    """Linea di servizio entrante (energia MT/BT, dati/TLC). CEI EN 62305-2 §A.4-A.5."""
    tipo: Literal["MT", "BT", "dati"] = "MT"
    Lc_m: float = Field(200.0, gt=0, description="Lunghezza tratto di linea [m] (max 1000)")
    posa: Literal["aerea", "interrata"] = "interrata"
    Ct: float = Field(1.0, description="Fattore trasformatore HV/LV sulla linea (Tab. A.3): 0.2 se presente, 1.0 altrimenti")
    Al_m2_override: float | None = Field(None, description="Override area raccolta diretta linea; default 40·Lc")
    Ai_m2_override: float | None = Field(None, description="Override area influenza linea; default 4000 (placeholder conservativo)")


class ValutazioneRischioFulmineInput(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    # === Input base v0.2 (nomi INVARIATI per retrocompatibilità) ===
    Nt_fulmini_km2_anno: float = Field(2.5, gt=0, description="Densità fulmini Ng [1/km²/anno] (Italia: 1-4; max sud)")
    L_m: float = Field(..., gt=0, description="Lunghezza struttura [m]")
    W_m: float = Field(..., gt=0, description="Larghezza struttura [m]")
    H_m: float = Field(..., gt=0, description="Altezza struttura [m]")
    Cd_posizione: float = Field(1.0, description="Fattore posizione (Tab. A.1): 0.25/0.5/1.0/2.0")
    Ce_ambiente: Literal["urbano", "suburbano", "rurale"] = "rurale"
    valore_servizio: Literal["ordinario", "essenziale", "critico_TLC", "ospedale"] = "ordinario"
    R_tollerabile: float = Field(1e-5, description="Rischio R1 tollerabile vite umane (CEI 62305-2: 10⁻⁵/anno)")

    # === Estensioni v0.5 (opzionali; default = comportamento v0.2) ===
    modalita: Literal["semplificato", "completo_62305"] = "semplificato"
    Ad_override_m2: float | None = Field(None, description="Se passato, salta il calcolo geometrico di Ad")

    linee_entranti: list[LineaEntrante] = Field(default_factory=list, description="Linee di servizio entranti (default: nessuna → RU=RV=0)")

    LPS_classe: Literal["nessuno", "I", "II", "III", "IV"] = "nessuno"
    SPD_livello: Literal["nessuno", "I", "II", "III-IV"] = "nessuno"

    misure_antincendio: Literal["nessuna", "manuale", "automatico"] = "nessuna"
    rischio_incendio: Literal["no", "basso", "ordinario", "elevato", "esplosivo"] = "ordinario"
    pericolo_speciale: Literal["nessuno", "panico_basso", "panico_medio", "panico_alto", "evacuazione_difficile"] = "nessuno"
    misure_contatto_passo: Literal["nessuna", "equipotenziale", "isolante", "barriere"] = "nessuna"

    # === v0.5.1 — Parametri "destinazione-style" (α): derivazione auto da costanti Annex C ===
    destinazione: Literal[
        "residenziale_altri", "industriale_commerciale",
        "intrattenimento_chiesa_museo", "ospedale_albergo_scuola_pubblico",
        "esplosione",
    ] | None = Field(None, description="α: deriva LB/LV da LF_DANNO_FISICO (Blitzplaner Tab. 3.2.5.5)")
    pavimento_tipo: Literal[
        "agricola_calcestruzzo", "marmo_ceramica",
        "ghiaia_moquette_tappeti", "asfalto_linoleum_legno",
    ] | None = Field(None, description="α: deriva LA/LU da rt·LT (Blitzplaner Tab. 3.2.5.1)")

    # CEI EN 62305-2:2013 Annex C — Fattori di perdita L per R1 (vite umane)
    #
    # LA e LU = perdita per tensioni di contatto/passo: rt · LT (Tab. C.3 × C.2).
    # LB e LV = perdita per DANNO FISICO da fulmine: LF puro (Tab. C.2); rp/rf/hz
    #     applicati come ARGOMENTI SEPARATI a componente_RB/RV (no double-count).
    #
    # v0.6 — DEFAULT CABLATI alle costanti del modulo via sentinel _UNSET:
    #     LA = LU = LT_CONTATTO_PASSO (1e-2)  [worst case rt=1: nessuna riduzione di
    #         superficie; più conservativo e onesto del precedente 1e-4 che assumeva
    #         implicitamente rt=1e-2 cemento. Blitzplaner pag. 44, Tab. 3.2.5.1/5.5]
    #     LB = LV = LF_DANNO_FISICO["industriale_commerciale"] (2e-2)  [worst-case
    #         plausibile per destinazione non specificata; NON "altri" (1e-2) che
    #         sarebbe meno conservativo del default v0.5. Blitzplaner pag. 45, Tab. 3.2.5.5]
    # Se l'utente passa un valore esplicito, il sentinel registra l'override
    # (flag _LA_explicit ecc.) per il trace asseverativo e per la logica α/β.
    LA: float | _UnsetType = Field(_UNSET, description="Perdita contatto/passo (vite umane): rt·LT, Tab. C.2-C.3. Default = LT_CONTATTO_PASSO (1e-2)")
    LB: float | _UnsetType = Field(_UNSET, description="Perdita danno fisico (vite umane): LF puro Tab. C.2. Default conservativo = LF['industriale_commerciale'] (2e-2)")
    LU: float | _UnsetType = Field(_UNSET, description="Perdita contatto/passo da linea (vite umane): rt·LT, Tab. C.3. Default = LT_CONTATTO_PASSO (1e-2)")
    LV: float | _UnsetType = Field(_UNSET, description="Perdita danno fisico da linea (vite umane): LF puro Tab. C.2. Default conservativo = LF['industriale_commerciale'] (2e-2)")

    # === v0.6 — Presenza persone (CEI EN 62305-2 §A.2): fattori di perdita L ===
    nz_su_nt: float = Field(
        1.0, gt=0, le=1.0,
        description="Rapporto numero persone esposte / numero totale persone (CEI EN 62305-2 §A.2). "
                    "Default 1.0 = tutti esposti (conservativo). Per strutture con presenza parziale: < 1.0",
    )
    tz_su_8760: float = Field(
        1.0, gt=0, le=1.0,
        description="Rapporto ore di presenza / ore anno (CEI EN 62305-2 §A.2). "
                    "Default 1.0 = 8760h/anno (conservativo). Per uffici 8h/giorno × 220gg/anno: 1760/8760 ≈ 0.2",
    )
    validate_runtime: bool = Field(False, description="Modalità C runtime (ADR-009): cross-validation inline "
                                                      "(solo modalità completo_62305).")
    with_kb_references: bool = Field(False, description="Tappa 2: include riferimenti normativi KB in riferimenti_kb.")
    dynamic_kb: bool = Field(False, description="Tappa 2 Fase 2: con with_kb_references, recupera i verbatim live dalla KB invece dello snapshot statico. Default False.")
    validate_kb_values: bool = Field(False, description="Tappa 2 Fase 2: con with_kb_references, valida i valori normativi del tool contro i verbatim KB (campo kb_validation). Default False.")

    # Flag privati (v0.6): tracciano se LA/LB/LU/LV sono override espliciti
    _LA_explicit: bool = PrivateAttr(default=False)
    _LB_explicit: bool = PrivateAttr(default=False)
    _LU_explicit: bool = PrivateAttr(default=False)
    _LV_explicit: bool = PrivateAttr(default=False)

    @model_validator(mode="after")
    def _resolve_perdite_default(self):
        """Risolve i sentinel _UNSET con i default normativi e registra gli override."""
        self._LA_explicit = not isinstance(self.LA, _UnsetType)
        self._LB_explicit = not isinstance(self.LB, _UnsetType)
        self._LU_explicit = not isinstance(self.LU, _UnsetType)
        self._LV_explicit = not isinstance(self.LV, _UnsetType)
        if isinstance(self.LA, _UnsetType):
            self.LA = LT_CONTATTO_PASSO
        if isinstance(self.LU, _UnsetType):
            self.LU = LT_CONTATTO_PASSO
        # Default conservativo per asseverazione: struttura industriale/commerciale
        # generica (2e-2). NON è LF_DANNO_FISICO['altri'] (1e-2): quel valore è MENO
        # conservativo del default v0.5 e adatto solo a strutture classificate "altri".
        # Rollback regressione conservatività v0.6 — vedi case study, master plan §13.
        if isinstance(self.LB, _UnsetType):
            self.LB = LF_DANNO_FISICO["industriale_commerciale"]
        if isinstance(self.LV, _UnsetType):
            self.LV = LF_DANNO_FISICO["industriale_commerciale"]
        return self


class ComponentiStadio(BaseModel):
    RA: float
    RB: float
    RU: float
    RV: float
    R1: float


class ValutazioneRischioOutput(BaseModel):
    # Campi v0.2 (sempre presenti)
    Ad_area_raccolta_m2: float
    Nd_eventi_pericolosi_anno: float
    R1_rischio_perdite_vite: float
    LPS_richiesto: bool
    livello_LPL_consigliato: Literal["nessuno", "IV", "III", "II", "I"]
    classe_LPS: str
    trace: dict
    # Campi v0.5 (popolati solo in modalita="completo_62305")
    modalita: str = "semplificato"
    Nl_eventi_linea_anno: float | None = None
    Ni_eventi_vicino_linea_anno: float | None = None
    stadio_1_iniziale: ComponentiStadio | None = None
    stadio_2_dopo_LPS: ComponentiStadio | None = None
    stadio_3_finale_LPS_SPD: ComponentiStadio | None = None
    R1_iniziale: float | None = None
    R1_finale: float | None = None
    conforme_finale: bool | None = None
    componente_dominante: str | None = None
    fattori_applicati: dict | None = None
    # Modalità C runtime (ADR-009)
    cross_validation_eseguita: bool = False
    cross_validation_esito: str = "NON_ESEGUITA"
    cross_validation_delta_pct: dict = Field(default_factory=dict)
    cross_validation_note: list[str] = Field(default_factory=list)
    riferimenti_kb: list[dict] = Field(default_factory=list)
    kb_validation: list[dict] = Field(default_factory=list)


# ====================================================================
# FUNZIONE PRINCIPALE
# ====================================================================

def valuta_rischio_fulmine(inp: ValutazioneRischioFulmineInput) -> ValutazioneRischioOutput:
    Ng = inp.Nt_fulmini_km2_anno
    Ad = inp.Ad_override_m2 if inp.Ad_override_m2 is not None else calcola_Ad(inp.L_m, inp.W_m, inp.H_m)
    Nd = calcola_Nd(Ng, Ad, inp.Cd_posizione)

    # ---------- MODALITÀ SEMPLIFICATA (v0.2 — comportamento INVARIATO) ----------
    if inp.modalita == "semplificato":
        LA_simpl = {"ordinario": 1e-2, "essenziale": 1e-1, "critico_TLC": 1e-1, "ospedale": 1.0}[inp.valore_servizio]
        rA = {"urbano": 1e-3, "suburbano": 1e-3, "rurale": 1e-2}[inp.Ce_ambiente]
        R1 = Nd * 1.0 * rA * LA_simpl
        LPS_needed = R1 > inp.R_tollerabile
        if not LPS_needed:
            LPL, classe = "nessuno", "non necessaria (R1 ≤ R_T)"
        else:
            ratio = R1 / inp.R_tollerabile
            if ratio > 10:    LPL, classe = "I",  "Classe I (Iimp=200 kA, maglia 5×5 m, palo Ø10mm)"
            elif ratio > 4:   LPL, classe = "II", "Classe II (Iimp=150 kA, maglia 10×10 m, palo Ø8mm)"
            elif ratio > 2:   LPL, classe = "III","Classe III (Iimp=100 kA, maglia 15×15 m, palo Ø8mm)"
            else:             LPL, classe = "IV", "Classe IV (Iimp=100 kA, maglia 20×20 m, palo Ø8mm)"
        _out = ValutazioneRischioOutput(
            Ad_area_raccolta_m2=round(Ad, 1),
            Nd_eventi_pericolosi_anno=round(Nd, 8),
            R1_rischio_perdite_vite=round(R1, 10),
            LPS_richiesto=LPS_needed,
            livello_LPL_consigliato=LPL,
            classe_LPS=classe,
            modalita="semplificato",
            trace={
                "norma": "CEI EN 62305-2 (valutazione rischio) + 62305-3 (LPS)",
                "formula_Ad": "Ad = L·W + 6H·(L+W) + 9π·H²",
                "formula_Nd": "Nd = Nt × Ad × Cd × 10⁻⁶",
                "soglia": f"R_T = {inp.R_tollerabile} (perdita vite umane CEI 62305-2)",
                "semplificazione": "Solo componente RA. Per il modello completo usare modalita='completo_62305'.",
                **({"nota_presenza": "nz/nt e tz/8760 ignorati in modalità semplificato (legacy v0.2); usare completo_62305"}
                   if (inp.nz_su_nt != 1.0 or inp.tz_su_8760 != 1.0) else {}),
            },
        )
        from ._cross_validation import finalize
        return finalize(inp, _out, "valuta_rischio_fulmine", {"modalita": inp.modalita})

    # ---------- MODALITÀ COMPLETA 62305-2 (RA + RB + RU + RV, 3 stadi) ----------
    Ce = {"urbano": 0.1, "suburbano": 0.5, "rurale": 1.0}[inp.Ce_ambiente]

    # Eventi sulle linee entranti
    Nl_tot, Ni_tot = 0.0, 0.0
    for ln in inp.linee_entranti:
        Al = ln.Al_m2_override if ln.Al_m2_override is not None else 40.0 * ln.Lc_m
        Ai = ln.Ai_m2_override if ln.Ai_m2_override is not None else 4000.0
        Cd_l = CD_LINEA_POSA[ln.posa]
        Nl_tot += calcola_Nl(Ng, Al, Cd_l, ln.Ct)
        Ni_tot += calcola_Ni(Ng, Ai, Ce, ln.Ct)

    # Fattori di perdita/riduzione (tabelle CEI)
    rp = RP_ANTINCENDIO[inp.misure_antincendio]
    rf = RF_INCENDIO[inp.rischio_incendio]
    hz = HZ_PERICOLO[inp.pericolo_speciale]

    # Probabilità tensioni di contatto/passo (PA, PU) ridotte da misure dedicate
    PA_factor = {"nessuna": 1.0, "equipotenziale": 1.0, "isolante": 1e-2, "barriere": 0.0}[inp.misure_contatto_passo]
    PA, PU_base = PA_factor, 1.0

    # === Derivazione default da costanti CEI EN 62305-2 Annex C (Blitzplaner pag. 44-46) ===
    # α (destinazione/pavimento → derivazione auto) + β (override esplicito vince, con WARNING).
    #
    # v0.6 — rilevamento override basato sui flag del sentinel _UNSET
    # (self._LA_explicit ecc.), non più sull'euristica fragile "== default".
    trace_derivazioni: list[str] = []
    DEST_TO_LF = {
        "residenziale_altri": "altri",
        "industriale_commerciale": "industriale_commerciale",
        "intrattenimento_chiesa_museo": "intrattenimento_chiesa_museo",
        "ospedale_albergo_scuola_pubblico": "ospedale_albergo_scuola_pubblico",
        "esplosione": "rischio_esplosione",
    }
    LA_eff, LB_eff, LU_eff, LV_eff = inp.LA, inp.LB, inp.LU, inp.LV
    LA_derivato = LU_derivato = LB_derivato = LV_derivato = False

    if inp.destinazione is not None:
        LF_d = LF_DANNO_FISICO[DEST_TO_LF[inp.destinazione]]
        if not inp._LB_explicit:
            LB_eff = LF_d
            LB_derivato = True
            trace_derivazioni.append(f"LB derivato da destinazione='{inp.destinazione}' → {LB_eff:.0e} (LF Tab. 3.2.5.5 Blitzplaner)")
        else:
            trace_derivazioni.append(f"WARNING: destinazione='{inp.destinazione}' suggerirebbe LB={LF_d:.0e}, ma usato override esplicito LB={inp.LB:.0e}")
        if not inp._LV_explicit:
            LV_eff = LF_d
            LV_derivato = True
            trace_derivazioni.append(f"LV derivato da destinazione='{inp.destinazione}' → {LV_eff:.0e}")
        else:
            trace_derivazioni.append(f"WARNING: destinazione='{inp.destinazione}' suggerirebbe LV={LF_d:.0e}, ma usato override esplicito LV={inp.LV:.0e}")

    if inp.pavimento_tipo is not None:
        rt_p = RT_SUPERFICIE[inp.pavimento_tipo]
        LA_p = rt_p * LT_CONTATTO_PASSO
        if not inp._LA_explicit:
            LA_eff = LA_p
            LA_derivato = True
            trace_derivazioni.append(f"LA derivato da pavimento_tipo='{inp.pavimento_tipo}' → rt={rt_p:.0e}·LT={LT_CONTATTO_PASSO:.0e} = {LA_eff:.0e}")
        else:
            trace_derivazioni.append(f"WARNING: pavimento_tipo='{inp.pavimento_tipo}' suggerirebbe LA={LA_p:.0e}, ma usato override esplicito LA={inp.LA:.0e}")
        if not inp._LU_explicit:
            LU_eff = LA_p
            LU_derivato = True
            trace_derivazioni.append(f"LU derivato da pavimento_tipo='{inp.pavimento_tipo}' → {LU_eff:.0e}")
        else:
            trace_derivazioni.append(f"WARNING: pavimento_tipo='{inp.pavimento_tipo}' suggerirebbe LU={LA_p:.0e}, ma usato override esplicito LU={inp.LU:.0e}")

    # v0.6 — trace sorgente per i parametri NON derivati da α: default normativo vs override β
    def _trace_sorgente(nome: str, explicit: bool, derivato: bool, valore: float, default_label: str):
        if derivato:
            return  # già tracciato sopra (derivazione α)
        if explicit:
            trace_derivazioni.append(f"{nome}: override esplicito utente = {valore:.0e}")
        else:
            trace_derivazioni.append(f"{nome}: default da {default_label}")

    _trace_sorgente("LA", inp._LA_explicit, LA_derivato, LA_eff, "LT_CONTATTO_PASSO=1e-2 (Blitzplaner pag. 44)")
    _trace_sorgente("LB", inp._LB_explicit, LB_derivato, LB_eff, "conservativo 'industriale_commerciale'=2e-2 (Blitzplaner pag. 45; per strutture specifiche passare destinazione esplicita o LB override)")
    _trace_sorgente("LU", inp._LU_explicit, LU_derivato, LU_eff, "LT_CONTATTO_PASSO=1e-2 (Blitzplaner pag. 44)")
    _trace_sorgente("LV", inp._LV_explicit, LV_derivato, LV_eff, "conservativo 'industriale_commerciale'=2e-2 (Blitzplaner pag. 45; per strutture specifiche passare destinazione esplicita o LV override)")

    # v0.6 — Fattore presenza persone (CEI EN 62305-2 §A.2): (nz/nt)·(tz/8760)
    presenza = inp.nz_su_nt * inp.tz_su_8760
    if presenza != 1.0:
        trace_derivazioni.append(
            f"Presenza persone: (nz/nt={inp.nz_su_nt:g})·(tz/8760={inp.tz_su_8760:g}) = {presenza:g} "
            "applicato a tutte le componenti R1 (§A.2)"
        )

    def _stadio(PB: float, PSPD: float) -> ComponentiStadio:
        RA = componente_RA(Nd, PA, LA_eff) * presenza
        RB = componente_RB(Nd, PB, LB_eff, rp, rf, hz) * presenza
        RU = componente_RU(Nl_tot, PSPD * PU_base, LU_eff) * presenza
        RV = componente_RV(Nl_tot, PSPD * 1.0, LV_eff, rp, rf, hz) * presenza
        return ComponentiStadio(RA=RA, RB=RB, RU=RU, RV=RV, R1=RA + RB + RU + RV)

    # Stadio 1: struttura nuda
    s1 = _stadio(PB=PB_LPS["nessuno"], PSPD=PSPD_COORD["nessuno"])
    # Stadio 2: con LPS dichiarato (nessun SPD)
    s2 = _stadio(PB=PB_LPS[inp.LPS_classe], PSPD=PSPD_COORD["nessuno"])
    # Stadio 3: LPS + SPD coordinati dichiarati
    s3 = _stadio(PB=PB_LPS[inp.LPS_classe], PSPD=PSPD_COORD[inp.SPD_livello])

    conforme = s3.R1 <= inp.R_tollerabile
    comp_dom = max([("RA", s3.RA), ("RB", s3.RB), ("RU", s3.RU), ("RV", s3.RV)], key=lambda x: x[1])[0]

    # LPL "consigliato" coerente con campo v0.2: se s3 conforme → LPS dichiarato sufficiente
    if conforme:
        LPL_out = inp.LPS_classe if inp.LPS_classe != "nessuno" else "nessuno"
        classe_txt = f"LPS {inp.LPS_classe} + SPD {inp.SPD_livello} → R1 conforme (≤ R_T)"
    else:
        LPL_out = "I"
        classe_txt = "LPS/SPD dichiarati INSUFFICIENTI → R1 > R_T, rafforzare protezioni"

    _out = ValutazioneRischioOutput(
        Ad_area_raccolta_m2=round(Ad, 1),
        Nd_eventi_pericolosi_anno=round(Nd, 8),
        R1_rischio_perdite_vite=round(s1.R1, 12),   # campo v0.2 = R1 iniziale (struttura nuda)
        LPS_richiesto=s1.R1 > inp.R_tollerabile,
        livello_LPL_consigliato=LPL_out,
        classe_LPS=classe_txt,
        modalita="completo_62305",
        Nl_eventi_linea_anno=round(Nl_tot, 8),
        Ni_eventi_vicino_linea_anno=round(Ni_tot, 8),
        stadio_1_iniziale=s1,
        stadio_2_dopo_LPS=s2,
        stadio_3_finale_LPS_SPD=s3,
        R1_iniziale=round(s1.R1, 12),
        R1_finale=round(s3.R1, 12),
        conforme_finale=conforme,
        componente_dominante=comp_dom,
        fattori_applicati={
            "Ng": Ng, "Ad_m2": round(Ad, 1), "Cd": inp.Cd_posizione, "Ce": Ce,
            "rp_antincendio": rp, "rf_incendio": rf, "hz_pericolo": hz, "PA": PA,
            "PB_LPS": PB_LPS[inp.LPS_classe], "PSPD": PSPD_COORD[inp.SPD_livello],
            "LA": LA_eff, "LB": LB_eff, "LU": LU_eff, "LV": LV_eff,
            "nz_su_nt": inp.nz_su_nt, "tz_su_8760": inp.tz_su_8760, "presenza": presenza,
            "n_linee_entranti": len(inp.linee_entranti),
        },
        trace={
            "norma": "CEI EN 62305-2:2013 §A-C (rischio R1 vite umane)",
            "componenti": "R1 = RA + RB + RU + RV",
            "stadi": "1=struttura nuda · 2=+LPS · 3=+LPS+SPD coordinati",
            "soglia": f"R_T = {inp.R_tollerabile}",
            "note_tabelle": "rp Tab.C.5 · rf Tab.C.4 · hz Tab.C.6 · PB Tab.B.2 · PSPD Tab.B.3",
            "derivazioni_default_costanti": trace_derivazioni,
        },
    )
    from ._cross_validation import finalize
    return finalize(inp, _out, "valuta_rischio_fulmine", {"modalita": inp.modalita})
