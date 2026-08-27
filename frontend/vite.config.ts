import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    host: true,
    allowedHosts: [".vercel.run", ".vercel.app", ".vusercontent.net", ".v0.build"],
    hmr: {
      protocol: "wss",
      clientPort: 443,
    },
    proxy: {
      "/api": "http://127.0.0.1:8000",
    },
  },
});
