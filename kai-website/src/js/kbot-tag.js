// Scenario C — aggancia il pillar SEO al K-BOT.
// Dal path della pagina pillar deriva il tag P01-P20 e:
//   1. lo appende ai link verso /app (es. "Apri K-BOT →")
//   2. lo salva in sessionStorage["kbot.tag_pillar"] (il K-BOT lo legge al
//      primo accesso, anche via il flusso ?continue= del bridge premium)
// Così un visitatore che arriva su /suite-ai/ai-legale-contratti.html entra nel
// K-BOT col contesto P03 → il bot propone il Boost legale giusto (vedi
// catalog.json mapping_tag_to_servizi).
(function () {
  // slug pillar (senza .html) → codice pillar SEO
  var MAP = {
    'agenti-email-crm': 'P01',
    'automazioni-amministrative': 'P02',
    'ai-legale-contratti': 'P03',
    'ai-ingegneria-progettazione': 'P04',
    'microapp-documenti-tecnici': 'P05',
    'ai-customer-service-ticket': 'P06',
    'rag-knowledge-base': 'P07',
    'ai-compliance-audit': 'P08',
    'ai-controllo-gestione-reporting': 'P09',
    'integrazione-gestionali-erp': 'P10',
    'ai-marketing-contenuti': 'P11',
    'analisi-strategica-pmi': 'P12',
    'agevolazioni-finanza-agevolata': 'P13',
    'ai-edilizia-appalti-pubblici': 'P14',
    'ai-hr-recruiting': 'P15',
    'ai-real-estate-tokenizzazione': 'P16',
    'ai-data-analytics-bi': 'P17',
    'ai-ux-design-system': 'P18',
    'ai-efficienza-energetica': 'P19',
    'ai-hospitality-revenue': 'P20'
  };

  function currentTag() {
    var m = window.location.pathname.match(/\/suite-ai\/([^/.]+)/);
    return m ? MAP[m[1]] : null;
  }

  var tag = currentTag();
  if (!tag) return;

  try { sessionStorage.setItem('kbot.tag_pillar', tag); } catch (e) { /* ignore */ }

  // appende ?tag= ai link verso /app (preserva eventuali query esistenti)
  var links = document.querySelectorAll('a[href^="/app"]');
  links.forEach(function (a) {
    var href = a.getAttribute('href') || '/app';
    if (href.indexOf('tag=') !== -1) return;
    href += (href.indexOf('?') === -1 ? '?' : '&') + 'tag=' + tag;
    a.setAttribute('href', href);
  });
})();
