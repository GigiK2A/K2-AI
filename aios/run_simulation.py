"""Run the Marketing 'multiverse' simulation (model-based, compressed time).
Prints the andamento over N days for several scenarios. No real channels touched.
Run: cd aios && .venv/bin/python run_simulation.py
"""
from aios.sim.engine import run_simulation


def _bar(v, vmax, width=24):
    n = 0 if vmax <= 0 else round(width * v / vmax)
    return "█" * n


def show(res):
    tl = res["timeline"]
    fmax = max(r["followers"] for r in tl)
    print(f"\n=== scenario seed={res['seed']} — {len(tl)} giorni ===")
    print(f"Follower: {tl[0]['followers']} -> {res['final_followers']} | "
          f"lead totali: {res['final_leads']} | autonomia finale: L{res['final_autonomy_level']}")
    for r in tl:
        if r["day"] % 3 == 0 or r["day"] == 1:
            print(f"  g{r['day']:>2} follower {r['followers']:>4} reach {r['reach']:>5} "
                  f"lead {r['total_leads']:>2}  {_bar(r['followers'], fmax)}")


def main():
    print("MULTIVERSO MARKETING (modello, tempo compresso)")
    for s in (1, 2, 3):
        show(run_simulation(days=21, seed=s, approve_rate=0.8))
    print("\nNota: il mondo è un MODELLO esplicito (vedi aios/sim/world.py), "
          "non una previsione reale.")


if __name__ == "__main__":
    main()
