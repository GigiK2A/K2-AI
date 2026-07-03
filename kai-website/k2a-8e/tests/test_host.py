"""HostBoost KPI deterministici — no placeholder '1' in un report pagato."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import host  # noqa: E402

ok = True


def check(label, cond):
    global ok
    ok = ok and bool(cond)
    print(f"  {'OK ' if cond else 'FAIL'} {label}")


def approx(a, b, tol=0.5):
    return a is not None and abs(float(a) - float(b)) <= tol


_PLACEHOLDER = {"adr": 1, "occupancy": 1, "revpar": 1, "trevpar": 1, "goppar": 1, "alos": 1,
                "booking_window_medio_giorni": 1, "cancellation_rate": 1,
                "yoy_revpar": 1, "yoy_adr": 1, "yoy_occupancy": 1}


def _deliv():
    return {"meta": {"versione": "1.0.0"}, "kpi": {"annuale": dict(_PLACEHOLDER), "mensile": []}}


print("── apply_hostboost: KPI calcolati dai dati dichiarati (no LLM, no '1') ──")
# B&B «confusionario»: ADR 95, occ 62%, 9 camere, ricavi 180k, costi 110k
form = {"camere_totali": 9, "giorni_apertura": 365,
        "kpi_attuali": {"adr_eur": 95, "occupancy_pct": 62}, "ricavi": 180000, "costi": 110000}
out, meta = host.apply_hostboost(_deliv(), form)
ann = out["kpi"]["annuale"]
check("ADR ≈ 95 (dichiarato, non 1)", approx(ann["adr"], 95))
check("occupancy = 0,62 FRAZIONE 0-1 (schema max:1), non 62 né 1", approx(ann["occupancy"], 0.62, tol=0.02))
check("RevPAR = ADR × occ = 58,9 (derivato, non 1)", approx(ann["revpar"], 58.9))
check("GOPPAR calcolato dai ricavi/costi (via metriche_hospitality)", ann.get("goppar") is not None and ann["goppar"] > 0)
check("fonte = metriche_hospitality", meta["hostboost_kpi_fonte"] == "metriche_hospitality")
check("KPI non conoscibili (yoy/alos) azzerati a null, NON 1",
      ann["yoy_revpar"] is None and ann["alos"] is None and ann["cancellation_rate"] is None)

print("── via minima: solo ADR+occ dichiarati → RevPAR derivato, resto null ──")
out2, meta2 = host.apply_hostboost(_deliv(), {"kpi_attuali": {"adr_eur": 120, "occupancy_pct": 50}})
ann2 = out2["kpi"]["annuale"]
check("ADR 120 passthrough / occ 0,50 frazione", approx(ann2["adr"], 120) and approx(ann2["occupancy"], 0.50, tol=0.02))
check("RevPAR = 60 (120×0,50)", approx(ann2["revpar"], 60))
check("GOPPAR null (niente ricavi/costi → non inventato)", ann2["goppar"] is None)

print("── kpi.mensile placeholder (12×'1') → svuotato + assunzione (no 12 mesi finti) ──")
d_men = _deliv()
d_men["kpi"]["mensile"] = [{"mese": f"2024-{m:02d}", "notti_disponibili": 1, "notti_vendute": 1,
                            "ricavi_camera": 1, "adr": 1, "occupancy": 1, "revpar": 1,
                            "fascia_stagionale": "bassa"} for m in range(1, 13)]
out_m, meta_m = host.apply_hostboost(d_men, form)
check("mensile placeholder svuotato → []", out_m["kpi"]["mensile"] == [])
check("assunzione onesta aggiunta (come ottenere il dettaglio mensile)",
      any("mensile" in a.lower() for a in out_m.get("assunzioni", [])))
# mensile REALE (non placeholder) NON va svuotato
d_real = _deliv()
d_real["kpi"]["mensile"] = [{"mese": "2024-07", "notti_disponibili": 279, "notti_vendute": 250,
                             "ricavi_camera": 30000, "adr": 120, "occupancy": 0.9, "revpar": 108,
                             "fascia_stagionale": "alta"}]
out_r, _ = host.apply_hostboost(d_real, form)
check("mensile REALE conservato (non svuotato)", len(out_r["kpi"]["mensile"]) == 1)

print("── nessun dato KPI → tutto null (mai il placeholder '1') ──")
out3, meta3 = host.apply_hostboost(_deliv(), {"nome": "B&B", "tipologia": "bb"})
ann3 = out3["kpi"]["annuale"]
check("adr/occupancy/revpar = None (onesto, non 1)",
      ann3["adr"] is None and ann3["occupancy"] is None and ann3["revpar"] is None)
check("fonte = nessun_dato", meta3["hostboost_kpi_fonte"] == "nessun_dato")
check("NESSUN valore residuo = 1 in tutta kpi.annuale", not any(v == 1 for v in ann3.values()))

print("\nTEST HOST " + ("PASS ✅" if ok else "FAIL ❌"))
sys.exit(0 if ok else 1)
