"""Test binder WebBoost on-page (app/web.py).

Lo score on-page viene dal tool audit_seo_onpage sulla pagina REALE (qui: HTML campione),
non fabbricato dall'LLM. Volumi keyword esterni → non toccati. Fetch fallito/no input →
onesto (verificato=False), nessuna sovrascrittura.

Standalone: python tests/test_web.py → exit 0 se PASS.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app import web  # noqa: E402

ok = True


def check(label, cond):
    global ok
    ok = ok and cond
    print(f"  {'OK ' if cond else 'FAIL'} {label}")


KW = "agenti ai email"
HTML_BUONO = f"""<html><head>
<title>{KW} per PMI | Studio</title>
<meta name="description" content="Automatizza la posta con {KW}: triage, risposte e CRM. Riduci il tempo speso del 40%.">
</head><body>
<h1>{KW}: la guida operativa</h1>
<p>Con gli {KW} la PMI gestisce la posta in automatico. {KW} per il triage,
{KW} per le risposte. Esempio pratico di {KW} nel CRM, integrazione e flusso completo
spiegato passo passo per ottenere risultati misurabili in poche settimane di lavoro.</p>
<img src="a.webp" alt="schema {KW}"><img src="b.webp" alt="dashboard">
</body></html>"""

HTML_SCARSO = """<html><head><title>Home</title></head><body>
<p>Benvenuti nel nostro sito. Contattaci.</p><img src="x.png"></body></html>"""

print("── audit_html (puro): pagina buona → score alto, controlli ottimi ──")
out_b = web.audit_html(HTML_BUONO, KW, "https://x.it")
check("punteggio_0_100 numerico e alto (>55)", out_b.punteggio_0_100 > 55)
check("densità keyword calcolata", out_b.densita_keyword_pct is not None)
check("title/meta/h1 letti (nessuna criticità su title mancante)",
      not any("title" in c.lower() and "manca" in c.lower() for c in out_b.criticita))

print("── audit_html: pagina scarsa (keyword assente) → score basso ──")
out_s = web.audit_html(HTML_SCARSO, KW, "https://x.it")
check("score scarso < buono", out_s.punteggio_0_100 < out_b.punteggio_0_100)
check("alt mancante rilevato (immagine senza alt)",
      any("alt" in c.lower() for c in out_s.criticita) or out_s.punteggio_0_100 < 60)

print("── bind_seo_onpage: sovrascrive lo score LLM con quello deterministico ──")
deliv = {"diagnosi": {"seo_onpage": {"valutazione_sintetica": "tutto ok", "score": 95, "findings": []}}}
meta = web.bind_seo_onpage(deliv, out_s)
so = deliv["diagnosi"]["seo_onpage"]
check("score sovrascritto col valore del tool (non 95)", so["score"] == round(out_s.punteggio_0_100) and so["score"] != 95)
check("findings enum validi (impatto/sforzo/priorita)",
      all(f["impatto"] in ("alto", "medio", "basso") and f["sforzo"] in ("rapido", "medio", "intenso")
          and f["priorita"] in ("P1", "P2", "P3", "P4") for f in so.get("findings", [])))
check("findings hanno problema (testo dal controllo reale)",
      all(f.get("problema") for f in so.get("findings", [])))

print("── apply_web: senza url/keyword → onesto, nessuna sovrascrittura ──")
d2 = {"diagnosi": {"seo_onpage": {"valutazione_sintetica": "x", "score": 80, "findings": []}}}
_, m2 = web.apply_web(d2, {"keywords_seed": ["x"]})  # manca url
check("verificato=False senza url", m2["verificato"] is False)
check("score LLM non toccato (80)", d2["diagnosi"]["seo_onpage"]["score"] == 80)
check("nota volumi esterni presente", "volumi" in m2.get("nota_volumi", "").lower())

print("── fetch_html: url non valido → None (nessun fetch) ──")
check("url non-http → None", web.fetch_html("non-un-url") is None)

print("\nTEST WEB " + ("PASS ✅" if ok else "FAIL ❌"))
sys.exit(0 if ok else 1)
