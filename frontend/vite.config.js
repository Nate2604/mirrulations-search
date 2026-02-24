import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
    plugins: [react()],
    base: '/static/',
    build: {
        outDir: '../static',
        emptyOutDir: false
    },
    server: {
        proxy: {
            '/search': 'http://127.0.0.1:80'
        }
    }
})