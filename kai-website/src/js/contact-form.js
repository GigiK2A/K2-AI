const API_BASE_URL = import.meta.env.VITE_KAI_API_BASE_URL || '';

const SUITE_PACKAGE_TITLES = {
  P01: 'Agenti AI Email & CRM',
  P02: 'Automazioni Amministrative',
  P03: 'AI Legale & Contratti',
  P04: 'AI Ingegneria & Progettazione',
  P05: 'Microapp Documenti Tecnici',
  P06: 'AI Customer Service & Ticket',
  P07: 'RAG Knowledge Base',
  P08: 'AI Compliance & Audit',
  P09: 'AI Controllo di Gestione',
  P10: 'Integrazione Gestionali & ERP',
  P11: 'AI Marketing & Contenuti',
  P12: 'Diagnosi Strategica PMI',
  P13: 'Agevolazioni & Finanza Agevolata',
  P14: 'AI Edilizia & Appalti Pubblici',
  P15: 'AI HR & Recruiting',
  P16: 'AI Real Estate & Tokenizzazione',
  P17: 'AI Data Analytics & BI',
  P18: 'AI UX & Design System',
  P19: 'AI Efficienza Energetica',
  P20: 'AI Hospitality & Revenue'
};

// Contesto pacchetto dalla URL (?pkg=ID&pkg_title=TITLE)
const PKG_CTX = (() => {
  try {
    const p = new URLSearchParams(window.location.search);
    const id = (p.get('pkg') || '').trim().toUpperCase().slice(0, 120);
    if (!id) return null;
    const title = (p.get('pkg_title') || SUITE_PACKAGE_TITLES[id] || id).trim().slice(0, 160);
    return { id, title };
  } catch { return null; }
})();

const CONTACT_PREFILL_KEY = 'kai-contact-prefill';
const CONTACT_PREFILL_META_KEY = 'kai-contact-prefill-meta';
const CONTACT_PREFILL_SOURCE_KEY = 'kai-contact-prefill-source';
const CONTACT_PREFILL_FIELDS_KEY = 'kai-contact-prefill-fields';

function resolveApiBaseUrl() {
  if (API_BASE_URL.trim()) {
    return API_BASE_URL.replace(/\/$/, '');
  }
  // Usa same-origin in ogni ambiente: in produzione il server web fa proxy su api.k2-ai.it
  return '';
}

const CONTACT_ENDPOINT = `${resolveApiBaseUrl()}/api/intake/contact`;

function mapContactError(status, detail) {
  const detailText = String(detail || '').trim();

  if (status === 400) {
    if (detailText) return `Invio non riuscito: ${detailText}.`;
    return 'Invio non riuscito: controlla i campi del modulo e riprova.';
  }

  if (status === 429) {
    return 'Hai fatto troppi tentativi in poco tempo. Attendi un minuto e riprova.';
  }

  if (status === 0) {
    return 'Errore di rete. Controlla la connessione e riprova.';
  }

  return 'Errore nell\'invio. Riprova più tardi o contattaci direttamente.';
}

function setFeedback(success, error, type, form) {
  if (type === 'success' && form) {
    // Nasconde tutto il form e mostra solo il messaggio di successo
    Array.from(form.elements).forEach(el => { el.hidden = true; });
    form.querySelectorAll('.form-group, .contact-submit, .contact-submit-note, .contact-legal-note, .hp-field').forEach(el => { el.hidden = true; });
    success.hidden = false;
    error.hidden = true;
  } else {
    success.hidden = type !== 'success';
    error.hidden = type !== 'error';
  }
}

function loadContactPrefill() {
  try {
    let fields = {};
    try {
      fields = JSON.parse(sessionStorage.getItem(CONTACT_PREFILL_FIELDS_KEY) || '{}') || {};
    } catch {
      fields = {};
    }

    return {
      message: String(sessionStorage.getItem(CONTACT_PREFILL_KEY) || '').trim(),
      internalContext: String(sessionStorage.getItem(CONTACT_PREFILL_META_KEY) || '').trim(),
      source: String(sessionStorage.getItem(CONTACT_PREFILL_SOURCE_KEY) || '').trim(),
      fields
    };
  } catch {
    return { message: '', internalContext: '', source: '', fields: {} };
  }
}

function clearContactPrefill() {
  try {
    sessionStorage.removeItem(CONTACT_PREFILL_KEY);
    sessionStorage.removeItem(CONTACT_PREFILL_META_KEY);
    sessionStorage.removeItem(CONTACT_PREFILL_SOURCE_KEY);
    sessionStorage.removeItem(CONTACT_PREFILL_FIELDS_KEY);
  } catch {
    // ignore storage failures
  }
}

document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('contact-form');
  const success = document.getElementById('form-success');
  const error = document.getElementById('form-error');

  if (!form || !success || !error) return;

  const submitButton = form.querySelector('[type="submit"]');
  const honeypot = form.querySelector('input[name="website"]');
  const messageField = form.querySelector('textarea[name="messaggio"]');
  const settoreField = form.querySelector('select[name="settore"]');
  const companyField = form.querySelector('input[name="azienda"]');
  const prefill = loadContactPrefill();

  // Pre-seleziona settore da URL param (es. ?settore=finance)
  const urlParams = new URLSearchParams(window.location.search);
  const settoreParam = (urlParams.get('settore') || '').trim();
  if (settoreField && settoreParam) {
    const opt = settoreField.querySelector(`option[value="${settoreParam}"]`);
    if (opt) settoreField.value = settoreParam;
  } else if (settoreField && prefill.fields?.sector) {
    const sector = String(prefill.fields.sector || '').trim();
    const opt = settoreField.querySelector(`option[value="${sector}"]`);
    if (opt) settoreField.value = sector;
  }

  if (companyField && !companyField.value.trim() && prefill.fields?.company_role) {
    companyField.value = String(prefill.fields.company_role || '').trim();
  }

  if (messageField && !messageField.value.trim() && prefill.message) {
    messageField.value = prefill.message;
    form.dataset.sourcePage = prefill.source || 'k-bot_to_contatti';
  } else if (messageField && !messageField.value.trim() && PKG_CTX) {
    // Arriva direttamente da un pacchetto Suite AI (senza passare per K-BOT)
    messageField.value =
      `Buongiorno, sono interessato al pacchetto Suite AI «${PKG_CTX.title}».\n\n` +
      `Processo da ottimizzare: [descrivi qui in 2-3 righe cosa fa il team oggi]\n` +
      `Dove si perde tempo: [il collo di bottiglia principale]\n` +
      `Strumenti già in uso: [es. Excel, CRM, gestionale]\n\n` +
      `Vorrei capire se questo pacchetto si adatta al mio caso.`;
    form.dataset.sourcePage = 'workshop_to_contatti';
    form.dataset.packageId = PKG_CTX.id;
    form.dataset.packageTitle = PKG_CTX.title;
  } else {
    form.dataset.sourcePage = 'contatti';
  }

  form.addEventListener('submit', async (event) => {
    event.preventDefault();

    if (honeypot && honeypot.value.trim()) {
      form.reset();
      return;
    }

    if (!form.reportValidity()) return;
    if (!submitButton) return;

    submitButton.disabled = true;
    submitButton.textContent = 'Invio in corso...';
    setFeedback(success, error, null);

    const formData = new FormData(form);

    // Contesto interno: da K-BOT (se presente) oppure dal pacchetto di provenienza
    const internalContext = prefill.internalContext ||
      (PKG_CTX
        ? `Contatto diretto dalla pagina Suite AI — pacchetto: ${PKG_CTX.title} (ID: ${PKG_CTX.id})`
        : '');

    const payload = {
      name: String(formData.get('name') || '').trim(),
      email: String(formData.get('email') || '').trim(),
      company_role: String(formData.get('azienda') || '').trim(),
      sector: String(formData.get('settore') || '').trim(),
      message: String(formData.get('messaggio') || '').trim(),
      internal_context: internalContext,
      source_page: form.dataset.sourcePage || 'contatti',
      website: honeypot ? honeypot.value.trim() : ''
    };

    try {
      const response = await fetch(CONTACT_ENDPOINT, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Accept: 'application/json',
          'X-KAI-Request': 'fetch'
        },
        body: JSON.stringify(payload)
      });

      if (!response.ok) {
        let detail = '';
        try {
          const body = await response.json();
          if (body && typeof body.detail === 'string') {
            detail = body.detail;
          }
        } catch {
          // ignore invalid json
        }
        const mapped = mapContactError(response.status, detail);
        const err = new Error(mapped);
        err.status = response.status;
        err.detail = detail;
        throw err;
      }

      form.reset();
      form.dataset.sourcePage = 'contatti';
      clearContactPrefill();
      setFeedback(success, error, 'success', form);
    } catch (requestError) {
      console.error('Contact form error:', requestError);
      const status = Number(requestError?.status || 0);
      const detail = requestError?.detail;
      const message = requestError?.message || mapContactError(status, detail);
      error.textContent = message;
      setFeedback(success, error, 'error');
    } finally {
      submitButton.disabled = false;
      submitButton.textContent = 'Invia →';
    }
  });
});
