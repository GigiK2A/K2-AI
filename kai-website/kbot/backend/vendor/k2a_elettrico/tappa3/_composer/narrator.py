"""Narratore LLM del Layer 4 — SOLO prosa narrativa, MAI numeri.

Genera premessa, sintesi normativa e conclusioni testuali per la relazione. Usa
gemini-2.5-flash (SDK google-genai). Su 503/errore/chiave mancante ricade su testo
standard pre-scritto (fallback graceful) e lo segnala: non blocca mai la generazione.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from k2a_elettrico.tappa3._core.classifier import DEFAULT_MODEL, _load_api_key

SYSTEM = """Sei un assistente che redige paragrafi narrativi per relazioni tecniche di
impianti elettrici italiani. Scrivi in italiano tecnico formale, terza persona, presente.
REGOLE FERREE:
1. NON inventare numeri. Se non sono nel contesto, resta generico.
2. NON inventare riferimenti normativi specifici (articoli/paragrafi). Cita solo le norme
   presenti nel contesto.
3. NON esprimere giudizi di conformità/non conformità (sono dell'ingegnere asseverante).
4. Tono asciutto, professionale, senza enfasi. Rispetta la lunghezza richiesta.
Restituisci SOLO il paragrafo richiesto, senza titoli.
"""

_FALLBACK_PREMESSA = (
    "La presente relazione documenta le verifiche elettrotecniche eseguite per "
    "l'impianto in oggetto, condotte mediante strumenti di calcolo deterministici e "
    "riferite alle norme tecniche applicabili. I risultati numerici riportati derivano "
    "integralmente dai calcoli e sono tracciati nell'apposita appendice.")
_FALLBACK_CONCLUSIONI = (
    "Sulla base delle verifiche e dei calcoli riportati, l'impianto risulta descritto in "
    "modo completo nei suoi parametri elettrici principali. La valutazione finale di "
    "conformità e la sottoscrizione competono al professionista incaricato, previa "
    "revisione delle assunzioni evidenziate.")
_FALLBACK_SINTESI = (
    "Il quadro normativo di riferimento comprende le norme tecniche applicabili "
    "all'impianto, richiamate nell'apposita sezione, per gli aspetti di dimensionamento, "
    "protezione e sicurezza.")


@dataclass
class NarratorOutput:
    premessa: str
    conclusioni: str
    sintesi_normativa: str
    gemini_status: str = "fallback"  # "ok" | "fallback"
    note: list[str] = field(default_factory=list)


class Narrator:
    def __init__(self, api_key: str | None = None, client=None,
                 model_name: str = DEFAULT_MODEL):
        self.model_name = model_name
        self._fallback = False
        self.note: list[str] = []
        if client is not None:
            self._client = client
        else:
            key = api_key or _load_api_key()
            if not key:
                self._client = None
                self._fallback = True
                self.note.append("Chiave Gemini assente: narrativa di fallback.")
            else:
                try:
                    from google import genai
                    self._client = genai.Client(api_key=key)
                except Exception as e:  # noqa: BLE001
                    self._client = None
                    self._fallback = True
                    self.note.append(f"Init Gemini fallito: {str(e)[:80]}")

    def _gen(self, prompt: str, fallback: str, max_parole: int) -> str:
        if self._client is None:
            self._fallback = True
            return fallback
        try:
            resp = self._client.models.generate_content(
                model=self.model_name, contents=SYSTEM + "\n\n" + prompt)
            text = (getattr(resp, "text", None) or "").strip()
            if not text:
                self._fallback = True
                self.note.append("Risposta Gemini vuota: fallback.")
                return fallback
            return text
        except Exception as e:  # noqa: BLE001 — 503/rete/altro
            self._fallback = True
            self.note.append(f"Gemini errore ({str(e)[:60]}): fallback.")
            return fallback

    def genera_premessa(self, contesto: dict) -> str:
        p = (f"Redigi una premessa (150-250 parole) per la relazione dell'impianto "
             f"'{contesto.get('denominazione','')}', committente "
             f"'{contesto.get('committente','')}', ubicato a "
             f"'{contesto.get('ubicazione','')}', tipologia "
             f"'{contesto.get('tipologia','')}'. Non citare numeri specifici.")
        return self._gen(p, _FALLBACK_PREMESSA, 250)

    def genera_sintesi_normativa(self, norme: list[str]) -> str:
        p = ("Inquadra in un paragrafo (max 150 parole) il seguente elenco di norme "
             f"applicabili, senza citare articoli specifici: {', '.join(norme)}.")
        return self._gen(p, _FALLBACK_SINTESI, 150)

    def genera_conclusioni(self, esiti: dict) -> str:
        p = ("Redigi conclusioni (100-200 parole) per una relazione tecnica di impianto "
             "elettrico. Non esprimere giudizio di conformità. Indica che la valutazione "
             "finale e la firma competono al professionista. Riferimento esiti (flag "
             f"booleani, non numeri): {esiti}.")
        return self._gen(p, _FALLBACK_CONCLUSIONI, 200)

    def narra(self, contesto: dict, norme: list[str], esiti: dict) -> NarratorOutput:
        prem = self.genera_premessa(contesto)
        sint = self.genera_sintesi_normativa(norme)
        concl = self.genera_conclusioni(esiti)
        return NarratorOutput(premessa=prem, conclusioni=concl, sintesi_normativa=sint,
                              gemini_status="fallback" if self._fallback else "ok",
                              note=list(self.note))
