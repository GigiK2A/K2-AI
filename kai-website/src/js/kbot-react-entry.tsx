import React from 'react'
import { createRoot } from 'react-dom/client'
import { KBot } from '../../components/kbot/KBot'

const rootEl = document.getElementById('kbot-react-root')
if (rootEl) {
  const root = createRoot(rootEl)
  root.render(<KBot />)
}
