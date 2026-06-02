import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

const isGitHubPagesBuild =
  (globalThis as typeof globalThis & { process?: { env?: Record<string, string | undefined> } })
    .process?.env?.GITHUB_PAGES === "true";

export default defineConfig({
  base: isGitHubPagesBuild ? "/industrial-design-intelligence-mvp/" : "/",
  plugins: [react()],
});
