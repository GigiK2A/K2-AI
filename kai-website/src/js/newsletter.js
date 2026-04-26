document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.newsletter-form').forEach(initNewsletterForm)
})

function initNewsletterForm(form) {
  const input = form.querySelector('input[type="email"]')
  const btn = form.querySelector('button[type="submit"]')
  const msg = form.querySelector('.newsletter-msg')
  const source = form.dataset.source || 'website'

  const nameInput = form.querySelector('input[name="name"]')

  form.addEventListener('submit', async (e) => {
    e.preventDefault()
    const email = input?.value?.trim()
    if (!email) return

    const name = nameInput?.value?.trim() || null

    btn.disabled = true
    btn.textContent = 'Invio...'
    if (msg) { msg.textContent = ''; msg.className = 'newsletter-msg' }

    try {
      const res = await fetch('/api/newsletter/subscribe', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, name, source }),
      })
      const data = await res.json()

      if (res.ok && data.ok) {
        if (msg) {
          msg.textContent = data.already
            ? 'Sei già iscritto alla newsletter.'
            : 'Controlla la tua email: ti abbiamo inviato il link di conferma.'
          msg.className = 'newsletter-msg newsletter-msg--ok'
        }
        input.value = ''
        btn.textContent = 'Iscriviti'
        btn.disabled = false
      } else {
        throw new Error(data.error || 'Errore')
      }
    } catch (err) {
      if (msg) {
        msg.textContent = err.message === 'Email non valida'
          ? 'Email non valida.'
          : 'Errore temporaneo, riprova.'
        msg.className = 'newsletter-msg newsletter-msg--err'
      }
      btn.disabled = false
      btn.textContent = 'Iscriviti'
    }
  })
}
