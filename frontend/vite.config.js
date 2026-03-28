import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
    plugins: [
    react(),
    tailwindcss(),
  ],
 
  server: {
    port: 5173,
  },
});
