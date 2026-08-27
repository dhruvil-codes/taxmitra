import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "");
  const backend = (env.BACKEND || env.BACKEND_2 || "http://127.0.0.1:8000").replace(/\/$/, "");

  return {
    plugins: [react(), tailwindcss()],
    server: {
      host: true,
      allowedHosts: [".vercel.run", ".vercel.app", ".vusercontent.net", ".v0.build"],
      proxy: {
        "/api": {
          target: backend,
          changeOrigin: true,
        },
      },
    },
  };
});
