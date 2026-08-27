import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

function apiOrigin(value: string | undefined): string | undefined {
  const trimmed = value?.trim();
  if (!trimmed) return undefined;

  let parsed: URL;
  try {
    parsed = new URL(trimmed);
  } catch {
    throw new Error("VITE_API_BASE_URL must be an absolute http(s) URL");
  }
  if (parsed.protocol !== "http:" && parsed.protocol !== "https:") {
    throw new Error("VITE_API_BASE_URL must use http:// or https://");
  }
  if (parsed.username || parsed.password || parsed.search || parsed.hash) {
    throw new Error("VITE_API_BASE_URL must be an API origin without credentials, query, or hash");
  }
  return parsed.origin;
}

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "VITE_");
  const target = apiOrigin(env.VITE_API_BASE_URL);

  return {
    plugins: [react(), tailwindcss()],
    // Keep the client URLs relative when no production API origin is set.
    // In development, proxy those relative URLs to the local FastAPI service.
    // A configured origin is also used for separate frontend/backend dev.
    server: {
      host: true,
      allowedHosts: [".vercel.run", ".vercel.app", ".vusercontent.net", ".v0.build"],
      proxy: {
        "/api": {
          target: target ?? "http://127.0.0.1:8000",
          changeOrigin: true,
        },
      },
    },
  };
});
