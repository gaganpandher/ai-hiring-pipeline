import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': '/app/src',
    },
  },
  server: {
    host: '0.0.0.0',
    port: 3000,
    hmr: {
      overlay: false,
    },
    open: false,
    proxy: {
      '/api': {
        target: 'http://backend:8000',
        changeOrigin: true,
      },
    },
  },
  optimizeDeps: {
    entries: ['src/main.tsx'],
  },
})