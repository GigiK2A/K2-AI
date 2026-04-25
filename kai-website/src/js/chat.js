const API_BASE_URL = import.meta.env.VITE_KAI_API_BASE_URL || '';

// Contesto pacchetto: presente quando l'utente arriva da /suite-ai
// tramite il link CTA di un pacchetto specifico (?pkg=ID&pkg_title=TITLE)
const PKG_CTX = (() => {
  try {
    const p = new URLSearchParams(window.location.search);
    const id = (p.get('pkg') || '').trim().slice(0, 120);
    if (!id) return null;
    const title = (p.get('pkg_title') || id).trim().slice(0, 160);
    return { id, title };
  } catch { return null; }
})();

// Se arriva da un pacchetto, usa storage key separato per non mescolare
// le chat di pacchetti diversi o la chat generica
const CHAT_STORAGE_KEY = PKG_CTX
  ? `kai-chat-pkg-${PKG_CTX.id}`
  : 'kai-analysis-chat-history';
const CHAT_SESSION_KEY = PKG_CTX
  ? `kai-session-pkg-${PKG_CTX.id}`
  : 'kai-analysis-session-id';

const CONTACT_PREFILL_KEY = 'kai-contact-prefill';
const CONTACT_PREFILL_META_KEY = 'kai-contact-prefill-meta';
const CONTACT_PREFILL_SOURCE_KEY = 'kai-contact-prefill-source';
const MAX_STORED_MESSAGES = 24;
const messages = [];
let isSending = false;

function resolveApiBaseUrl() {
  if (API_BASE_URL.trim()) {
    return API_BASE_URL.replace(/\/$/, '');
  }
  // In dev, Vite proxy forwards /api → localhost:8000 (same origin, no CORS)
  if (import.meta.env.DEV) {
    return '';
  }
  return 'https://api.k2-ai.it';
}

const CHAT_ENDPOINT = `${resolveApiBaseUrl()}/api/intake/kbot-chat`;

const FIRST_MESSAGE = PKG_CTX
  ? {
      role: 'assistant',
      content: `Ciao! Stai guardando il pacchetto **${PKG_CTX.title}**.\n\nRaccontami il processo che vorresti ottimizzare: cosa succede oggi, dove si perde tempo e quali strumenti usi già. Così vediamo subito se questo pacchetto è adatto al tuo caso.`
    }
  : {
      role: 'assistant',
      content: "Ciao. Raccontami in 2-3 righe il processo che ti costa più tempo: cosa succede oggi, dove si blocca e quali strumenti usi già. Da lì capiamo se l'AI può fare la differenza."
    };

function generateSessionId() {
  const cryptoApi = globalThis.crypto;

  if (cryptoApi?.randomUUID) {
    return cryptoApi.randomUUID();
  }

  if (cryptoApi?.getRandomValues) {
    const bytes = cryptoApi.getRandomValues(new Uint8Array(16));
    bytes[6] = (bytes[6] & 0x0f) | 0x40;
    bytes[8] = (bytes[8] & 0x3f) | 0x80;
    const hex = Array.from(bytes, byte => byte.toString(16).padStart(2, '0')).join('');
    return [
      hex.slice(0, 8),
      hex.slice(8, 12),
      hex.slice(12, 16),
      hex.slice(16, 20),
      hex.slice(20, 32)
    ].join('-');
  }

  const now = Date.now().toString(16);
  const random = Math.random().toString(16).slice(2, 18).padEnd(16, '0');
  return `${now.slice(-8)}-${random.slice(0, 4)}-4${random.slice(5, 8)}-a${random.slice(9, 12)}-${random.slice(0, 12)}`;
}

function getOrCreateSessionId() {
  try {
    const existing = sessionStorage.getItem(CHAT_SESSION_KEY);
    if (existing) return existing;

    const nextId = generateSessionId();
    sessionStorage.setItem(CHAT_SESSION_KEY, nextId);
    return nextId;
  } catch {
    return generateSessionId();
  }
}

function refreshSessionId() {
  const nextId = generateSessionId();

  try {
    sessionStorage.setItem(CHAT_SESSION_KEY, nextId);
  } catch {
    // ignore storage failures
  }

  return nextId;
}

function loadMessages() {
  try {
    const raw = sessionStorage.getItem(CHAT_STORAGE_KEY);
    if (!raw) return [];

    const parsed = JSON.parse(raw);
    if (!Array.isArray(parsed)) return [];

    return parsed
      .filter(message =>
        message &&
        (message.role === 'assistant' || message.role === 'user') &&
        typeof message.content === 'string' &&
        message.content.trim()
      )
      .slice(-MAX_STORED_MESSAGES);
  } catch {
    return [];
  }
}

function persistMessages() {
  try {
    sessionStorage.setItem(
      CHAT_STORAGE_KEY,
      JSON.stringify(messages.slice(-MAX_STORED_MESSAGES))
    );
  } catch {
    // ignore storage failures
  }
}

function clearMessages() {
  messages.splice(0, messages.length);
  messages.push(FIRST_MESSAGE);
  persistMessages();
}

function truncateText(text, maxLength) {
  const clean = String(text || '').trim();
  if (clean.length <= maxLength) return clean;
  return `${clean.slice(0, maxLength - 1).trimEnd()}…`;
}

function cleanAssistantContactText(text) {
  return String(text || '')
    .replace(/(?:^|\n)\s*\/contatti(?:\.html)?\s*(?:$|\n)/gi, '\n')
    .replace(/\s{2,}/g, ' ')
    .trim();
}

function splitIntoSentences(text) {
  return String(text || '')
    .split(/[\n\r]+|(?<=[.!?])\s+/)
    .map(line => line.trim())
    .filter(Boolean);
}

function uniqueLines(items, maxItems = 4, maxLength = 320) {
  const seen = new Set();
  const result = [];

  for (const item of items) {
    const normalized = String(item || '').trim();
    if (!normalized) continue;

    const key = normalized.toLowerCase();
    if (seen.has(key)) continue;
    seen.add(key);

    result.push(truncateText(normalized, maxLength));
    if (result.length >= maxItems) break;
  }

  return result;
}

function pickObjective(sentences) {
  const objectiveRegex = /\b(voglio|vorrei|mi serve|ci serve|obiettivo|devo|dobbiamo|cos[iì] da|in modo da|per poter)\b/i;
  return sentences.find(sentence => objectiveRegex.test(sentence)) || '';
}

function pickConstraints(sentences) {
  const constraintRegex = /\b(budget|tempo|deadline|team|strument|crm|erp|excel|api|n8n|zapier|integrazion|privacy|gdpr|approvaz|manuale|database|legacy|software)\b/i;
  return uniqueLines(sentences.filter(sentence => constraintRegex.test(sentence)), 4, 220);
}

function buildClientFacingContactMessage(problem, contextLines, objective) {
  const parts = [];

  parts.push('Buongiorno, vi contatto perché sto valutando un intervento su un processo che oggi crea attrito operativo.');

  if (problem) {
    parts.push(`In sintesi, il problema principale è questo: ${truncateText(problem, 700)}`);
  }

  if (contextLines.length > 0) {
    parts.push(`Oggi la situazione è questa: ${truncateText(contextLines.join(' '), 700)}`);
  }

  if (objective) {
    parts.push(`L'obiettivo è questo: ${truncateText(objective, 450)}`);
  } else {
    parts.push("Vorrei capire se ha senso automatizzare il flusso, creare un prototipo o impostare una soluzione più strutturata.");
  }

  parts.push("Mi farebbe comodo un confronto per capire se il caso regge davvero e quale strada ha più senso.");

  return truncateText(parts.join('\n\n'), 1800);
}

function buildContactPrefill() {
  const userMessages = messages
    .filter(message => message.role === 'user')
    .map(message => String(message.content || '').trim())
    .filter(Boolean);

  const assistantMessages = messages
    .filter(message => message.role === 'assistant' && message.content !== FIRST_MESSAGE.content)
    .map(message => cleanAssistantContactText(message.content))
    .filter(Boolean);

  const allUserSentences = uniqueLines(userMessages.flatMap(splitIntoSentences), 8, 320);
  const contextLines = uniqueLines(userMessages.slice(1).flatMap(splitIntoSentences), 4, 240);
  const objective = pickObjective(allUserSentences);
  const constraints = pickConstraints(allUserSentences);
  const latestDiagnosis = assistantMessages.at(-1);
  const problem = userMessages.length > 0 ? truncateText(userMessages[0], 850) : '';

  const internalParts = [
    PKG_CTX
      ? `Arrivo da K-BOT — pacchetto di interesse: ${PKG_CTX.title} (ID: ${PKG_CTX.id}).`
      : 'Arrivo da K-BOT.'
  ];

  if (problem) {
    internalParts.push(`Problema da risolvere:\n${problem}`);
  }

  if (contextLines.length > 0) {
    internalParts.push(`Contesto attuale:\n${contextLines.map(line => `- ${line}`).join('\n')}`);
  } else if (allUserSentences.length > 1) {
    internalParts.push(`Contesto attuale:\n- ${allUserSentences.slice(1, 3).join('\n- ')}`);
  }

  internalParts.push(
    `Obiettivo desiderato:\n${objective || 'Da confermare nel contatto diretto, partendo da quanto emerso in chat.'}`
  );

  if (constraints.length > 0) {
    internalParts.push(`Vincoli o strumenti già emersi:\n${constraints.map(line => `- ${line}`).join('\n')}`);
  }

  if (latestDiagnosis) {
    internalParts.push(`Diagnosi iniziale K-BOT:\n${truncateText(latestDiagnosis, 900)}`);
  }

  return {
    publicMessage: buildClientFacingContactMessage(problem, contextLines, objective),
    internalContext: truncateText(internalParts.join('\n\n'), 2600),
  };
}

function persistContactPrefill() {
  const prefill = buildContactPrefill();

  try {
    sessionStorage.setItem(CONTACT_PREFILL_KEY, prefill.publicMessage);
    sessionStorage.setItem(CONTACT_PREFILL_META_KEY, prefill.internalContext);
    sessionStorage.setItem(
      CONTACT_PREFILL_SOURCE_KEY,
      PKG_CTX ? `k-bot_pkg_${PKG_CTX.id}` : 'k-bot'
    );
  } catch {
    // ignore storage failures
  }
}

function initChat() {
  const container = document.getElementById('chat-messages');
  const input = document.getElementById('chat-input');
  const sendBtn = document.getElementById('chat-send');
  const form = document.getElementById('chat-form');
  const resetBtn = document.getElementById('chat-reset');

  if (!container || !input || !sendBtn) return;
  getOrCreateSessionId();

  const savedMessages = loadMessages();

  if (savedMessages.length) {
    messages.push(...savedMessages);
    savedMessages.forEach(renderMessage);
  } else {
    messages.push(FIRST_MESSAGE);
    persistMessages();
    renderMessage(FIRST_MESSAGE);
  }

  const handleSubmit = event => {
    event?.preventDefault?.();
    sendMessage();
  };

  form?.addEventListener('submit', handleSubmit);
  sendBtn.addEventListener('click', handleSubmit);
  sendBtn.addEventListener(
    'touchend',
    event => {
      event.preventDefault();
      sendMessage();
    },
    { passive: false }
  );
  resetBtn?.addEventListener('click', resetChat);
  container.addEventListener('click', event => {
    const target = event.target.closest('[data-contact-cta]');
    if (!target) return;
    persistContactPrefill();
  });
  input.addEventListener('keydown', e => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  });
}

async function sendMessage() {
  const input = document.getElementById('chat-input');
  const sendBtn = document.getElementById('chat-send');
  if (!input || !sendBtn || isSending) return;

  const text = input.value.trim();
  if (!text) return;

  isSending = true;
  input.value = '';
  const userMsg = { role: 'user', content: text };
  messages.push(userMsg);
  persistMessages();
  renderMessage(userMsg);

  const typing = renderTyping();
  sendBtn.disabled = true;

  try {
    const chatPayload = {
      session_id: getOrCreateSessionId(),
      source_page: PKG_CTX ? `k-bot_pkg_${PKG_CTX.id}` : 'k-bot',
      messages,
    };
    if (PKG_CTX) chatPayload.package_context = PKG_CTX;

    const res = await fetch(CHAT_ENDPOINT, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Accept: 'application/json',
        'X-KAI-Request': 'fetch'
      },
      body: JSON.stringify(chatPayload)
    });

    if (res.status === 429) {
      typing.remove();
      renderMessage({ role: 'assistant', content: 'Hai inviato troppi messaggi di fila. Aspetta un minuto e riprova.' });
      return;
    }

    if (!res.ok) throw new Error(`HTTP ${res.status}`);

    const data = await res.json();
    const assistantMsg = { role: 'assistant', content: data.message };
    messages.push(assistantMsg);
    persistMessages();
    typing.remove();
    renderMessage(assistantMsg);
  } catch {
    typing.remove();
    renderMessage({ role: 'assistant', content: 'Errore di connessione. Riprova.' });
  } finally {
    isSending = false;
    sendBtn.disabled = false;
    input.focus();
  }
}

function renderMessage({ role, content }) {
  const container = document.getElementById('chat-messages');
  const div = document.createElement('div');
  div.className = `chat-message chat-${role}`;
  if (role === 'assistant') {
    div.append(_renderAssistantContent(content));
  } else {
    div.textContent = content;
  }
  container.appendChild(div);
  container.scrollTop = container.scrollHeight;
  return div;
}

function _renderAssistantContent(text) {
  const fragment = document.createDocumentFragment();

  const cleaned = text
    // rimuovi varianti comuni di "link: /contatti" o "su /contatti"
    .replace(/(?:al seguente link|seguente link|link|su|a)\s*:\s*\/contatti(?:\.html)?/gi, '')
    .replace(/\/contatti(?:\.html)?/gi, '')
    .trim()
    // rimuovi puntini/virgole/punti residui a fine frase prima del bottone
    .replace(/[,.:]\s*$/, '');

  // Se il testo originale conteneva /contatti, aggiungi il bottone in fondo
  const hasContact = /\/contatti(?:\.html)?/i.test(text);
  const urlRegex = /(https?:\/\/[^\s<>"]+)/g;
  let cursor = 0;
  let match;

  while ((match = urlRegex.exec(cleaned)) !== null) {
    if (match.index > cursor) {
      fragment.append(document.createTextNode(cleaned.slice(cursor, match.index)));
    }

    const url = match[0];
    const link = document.createElement('a');
    link.href = url;
    link.target = '_blank';
    link.rel = 'noopener noreferrer';
    link.className = 'chat-link';
    link.textContent = url;
    fragment.append(link);
    cursor = match.index + url.length;
  }

  if (cursor < cleaned.length) {
    fragment.append(document.createTextNode(cleaned.slice(cursor)));
  }

  if (hasContact) {
    const contactBtn = document.createElement('a');
    contactBtn.href = '/contatti';
    contactBtn.className = 'chat-cta-btn';
    contactBtn.dataset.contactCta = '1';
    contactBtn.textContent = 'Scrivici →';
    fragment.append(document.createTextNode('\n'));
    fragment.append(contactBtn);
  }

  return fragment;
}

function renderTyping() {
  const container = document.getElementById('chat-messages');
  const div = document.createElement('div');
  div.className = 'chat-message chat-assistant chat-typing';
  for (let index = 0; index < 3; index += 1) {
    div.appendChild(document.createElement('span'));
  }
  container.appendChild(div);
  container.scrollTop = container.scrollHeight;
  return div;
}

function resetChat() {
  const container = document.getElementById('chat-messages');
  const input = document.getElementById('chat-input');

  if (!container) return;

  container.replaceChildren();
  refreshSessionId();
  clearMessages();
  renderMessage(FIRST_MESSAGE);

  if (input) {
    input.value = '';
    input.focus();
  }
}

document.addEventListener('DOMContentLoaded', initChat);
