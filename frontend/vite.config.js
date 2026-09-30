import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0', // Exposes Vite outside the container
    port: 5173,
    watch: {
      usePolling: true, // Ensures file edits update live in Docker
    },
  },
})
