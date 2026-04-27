import { defineConfig } from "zotero-plugin-scaffold";

export default defineConfig({
  name: "Zotron",
  id: "zotron@diamondrill",
  namespace: "Zotron",
  source: ["src", "addon"],
  logLevel: "DEBUG" as any,
  server: {
    asProxy: true,
  } as any,
  plugins: {
    asProxy: true,
  } as any,
  build: {
    prefs: {
      prefix: "extensions.zotron",
    },
    esbuildOptions: [
      {
        entryPoints: ["src/index.ts"],
        outfile: ".scaffold/build/addon/content/scripts/zotron.js",
        bundle: true,
        target: "firefox115",
      },
    ],
  },
});
