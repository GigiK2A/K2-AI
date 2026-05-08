import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import fs from 'fs'
import path from 'path'

const securityHeaders = {
  'Content-Security-Policy': [
    "default-src 'self'",
    "script-src 'self' 'unsafe-inline'",
    "style-src 'self' 'unsafe-inline'",
    "img-src 'self' data: https://*.stripe.com",
    "media-src 'self'",
    "font-src 'self' https://api.fontshare.com https://fonts.gstatic.com",
    "connect-src 'self' http://localhost:3000 http://localhost:8000 http://127.0.0.1:8000 http://192.168.0.62:8000 http://192.168.1.169:8000 https://*.stripe.com https://checkout.stripe.com ws://localhost:3000 ws://127.0.0.1:3000",
    "frame-src https://*.stripe.com https://checkout.stripe.com",
    "form-action 'self'",
    "frame-ancestors 'none'",
    "object-src 'none'",
    "base-uri 'self'"
  ].join('; '),
  'X-Frame-Options': 'DENY',
  'X-Content-Type-Options': 'nosniff',
  'Referrer-Policy': 'strict-origin-when-cross-origin',
  'Permissions-Policy': 'camera=(), microphone=(), geolocation=(), payment=(), usb=(), interest-cohort=()',
  'Cross-Origin-Opener-Policy': 'same-origin',
  'Cross-Origin-Resource-Policy': 'same-origin'
}

function blockSensitiveFallbacks() {
  const blockedPaths = new Set([
    '/admin',
    '/dashboard',
    '/login',
    '/wp-admin',
    '/wp-login.php',
    '/package.json',
    '/package-lock.json',
    '/pnpm-lock.yaml',
    '/yarn.lock',
    '/.DS_Store',
    '/.well-known',
    '/.well-known/'
  ])

  const middleware = (req, res, next) => {
    const pathname = new URL(req.url || '/', 'http://localhost').pathname
    const isSourceMap = pathname.endsWith('.map')
    const isHiddenPath = /^\/\./.test(pathname)
    const isBlockedPath = blockedPaths.has(pathname)

    Object.entries(securityHeaders).forEach(([header, value]) => {
      res.setHeader(header, value)
    })

    if (pathname.startsWith('/api/') && req.method === 'OPTIONS') {
      const origin = req.headers.origin
      const allowedOrigins = new Set([
        'http://localhost:4173',
        'http://127.0.0.1:4173',
        'http://192.168.0.62:4173',
        'http://192.168.1.169:4173'
      ])

      if (allowedOrigins.has(origin)) {
        res.setHeader('Access-Control-Allow-Origin', origin)
        res.setHeader('Vary', 'Origin, Access-Control-Request-Headers')
      }
      res.setHeader('Access-Control-Allow-Methods', 'POST')
      res.setHeader('Access-Control-Allow-Headers', 'Content-Type, X-KAI-Request')
      res.statusCode = 204
      res.end()
      return
    }

    if (isSourceMap || isHiddenPath || isBlockedPath) {
      res.statusCode = 404
      res.setHeader('Content-Type', 'text/plain; charset=utf-8')
      res.end('Not found')
      return
    }

    next()
  }

  return {
    name: 'block-sensitive-fallbacks',
    configureServer(server) {
      server.middlewares.use(middleware)
    },
    configurePreviewServer(server) {
      server.middlewares.use(middleware)
    }
  }
}

export default defineConfig({
  root: 'src',
  plugins: [react(), blockSensitiveFallbacks()],
  build: {
    outDir: '../dist',
    emptyOutDir: true,
    sourcemap: false,
    chunkSizeWarningLimit: 900,
    target: ['chrome87', 'edge88', 'firefox78', 'safari14'],
    cssTarget: ['chrome87', 'edge88', 'firefox78', 'safari14'],
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (!id.includes('node_modules')) return
          if (id.includes('/three/')) return 'vendor-three'
          if (id.includes('/react/') || id.includes('/react-dom/')) return 'vendor-react'
          if (id.includes('/@supabase/')) return 'vendor-supabase'
          if (id.includes('/@anthropic-ai/')) return 'vendor-anthropic'
          if (id.includes('/stripe/')) return 'vendor-stripe'
          return undefined
        },
      },
      input: {
        main: 'src/index.html',
        metodo: 'src/metodo.html',
        'casi-studio': 'src/casi-studio.html',
        laboratorio: 'src/laboratorio.html',
        analisi: 'src/analisi.html',
        'k-bot': 'src/k-bot.html',
        'report-preview': 'src/report-preview.html',
        contatti: 'src/contatti.html',
        privacy: 'src/privacy.html',
        cookie: 'src/cookie.html',
        'note-legali': 'src/note-legali.html',
        workshop: 'src/workshop.html',
        'suite-ai': 'src/suite-ai.html',
        newsletter: 'src/newsletter.html',
        'newsletter-entry': 'src/newsletter-entry.html',
        'newsletter-ok': 'src/newsletter-ok.html',
        'newsletter-error': 'src/newsletter-error.html',
        ...collectSuiteAiHtmlInputs(),
      }
    }
  },
  server: {
    host: '0.0.0.0',
    sourcemap: false,
    headers: securityHeaders,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true
      }
    }
  },
  preview: {
    host: '0.0.0.0',
    headers: securityHeaders,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true
      }
    }
  }
})

function collectSuiteAiHtmlInputs() {
  const suiteDir = path.resolve(process.cwd(), 'src/suite-ai')
  if (!fs.existsSync(suiteDir)) return {}

  const entries = {}
  for (const fileName of fs.readdirSync(suiteDir)) {
    if (!fileName.endsWith('.html')) continue
    if (fileName.startsWith('._')) continue
    const slug = fileName.replace(/\.html$/i, '')
    entries[`suite-ai/${slug}`] = `src/suite-ai/${fileName}`
  }
  return entries
}
