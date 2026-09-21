import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    // dev: forward API calls to the Python backend (uvicorn api:app --port 8000)
    proxy: {
      '/api': 'http://localhost:8000',
    },
  },
})