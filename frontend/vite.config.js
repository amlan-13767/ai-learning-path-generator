import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'
import { fileURLToPath } from 'url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, '.', '')
  const backend = env.VITE_BACKEND_ORIGIN || 'http://localhost:5000'

  // Everything the browser needs from Flask is proxied through the dev server so
  // that the SPA only ever talks to its own origin (port 3000). This is what
  // makes the session cookie first-party and keeps port 5000 out of the URL bar.
  const proxy = Object.fromEntries(
    ['/api', '/auth', '/login/google', '/health'].map((route) => [
      route,
      { target: backend, changeOrigin: false },
    ]),
  )

  return {
    plugins: [react()],
    resolve: { alias: { '@': path.resolve(__dirname, './src') } },
    server: {
      port: 3000,
      strictPort: true,
      proxy,
    },
  }
})
