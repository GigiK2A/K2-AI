"""La cartella clienti deve essere raggiungibile da chi la usa.

Il metodo scritto in una skill che nessuno apre non serve a niente, e un aggiornamento
automatico che non gira nel loop non è automatico. Questi test tengono ferme le tre
connessioni: la skill è nella biblioteca di Vendite, il quadro è un sensore, e il
motore che muove gli stati è cablato nel loop.
"""
import re
from pathlib import Path


def test_la_cartella_esiste_nella_biblioteca():
    from aios.skills import SkillLibrary
    s = SkillLibrary()
    assert "pipeline-clienti-stati" in s.names()
    testo = s.load("pipeline-clienti-stati")
    assert len(testo) > 1500


def test_e_una_skill_di_vendite():
    from aios.skills import SkillLibrary
    s = SkillLibrary()
    assert "pipeline-clienti-stati" in s.for_domain("vendite", 120)
    # e viene scelta come metodo quando la richiesta è quella
    assert "pipeline-clienti-stati" in s.pick_for(
        "vendite", "aggiorna lo stato dei clienti nella tabella", 2)


def test_e_prima_fra_quelle_curate_del_reparto():
    """`skill_focus` è la lista curata a mano: la prima è quella che l'agente vede
    sempre, prima di qualsiasi instradamento automatico."""
    from aios.agents.sales_config import SALES_CONFIG
    assert SALES_CONFIG.skill_focus[0] == "pipeline-clienti-stati"


def test_la_skill_elenca_tutti_gli_stati_del_codice():
    """Se il codice aggiunge uno stato e la cartella non lo dice, l'agente lavora su un
    contratto vecchio."""
    from aios.pipeline_clienti import STATI
    from aios.skills import SkillLibrary
    testo = SkillLibrary().load("pipeline-clienti-stati")
    for s in STATI:
        assert f"`{s}`" in testo, s


def test_la_skill_dice_quali_stati_sono_automatici():
    from aios.skills import SkillLibrary
    testo = SkillLibrary().load("pipeline-clienti-stati")
    assert "Cosa succede da solo" in testo
    assert "last_contact_at" in testo
    # e ripete i due vincoli che costano soldi se ignorati
    assert "Un contatto non si inventa" in testo
    assert "da 1 a 10" in testo


def test_il_sensore_e_nei_sensori_di_vendite():
    """Registrarlo nel kernel non basta: l'agente vede solo i sensori del suo config.
    Provato in produzione il 21 ago: il sensore c'era ma Vendite non lo chiamava,
    perché per lui non esisteva."""
    from aios.agents.sales_config import SALES_CONFIG
    nomi = [t for t, _a in SALES_CONFIG.sensors]
    assert nomi[0] == "leggi_tabella_clienti"     # primo: è il quadro d'insieme


def test_il_sensore_si_spiega_da_solo():
    """Senza descrizione un sensore si chiama «Sensore di reparto: nome» e il modello
    preferisce quelli che capisce — infatti aveva usato leggi_lead e leggi_clienti."""
    from aios.chat_runner import _SENSOR_DESC
    d = _SENSOR_DESC["leggi_tabella_clienti"]
    assert "pipeline_leads" in d and "conteggio per stato" in d
    assert "pipeline-clienti-stati" in d          # rimanda al metodo


def test_il_quadro_e_un_sensore_di_sola_lettura_del_reparto():
    """Registrato dalla fabbrica di Vendite — dichiararlo nel config e registrarlo in
    build_platform lo rendeva invisibile all'agente, e un test preesistente lo ha preso."""
    from aios.sources.sales import lead_tools

    class C:
        def select(self, tab, params):
            return [{"name": "Alfa", "status": "nuovo"}]

    t = {x.name: x for x in lead_tools(C())}["leggi_tabella_clienti"]
    assert t.readonly is True and t.action_type is None
    assert t.run()["per_stato"] == {"nuovo": 1}


def test_l_aggiornamento_dalla_posta_gira_nel_loop():
    """Un aggiornamento automatico che nessuno chiama non è automatico: era il difetto
    della ricerca clienti, che esisteva ma partiva solo da un bottone."""
    righe = Path("autonomy_loop.py").read_text(encoding="utf-8").splitlines()
    assert any("from aios import pipeline_clienti" in r for r in righe)
    chiamata = [r for r in righe if "pipeline_clienti.aggiorna_da_email" in r]
    assert chiamata, "il motore non è chiamato da nessuna parte"
    # Deve girare a OGNI giro, non dentro un blocco «una volta al giorno»: la profondità
    # è quella del corpo del while (8) più il try (4). Più rientro = è annidato in un if.
    rientro = len(chiamata[0]) - len(chiamata[0].lstrip())
    assert rientro == 12, f"rientro {rientro}: sembra annidato in un blocco condizionale"


def test_gli_stati_del_codice_sono_quelli_accettati_dal_db():
    """Verificati uno per uno su pipeline_leads il 21 ago 2026: `status` è testo libero,
    quindi il contratto vive qui e non nello schema."""
    from aios.pipeline_clienti import STATI
    assert len(set(STATI)) == len(STATI)
    for s in STATI:
        assert re.fullmatch(r"[a-z_]+", s), s
