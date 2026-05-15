// Cross-bot bridge: reveal "Continua su K-BOT Premium" once the site widget
// has created a session (key written by components/kbot/KBot.tsx).
// Extracted from inline <script> in suite-ai.html for strict CSP.
(function () {
  const bridge = document.getElementById('kbot-premium-bridge')
  const cta = document.getElementById('kbot-premium-bridge-cta')
  if (!bridge || !cta) return
  function refresh() {
    try {
      const sid = sessionStorage.getItem('kbot.site_session_id')
      if (sid && sid.length > 8) {
        cta.setAttribute('href', '/app/?continue=' + encodeURIComponent(sid))
        bridge.hidden = false
      } else {
        bridge.hidden = true
      }
    } catch (_) { /* ignore */ }
  }
  refresh()
  window.addEventListener('storage', refresh)
  // sessionStorage doesn't fire 'storage' in the same tab — poll lightly.
  setInterval(refresh, 1500)
})()
