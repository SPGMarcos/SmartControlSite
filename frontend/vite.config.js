import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  base: process.env.VITE_BASE_PATH || "/",
  plugins: [react()],
  server: {
    host: "0.0.0.0",
    port: 5173,
    proxy: process.env.VITE_DEV_API_PROXY_TARGET
      ? {
          "/api": {
            target: process.env.VITE_DEV_API_PROXY_TARGET,
            changeOrigin: true,
            secure: false
          }
        }
      : undefined
  }
});
