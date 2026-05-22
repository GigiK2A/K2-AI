const params = new URLSearchParams(window.location.search);
const sessionId = params.get('session_id');
const target = document.querySelector('[data-session-id]');

if (target) {
  if (sessionId && /^cs_(test|live)_[A-Za-z0-9]+$/.test(sessionId)) {
    target.textContent = sessionId;
  } else {
    const container = document.getElementById('kbot-grazie-session');
    if (container) container.style.display = 'none';
  }
}
