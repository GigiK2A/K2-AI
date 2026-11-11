"""La procedura di privatizzazione dei bucket (scripts/verifica_bucket.py) provata su un finto Storage: prima/dopo, pulizia, rifiuti."""
import os
import re
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import verifica_bucket as VB  # noqa: E402

BASE = "https://prog.supabase.co"


class Storage:
    def __init__(self, pubblici):
        self.files, self.pubblici, self.cancellati = {}, set(pubblici), []

    def from_(self, b):
        s = self

        class B:
            def upload(self, path, data, opts=None): s.files[(b, path)] = data
            def create_signed_url(self, path, n): return {"signedURL": f"/storage/v1/object/sign/{b}/{path}?token=t{n}"}
            def download(self, path): return s.files[(b, path)]
            def remove(self, paths):
                for p in paths:
                    s.files.pop((b, p), None); s.cancellati.append((b, p))
        return B()


class Client:
    def __init__(self, pubblici): self.storage = Storage(pubblici)


def http(client):
    def get(url):
        m = re.match(r"^https://prog\.supabase\.co/storage/v1/object/(public|sign)/([^/]+)/(.+?)(\?.*)?$", url)
        if not m:
            return 0, b""
        tipo, b, path = m.group(1), m.group(2), m.group(3)
        if (b, path) not in client.storage.files:
            return 404, b""
        if tipo == "public" and b not in client.storage.pubblici:
            return 400, b""
        return 200, client.storage.files[(b, path)]
    return get


@pytest.fixture
def rinfresca(monkeypatch):
    from app.lib import storage
    monkeypatch.setattr(storage, "SUPABASE_URL", BASE)
    return storage.rinfresca_url


def prova(pubblici, rinfresca_fn, monkeypatch, fase, anon=None, anon_voci=0):
    from app.lib import storage
    c = Client(pubblici)
    monkeypatch.setattr(storage, "get_admin_client", lambda: c)
    ris = VB.raccogli(c, BASE, http(c), rinfresca_fn, anon_key=anon, http_list=(lambda b, k: anon_voci) if anon is not None else None)
    return c, VB.valuta(fase, ris)


def test_prima_i_bucket_pubblici_sono_esposti_e_la_prova_lo_documenta(monkeypatch, rinfresca):
    c, righe = prova({"kbot-uploads", "kbot-reports"}, rinfresca, monkeypatch, "prima")
    assert all(ok for *_, ok in righe), righe                                     # stato attuale: link pubblico = 200
    assert len(c.storage.cancellati) == 2 and not c.storage.files                  # ha ripulito tutto, e solo i propri file


def test_dopo_la_privatizzazione_il_link_pubblico_e_chiuso_ma_i_vecchi_link_funzionano(monkeypatch, rinfresca):
    c, righe = prova(set(), rinfresca, monkeypatch, "dopo")
    assert all(ok for *_, ok in righe), righe
    # la stessa corsa, valutata come «dopo», NON passa se i bucket sono ancora pubblici
    _, righe2 = prova({"kbot-uploads", "kbot-reports"}, rinfresca, monkeypatch, "dopo")
    assert not all(ok for *_, ok in righe2)
    assert [r for r in righe2 if not r[4]][0][1] == "lettura anonima del link PUBBLICO"


def test_se_la_rinfresca_non_funziona_la_prova_lo_vede(monkeypatch):
    _, righe = prova(set(), lambda u: u, monkeypatch, "dopo")                      # una rinfresca che non cambia nulla
    assert any((not ok) and "rinfresca" in controllo for (_, controllo, _, _, ok) in righe)


def test_percorsi_creati_solo_sotto_test31_e_pulizia_anche_in_errore(monkeypatch, rinfresca):
    c = Client(set())
    orig = c.storage.from_

    def from_(b):
        o = orig(b)
        vecchio = o.create_signed_url

        def boom(path, n): raise RuntimeError("errore simulato")
        o.create_signed_url = boom
        return o
    c.storage.from_ = from_
    with pytest.raises(RuntimeError):
        VB.raccogli(c, BASE, http(c), rinfresca)
    assert not c.storage.files and all(p.startswith("test31/") for _, p in c.storage.cancellati)


def test_senza_esegui_non_scrive_rifiuta_l_ambiente_sbagliato_e_non_stampa_le_chiavi(monkeypatch, capsys):
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "SEGRETO-CHIAVE-123")
    monkeypatch.setenv("SUPABASE_URL", "https://altro-progetto.supabase.co")
    assert VB.main(["--fase", "prima", "--progetto", "uiuvwzrmrdqbfajguuab"]) == 2                    # progetto diverso: rifiuto
    monkeypatch.setenv("SUPABASE_URL", "https://uiuvwzrmrdqbfajguuab.supabase.co")
    assert VB.main(["--fase", "prima", "--progetto", "uiuvwzrmrdqbfajguuab"]) == 0                    # senza --esegui: solo il piano
    cat = capsys.readouterr()
    assert "nessuna scrittura" in cat.out and "SEGRETO-CHIAVE-123" not in cat.out + cat.err


def test_l_elenco_con_la_chiave_anon_si_giudica_dal_numero_di_voci_non_dal_codice(monkeypatch, rinfresca):
    _, righe = prova(set(), rinfresca, monkeypatch, "dopo", anon="chiave-anon", anon_voci=0)         # 200 con elenco vuoto: chiuso
    assert all(ok for *_, ok in righe)
    _, righe = prova(set(), rinfresca, monkeypatch, "dopo", anon="chiave-anon", anon_voci=3)         # la chiave anon vede file: ESPOSTO
    assert [r[1] for r in righe if not r[4]] == ["elenco del bucket con la chiave anon (voci visibili)"] * 2


def test_filtro_bucket_e_controllo_cache(monkeypatch, rinfresca):
    from app.lib import storage
    c = Client({"kbot-uploads", "kbot-reports"})
    monkeypatch.setattr(storage, "get_admin_client", lambda: c)
    ris = VB.raccogli(c, BASE, http(c), rinfresca, buckets=("kbot-reports",))
    assert list(ris) == ["kbot-reports"] and not c.storage.files                                 # solo il bucket richiesto, ripulito
    urls = VB.prepara_cache(c, BASE, http(c), buckets=("kbot-uploads",))
    assert len(urls) == 1 and "/object/public/kbot-uploads/test31/cache-" in urls[0] and not c.storage.files       # l'URL è salvato, il file è già cancellato
    # file cancellato ma «ancora in cache»: simulato da un http_get che risponde 200 → il controllo lo segnala
    assert VB.controlla_cache(urls, lambda u: (200, b"")) == [(urls[0], 200, False)]
    assert VB.controlla_cache(urls, lambda u: (400, b"")) == [(urls[0], 400, True)]
