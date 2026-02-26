import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  envDir: '..', // load .env from repo root
  server: {
    port: 5173,
    host: true, // listen on 0.0.0.0 in Docker

    proxy: {
      "/auth": {
        target: process.env.VITE_API_URL,
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\auth/, '') 
      },
      "/tracks": {
        target: process.env.VITE_API_URL,
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\tracks/, '') 
      }
    }
  }
})
