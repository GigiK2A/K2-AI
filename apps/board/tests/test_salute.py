"""Autodiagnosi: il board conta i propri errori invece di farseli contare da fuori.

Il censimento del 20 ago 2026 lo faceva una routine esterna. Sono letture delle
proprie tabelle: `aios_audit`, `aios_approvals`, `email_messages`,
`aios_deliverables`. Qui si verifica che i numeri escano giusti e che il referto
dica solo le cause che si RIPETONO — una che appare una volta è un caso, una che
torna è un difetto.
"""
from datetime import datetime, timedelta, timezone

from aios import salute


def _iso(giorni_fa=0):
    return (datetime.now(timezone.utc) - timedelta(days=giorni_fa)).isoformat()


class Client:
    """Supabase finto: restituisce per tabella e registra le query fatte."""

    def __init__(self, **tabelle):
        self.t = tabelle
        self.query = []
        self.scritture = []

    def select(self, table, params):
        self.query.append((table, dict(params)))
        return list(self.t.get(table, []))

    def insert(self, table, row):
        self.scritture.append(("insert", table))
        return [row]

    def update(self, table, filters, patch):
        self.scritture.append(("update", table))
        return [patch]


def _ripiego(tabella, causa, titolo="t"):
    return {"event": "ripiegata", "actor": "vendite_agent", "action_key": "vendite.azione",
            "created_at": _iso(), "detail": {"titolo": titolo, "tabella_voluta": tabella,
                                             "causa": causa}}


def _fallita(errore):
    return {"event": "failed", "actor": "legal_agent", "action_key": "legal.azione",
            "created_at": _iso(), "detail": {"esito": {"ok": False, "errore": errore}}}


def _eseguita():
    return {"event": "executed", "actor": "vendite_agent", "action_key": "vendite.azione",
            "created_at": _iso(), "detail": {"esito": {"ok": True, "tabella": "board_tasks"}}}


# ---- non deve scrivere niente, mai ----
def test_autodiagnosi_e_sola_lettura():
    c = Client(aios_audit=[_eseguita(), _ripiego("enablement", "tabella non in allowlist")])
    salute.esamina(c)
    assert c.scritture == []


def test_legge_solo_le_proprie_tabelle():
    c = Client(aios_audit=[_eseguita()])
    salute.esamina(c)
    lette = {t for t, _ in c.query}
    assert lette <= {"aios_audit", "aios_approvals", "email_messages", "aios_deliverables"}


def test_client_assente_non_solleva():
    assert salute.esamina(None) == {}
    assert salute.referto({}) == ""


def test_supabase_giu_non_ferma_il_loop():
    class Rotto:
        def select(self, table, params):
            raise RuntimeError("supabase giù")

    dati = salute.esamina(Rotto())
    assert dati["eventi"] == {}          # niente numeri, ma nessuna eccezione
    assert dati["pendenti"] == 0


# ---- i numeri ----
def test_conta_gli_eventi_per_tipo():
    c = Client(aios_audit=[_eseguita(), _eseguita(),
                           _ripiego("enablement", "tabella non in allowlist: enablement"),
                           _fallita("nessuna riga corrisponde al match")])
    d = salute.esamina(c)
    assert d["eventi"] == {"executed": 2, "ripiegata": 1, "failed": 1}


def test_raggruppa_i_ripieghi_per_tabella_voluta():
    # È il punto del modulo: cinque ripieghi sulla stessa tabella sono UN difetto.
    c = Client(aios_audit=[_ripiego("enablement", "tabella non in allowlist: enablement")] * 5)
    d = salute.esamina(c)
    voci = d["cause"]["ripiegata"]
    assert len(voci) == 1
    causa, n = voci[0]
    assert n == 5 and "enablement" in causa


def test_eta_del_lavoro_fermo():
    c = Client(
        aios_approvals=[{"id": 1, "actor": "hr_agent", "created_at": _iso(giorni_fa=4)},
                        {"id": 2, "actor": "hr_agent", "created_at": _iso()}],
        email_messages=[{"id": "m1", "created_at": _iso(giorni_fa=38)}])
    d = salute.esamina(c)
    assert d["pendenti"] == 2
    assert d["pendenti_eta_giorni"] == 4        # la più vecchia, non la media
    assert d["bozze"] == 1 and d["bozze_eta_giorni"] == 38
    assert d["pendenti_per_reparto"] == [("hr_agent", 2)]


def test_data_illeggibile_non_solleva():
    c = Client(aios_approvals=[{"id": 1, "actor": "x", "created_at": "non-una-data"}])
    assert salute.esamina(c)["pendenti_eta_giorni"] is None


# ---- qualità ----
def test_qualita_misura_le_tre_cose_richieste():
    q = salute.qualita([
        {"motivo": "Pipeline a 0 lead su 20 di target. Alternativa scartata: attendere "
                   "inbound. Cambierebbe idea se ci fosse un dataset già arricchito."},
        {"motivo": "Va fatto perché è importante."},
    ])
    assert q == {"proposte": 2, "numeri": 50, "alternativa": 50, "ripensamento": 50}


def test_qualita_su_zero_proposte_non_divide_per_zero():
    assert salute.qualita([])["proposte"] == 0


# ---- il referto ----
def test_referto_dice_solo_le_cause_che_si_ripetono():
    c = Client(aios_audit=[_ripiego("enablement", "tabella non in allowlist: enablement"),
                           _ripiego("enablement", "tabella non in allowlist: enablement"),
                           _ripiego("analytics", "tabella non in allowlist: analytics")])
    testo = salute.referto(salute.esamina(c))
    assert "2× enablement" in testo      # si ripete → è un difetto
    assert "analytics" not in testo      # una volta sola → è un caso


def test_referto_riporta_il_lavoro_fermo_con_l_eta():
    c = Client(aios_approvals=[{"id": 1, "actor": "legal_agent",
                                "created_at": _iso(giorni_fa=3)}],
               email_messages=[{"id": "m", "created_at": _iso(giorni_fa=38)}])
    testo = salute.referto(salute.esamina(c))
    assert "Fermo in attesa di te" in testo
    assert "1 decisione in attesa" in testo and "da 3 giorni" in testo
    assert "1 bozza email mai inviata" in testo and "da 38 giorni" in testo


def test_referto_distingue_eseguite_da_ripiegate():
    c = Client(aios_audit=[_eseguita(), _eseguita(),
                           _ripiego("x", "y"), _ripiego("x", "y")])
    testo = salute.referto(salute.esamina(c))
    assert "2 azioni eseguite" in testo
    assert "2 ripiegate a task" in testo


def test_referto_include_la_qualita():
    c = Client(aios_deliverables=[
        {"motivo": "3 lead su 20. Alternativa scartata: aspettare. "
                   "Cambierebbe idea se arrivasse inbound.", "created_at": _iso()}])
    testo = salute.referto(salute.esamina(c))
    assert "numeri 100%" in testo
    assert "alternativa scartata 100%" in testo
    assert "cosa cambierebbe idea 100%" in testo


def test_giornata_pulita_non_manda_un_referto_inutile():
    # Niente insuccessi, niente fermo, niente proposte: solo la riga di intestazione,
    # nessuna sezione. Un referto quotidiano che nessuno legge non serve a nulla.
    testo = salute.referto(salute.esamina(Client(aios_audit=[_eseguita()])))
    assert "1 azione eseguita" in testo
    assert "Fermo in attesa di te" not in testo
    assert "Qualità" not in testo


# ---- l'aggancio nel loop ----

class _Kernel:
    def __init__(self, client):
        self._supabase = client


class _Platform:
    def __init__(self, client):
        self.kernel = _Kernel(client)


def test_il_loop_manda_il_referto_su_telegram(monkeypatch):
    import autonomy_loop
    from aios.notify import telegram
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "t")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "42")
    mandate = []
    monkeypatch.setattr(telegram, "_post",
                        lambda m, p, timeout=35: mandate.append(p) or {})
    c = Client(aios_audit=[_eseguita(),
                           _ripiego("enablement", "tabella non in allowlist: enablement"),
                           _ripiego("enablement", "tabella non in allowlist: enablement")])
    dati = autonomy_loop._autodiagnosi(_Platform(c))
    assert dati["eventi"]["executed"] == 1
    testo = " ".join(str(m.get("text")) for m in mandate)
    assert "Salute del board" in testo and "2× enablement" in testo


def test_senza_supabase_il_loop_non_si_ferma():
    import autonomy_loop
    assert autonomy_loop._autodiagnosi(_Platform(None)) == {}


def test_singolare_e_plurale_corretti():
    # È un messaggio che l'owner legge ogni mattina: «1 decisioni da 1 giorni» no.
    c = Client(aios_approvals=[{"id": 1, "actor": "x", "created_at": _iso(giorni_fa=1)}])
    testo = salute.referto(salute.esamina(c))
    assert "1 decisione in attesa, la più vecchia da 1 giorno" in testo
    assert "giorni" not in testo
