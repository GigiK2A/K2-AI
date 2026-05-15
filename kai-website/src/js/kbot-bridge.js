// Cross-bot bridge: carry the site-widget session into kbot standalone CTAs.
// Extracted from inline <script> blocks to allow a strict CSP without
// 'unsafe-inline' in script-src.
(function () {
  try {
    const sid = sessionStorage.getItem('kbot.site_session_id')
    if (!sid || sid.length < 8) return
    const carry = '?continue=' + encodeURIComponent(sid)
    document.querySelectorAll('a[href="/app"], a[href="/app/"]').forEach(function (a) {
      a.setAttribute('href', '/app/' + carry)
    })
  } catch (_) { /* ignore */ }
})()
