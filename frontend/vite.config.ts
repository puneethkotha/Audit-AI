import tailwindcss from "@tailwindcss/vite";
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  base: process.env.VERCEL ? "/" : "/Audit-AI/",
  server: {
    port: 3000,
    proxy: {
      "/audit": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
      "/rules": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
      "/health": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
});
