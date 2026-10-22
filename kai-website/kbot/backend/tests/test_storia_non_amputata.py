"""Causa dei troncamenti del 22/10/2026 (test 09-11): la STORIA mandata al modello tagliava anche le risposte del bot a 900
caratteri + «…». Il modello vedeva le proprie risposte finire a metà frase e al turno dopo le chiudeva allo stesso modo
(risposte di 890-1.500 car. con «…» finale salvate in prod); e `taglio_guard` considerava «…» una fine valida."""
from app.lib import taglio_guard as T
from app.lib.prompts import compact_messages

LUNGA = ("Qui la situazione cambia: la detrazione nasce quando l'imposta diventa esigibile. " * 40).strip()   # ~3.200 car.


def _storia(n_turni=3):
    out = []
    for i in range(n_turni):
        out.append({"role": "user", "content": f"domanda {i}"})
        out.append({"role": "assistant", "content": LUNGA + f" Fine della risposta {i}."})
    out.append({"role": "user", "content": "e adesso?"})
    return out


def test_le_ultime_risposte_del_bot_arrivano_intere():
    h = compact_messages(_storia(), 12, 900)
    assist = [m["content"] for m in h if m["role"] == "assistant"]
    assert assist[-1].endswith("Fine della risposta 2.")
    assert assist[-2].endswith("Fine della risposta 1.")


def test_nessuna_risposta_del_bot_finisce_con_ellissi():
    h = compact_messages(_storia(6), 12, 900)
    for m in h:
        if m["role"] == "assistant":
            assert not m["content"].rstrip().endswith(("…", "..."))
            assert m["content"].rstrip()[-1] in ".?!:)"          # taglio solo a fine frase


def test_le_risposte_vecchie_restano_compatte():
    h = compact_messages(_storia(6), 12, 900)
    vecchie = [m["content"] for m in h if m["role"] == "assistant"][:-2]
    assert vecchie and all(len(c) <= 2600 for c in vecchie)


def test_i_messaggi_dell_utente_restano_al_tetto():
    h = compact_messages([{"role": "user", "content": "x " * 1000}, {"role": "assistant", "content": "ok."},
                          {"role": "user", "content": "ciao"}], 12, 900)
    assert len(h[0]["content"]) <= 900


def test_taglio_guard_non_prende_l_ellissi_per_una_fine():
    base = "Questa risposta è abbastanza lunga da superare la soglia minima di caratteri del controllo. " * 3
    assert T.e_troncata(base + "La detrazione dell'IVA…")
    assert T.e_troncata(base + "\n3. La detrazione dell'IVA…")           # anche in un elenco
    assert T.e_troncata(base + "La detrazione dell'IVA...")
    assert not T.e_troncata(base + "Ti conviene farlo subito.")
