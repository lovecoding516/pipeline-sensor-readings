import tailwindcss from '@tailwindcss/vite'
import vue from '@vitejs/plugin-vue'
import { defineConfig } from 'vite'

export default defineConfig({
  plugins: [vue(), tailwindcss()],
  server: {
    // Bind IPv4 explicitly: resolving "localhost" to ::1 makes the dev server
    // unreachable on some Windows setups.
    host: '127.0.0.1',
    port: 5173,
    strictPort: true,
  },
})
