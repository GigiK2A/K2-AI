"""«Trovami clienti in Umbria» deve cercare davvero, non ricordare.

Caso reale del 20 ago 2026: l'owner chiede clienti in Umbria escludendo gli studi di
ingegneria. Marketing risponde con Studio Muzi (telefono 06, quindi Roma), P.M. Italia e
Studio Fiammarelli — aziende sparse per l'Italia, senza una riga su cosa fanno e con
«contatto via form web» al posto del contatto. Causa: in chat gli agenti NON hanno la
ricerca web (è un server-tool, scartato per OpenAI e per il locale), quindi il modello
ha risposto a memoria. E Sales ha proposto come lead `test@k2ai.com`.
"""
from aios.chat_runner import _CERCA_CLIENTI_DEF
from aios.prospecting import Prospector


class LLMWebFinto:
    """Finge la ricerca web: restituisce il testo grezzo che riceve nel prompt."""

    def __init__(self):
        self.prompt = ""

    def complete(self, *, system, user):
        self.prompt = user
        return "risultati grezzi"


class LLMStruct:
    def __init__(self, prospects):
        self._p = prospects
        self.prompt = ""

    def complete_json(self, *, system, user, schema=None):
        self.prompt = user
        return {"prospects": self._p}


class Founder:
    def to_prompt(self):
        return "K2-AI"


def _prospector(prospects):
    web, struct = LLMWebFinto(), LLMStruct(prospects)
    return Prospector(web, struct, Founder(), suite_reader=lambda: []), web, struct


def _p(nome, zona, fit=80, attivita="fa cose", email="info@x.it", in_zona=True):
    return {"company": nome, "zona": zona, "attivita": attivita, "in_zona": in_zona,
            "sector": "manifatturiero",
            "in_target": True, "fit_score": fit, "fit_reason": "processi manuali",
            "contact_email": email, "contact_phone": "075 1234567",
            "email_source": "sito, pagina contatti", "website": "https://x.it",
            "draft_subject": "s", "draft_body": "b"}


# ---- il vincolo geografico ----
def test_la_zona_entra_nel_prompt_come_vincolo():
    pros, web, struct = _prospector([_p("Alfa", "Perugia (PG)")])
    pros.find(3, zona="Umbria", esclusioni="studi di ingegneria")
    assert "VINCOLO GEOGRAFICO NON NEGOZIABILE" in web.prompt
    assert "Umbria" in web.prompt
    assert "studi di ingegneria" in web.prompt
    # il vincolo va anche al passo di strutturazione, non solo alla ricerca
    assert "Umbria" in struct.prompt


def test_un_prospect_fuori_zona_viene_squalificato():
    """Il modello a volte ignora il vincolo: secondo controllo sul booleano `in_zona`.
    NON su sottostringa: «Perugia (PG)» è in Umbria senza contenere la parola, e un
    confronto di testo scarterebbe proprio le aziende giuste."""
    pros, _w, _s = _prospector([_p("Roma Srl", "Roma (RM)", in_zona=False),
                                _p("Alfa", "Perugia (PG)")])
    out = pros.find(2, zona="Umbria")
    fuori = {p["company"]: p for p in out}
    assert fuori["Roma Srl"]["in_target"] is False
    assert "fuori dalla zona" in fuori["Roma Srl"]["fit_reason"]
    assert fuori["Alfa"]["in_target"] is True     # Perugia resta


def test_una_citta_umbra_non_viene_scartata_per_il_nome():
    """Regressione del filtro a sottostringa: Perugia, Terni e Foligno sono in Umbria."""
    pros, _w, _s = _prospector([_p("Alfa", "Perugia (PG)"), _p("Beta", "Terni (TR)"),
                                _p("Gamma", "Foligno (PG)")])
    out = pros.find(3, zona="Umbria")
    assert all(p["in_target"] for p in out)


def test_zona_mancante_nel_risultato_non_squalifica():
    """Un falso negativo qui costa un cliente: se il campo manca, non si scarta."""
    senza = _p("Delta", "Spoleto")
    del senza["in_zona"]
    pros, _w, _s = _prospector([senza])
    assert pros.find(1, zona="Umbria")[0]["in_target"] is True


def test_senza_zona_nessun_filtro():
    pros, web, _s = _prospector([_p("Alfa", "Milano")])
    out = pros.find(1)
    assert "VINCOLO GEOGRAFICO" not in web.prompt
    assert out[0]["in_target"] is True


# ---- cosa fanno e come si contattano ----
def test_il_prompt_pretende_attivita_e_contatto_raggiungibile():
    pros, web, _s = _prospector([_p("Alfa", "Terni")])
    pros.find(2, zona="Umbria")
    assert "UNA RIGA su cosa fa" in web.prompt
    assert "«Contatto via form web» NON è un contatto" in web.prompt
    assert "Non inventare aziende" in web.prompt


def test_la_riga_salvata_porta_attivita_sede_e_telefono():
    """Prima nel DB restava solo un nome: `marketing_prospects` non ha colonne per
    attività, sede e telefono, quindi vanno nel campo che l'owner legge."""
    riga = Prospector.to_row(_p("Alfa", "Foligno (PG)",
                                attivita="produce macchine per l'agroalimentare"))
    assert "macchine per l'agroalimentare" in riga["fit_reason"]
    assert "Foligno" in riga["fit_reason"]
    assert "075 1234567" in riga["fit_reason"]
    assert riga["contact_email"] == "info@x.it"
    # solo colonne che esistono davvero in marketing_prospects
    assert "contact_phone" not in riga and "attivita" not in riga and "zona" not in riga


def test_schema_richiede_attivita_e_zona():
    from aios.prospecting import _SCHEMA
    obbligatori = _SCHEMA["properties"]["prospects"]["items"]["required"]
    assert "attivita" in obbligatori and "zona" in obbligatori


# ---- il tool in chat ----
def test_il_tool_dice_di_usarlo_al_posto_della_memoria():
    d = _CERCA_CLIENTI_DEF["description"]
    assert "CERCA SUL WEB" in d
    assert "a memoria" in d          # spiega perché esiste
    for campo in ("zona", "settori", "esclusioni", "quanti"):
        assert campo in _CERCA_CLIENTI_DEF["input_schema"]["properties"]


def _orch_con_prospector(prospects):
    """Orchestratore minimo con un Prospector finto attaccato alla platform."""
    from types import SimpleNamespace

    from aios.chat_runner import ChatOrchestrator
    from aios.kernel import Kernel

    class ClientFinto:
        def __init__(self):
            self.scritture = []

        def insert(self, table, row):
            self.scritture.append((table, row))
            return [row]

    k = Kernel()
    client = ClientFinto()
    k._supabase = client
    pros, _w, _s = _prospector(prospects)
    platform = SimpleNamespace(kernel=k, agents={}, commands=None, chat=None,
                               prospector=pros)
    return ChatOrchestrator(platform, None, None, skills=None), client


def test_qualunque_reparto_puo_cercare():
    """Prima il tool era solo di marketing e vendite: una domanda instradata a legal
    («dammi 2 aziende in Umbria da contattare») restava senza strumenti e l'agente
    rispondeva «non ci riesco». Instradare meglio aiuta, ma è un elenco di parole
    chiave: il buco si chiude dando la ricerca a tutti."""
    from aios.chat_runner import ChatAgent
    orch, _c = _orch_con_prospector([_p("Alfa", "Perugia (PG)")])
    for dominio in ("marketing", "vendite", "legal", "finance", "hr", "operations"):
        nomi = [t["name"] for t in ChatAgent(orch, dominio, None)._tool_defs()]
        assert "cerca_clienti" in nomi, dominio


def test_senza_prospector_il_tool_non_c_e():
    from types import SimpleNamespace

    from aios.chat_runner import ChatAgent, ChatOrchestrator
    from aios.kernel import Kernel
    platform = SimpleNamespace(kernel=Kernel(), agents={}, commands=None, chat=None,
                               prospector=None)
    orch = ChatOrchestrator(platform, None, None, skills=None)
    assert "cerca_clienti" not in [t["name"]
                                   for t in ChatAgent(orch, "vendite", None)._tool_defs()]


def test_la_scheda_prospect_la_scrivono_solo_i_commerciali():
    """Allargare la ricerca non deve allargare il perimetro di SCRITTURA di nessuno."""
    from aios.chat_runner import ChatAgent
    orch, client = _orch_con_prospector([_p("Alfa", "Perugia (PG)")])

    res = ChatAgent(orch, "legal", None)._exec_tool("cerca_clienti", {"zona": "Umbria"})
    assert res["trovati"] == 1 and res["salvati"] == 0
    assert client.scritture == []                        # niente riga scritta da legal
    assert "Marketing e Vendite" in res["nota"]          # e lo dice all'owner

    res = ChatAgent(orch, "vendite", None)._exec_tool("cerca_clienti", {"zona": "Umbria"})
    assert res["salvati"] == 1
    assert client.scritture and client.scritture[0][0] == "marketing_prospects"


def test_i_reparti_che_possono_salvare_sono_due():
    from aios.chat_runner import _DOMINI_PROSPECT
    assert _DOMINI_PROSPECT == {"marketing", "vendite"}
