"""Statistiche del banco di prova: una differenza fra due esecuzioni va letta solo se supera la
variazione del modello. Dati sintetici, nessuna rete."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "evals"))

import statistiche as S  # noqa: E402


def _r(caso, rep, spec_ok, spec_tot=3, gen_ok=7, gen_tot=7):
    """Un risultato sintetico: `spec_ok` dei `spec_tot` controlli specifici superati."""
    spec = {f"c{i}": (i < spec_ok, "") for i in range(spec_tot)}
    gen = {f"g{i}": (i < gen_ok, "") for i in range(gen_tot)}
    return {"id": caso, "ripetizione": rep, "esito": {"generici": gen, "specifici": spec}}


def _file(risultati, modello="m"):
    return {"meta": {"modello": modello, "data": "2026-10-15T00:00:00"}, "risultati": risultati}


def test_i_file_senza_il_campo_ripetizione_contano_come_una():
    rr = [{"id": "a", "esito": {"generici": {"g": (True, "")}, "specifici": {"s": (False, "")}}}]
    t = S.totali_per_ripetizione(rr)
    assert len(t) == 1 and t[0]["ripetizione"] == 1 and t[0]["specifici_ok"] == 0


def test_totali_per_ripetizione():
    rr = [_r("a", 1, 3), _r("b", 1, 1), _r("a", 2, 2), _r("b", 2, 1)]
    t = S.totali_per_ripetizione(rr)
    assert [x["specifici_ok"] for x in t] == [4, 3]
    assert [x["casi_tutte_attese"] for x in t] == [1, 0]
    assert all(x["casi"] == 2 for x in t)


def test_media_e_deviazione():
    m, sd = S.media_sd([4, 3, 5])
    assert m == 4 and round(sd, 2) == 1.0
    assert S.media_sd([4]) == (4, None)
    assert S.media_sd([]) == (0.0, None)


def test_controlli_instabili_sono_quelli_che_cambiano_fra_ripetizioni():
    # stesso caso: nella prima ripetizione 3/3, nella seconda 1/3 → c1 e c2 instabili, c0 stabile
    rr = [_r("contanti", 1, 3), _r("contanti", 2, 1), _r("dvr", 1, 3), _r("dvr", 2, 3)]
    inst = S.instabili(rr)
    assert {(i["caso"], i["controllo"]) for i in inst} == {("contanti", "specifici.c1"), ("contanti", "specifici.c2")}
    assert all(i["ok"] == 1 and i["su"] == 2 for i in inst)


def test_una_sola_ripetizione_non_da_un_verdetto():
    a = _file([_r("a", 1, 1)])
    b = _file([_r("a", 1, 3)])
    righe = {r["metrica"]: r for r in S.confronta(a, b)}
    assert righe["specifici_ok"]["delta"] == 2
    assert "non misurabile" in righe["specifici_ok"]["giudizio"]


def test_differenza_entro_la_variazione_e_rumore():
    # A: 24, 27, 21 (sd 3) — B: 26, 24, 28: Δ media = +1, ben dentro 2·sd
    a = _file([_r("x", 1, 3), _r("y", 1, 3), _r("x", 2, 3), _r("y", 2, 2), _r("x", 3, 1), _r("y", 3, 1)])
    b = _file([_r("x", 1, 3), _r("y", 1, 3), _r("x", 2, 3), _r("y", 2, 1), _r("x", 3, 2), _r("y", 3, 2)])
    g = {r["metrica"]: r for r in S.confronta(a, b)}["specifici_ok"]["giudizio"]
    assert "entro la variazione" in g


def test_differenza_oltre_la_variazione_e_reale():
    # A stabile attorno a 2 (sd ~0), B stabile attorno a 6: salto netto
    a = _file([_r("x", k, 1) for k in (1, 2, 3)] + [_r("y", k, 1) for k in (1, 2, 3)])
    b = _file([_r("x", k, 3) for k in (1, 2, 3)] + [_r("y", k, 3) for k in (1, 2, 3)])
    righe = {r["metrica"]: r for r in S.confronta(a, b)}
    assert righe["specifici_ok"]["delta"] == 4
    assert "oltre la variazione" in righe["specifici_ok"]["giudizio"]


def test_nessuna_differenza():
    a = _file([_r("x", 1, 2), _r("x", 2, 2)])
    assert {r["metrica"]: r for r in S.confronta(a, a)}["specifici_ok"]["giudizio"] == "nessuna differenza"


def test_tassi_per_controllo():
    rr = [_r("a", 1, 3), _r("a", 2, 1)]
    assert S.tassi_per_controllo(rr)["specifici.c2"] == (1, 2)


def test_formattazione_non_esplode_e_nomina_gli_instabili():
    a = _file([_r("contanti", 1, 3), _r("contanti", 2, 1)], "modello A")
    out = S.formatta_confronto(S.confronta(a, a), a, a)
    assert "modello A" in out and "contanti" in out and "instabili" in out
