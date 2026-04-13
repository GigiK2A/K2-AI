const API_BASE_URL = import.meta.env.VITE_KAI_API_BASE_URL || '';
const CONTACT_PREFILL_KEY = 'kai-contact-prefill';
const CONTACT_PREFILL_META_KEY = 'kai-contact-prefill-meta';
const CONTACT_PREFILL_SOURCE_KEY = 'kai-contact-prefill-source';

function resolveApiBaseUrl() {
  if (API_BASE_URL.trim()) {
    return API_BASE_URL.replace(/\/$/, '');
  }
  // In dev, Vite proxy forwards /api → localhost:8000 (same origin, no CORS)
  if (import.meta.env.DEV) {
    return '';
  }
  return window.location.origin.replace(/\/$/, '');
}

const CONTACT_ENDPOINT = `${resolveApiBaseUrl()}/api/intake/contact`;

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
    return {
      message: String(sessionStorage.getItem(CONTACT_PREFILL_KEY) || '').trim(),
      internalContext: String(sessionStorage.getItem(CONTACT_PREFILL_META_KEY) || '').trim(),
      source: String(sessionStorage.getItem(CONTACT_PREFILL_SOURCE_KEY) || '').trim()
    };
  } catch {
    return { message: '', internalContext: '', source: '' };
  }
}

function clearContactPrefill() {
  try {
    sessionStorage.removeItem(CONTACT_PREFILL_KEY);
    sessionStorage.removeItem(CONTACT_PREFILL_META_KEY);
    sessionStorage.removeItem(CONTACT_PREFILL_SOURCE_KEY);
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
  const prefill = loadContactPrefill();

  if (messageField && !messageField.value.trim() && prefill.message) {
    messageField.value = prefill.message;
    form.dataset.sourcePage = prefill.source === 'k-bot' ? 'k-bot_to_contatti' : 'contatti';
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

    const payload = {
      name: String(formData.get('name') || '').trim(),
      email: String(formData.get('email') || '').trim(),
      company_role: String(formData.get('azienda') || '').trim(),
      sector: String(formData.get('settore') || '').trim(),
      message: String(formData.get('messaggio') || '').trim(),
      internal_context: prefill.internalContext,
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
        throw new Error(`HTTP ${response.status}`);
      }

      form.reset();
      form.dataset.sourcePage = 'contatti';
      clearContactPrefill();
      setFeedback(success, error, 'success', form);
    } catch (requestError) {
      console.error('Contact form error:', requestError);
      error.textContent = 'Errore nell\'invio. Riprova più tardi o contattaci direttamente.';
      setFeedback(success, error, 'error');
    } finally {
      submitButton.disabled = false;
      submitButton.textContent = 'Invia →';
    }
  });
});
