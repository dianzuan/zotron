import { defineConfig } from "zotero-plugin-scaffold";

export default defineConfig({
  name: "Zotero Bridge",
  id: "zotero-bridge@diamondrill",
  namespace: "ZoteroBridge",
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
      prefix: "extensions.zoterobridge",
    },
    esbuildOptions: [
      {
        entryPoints: ["src/index.ts"],
        outfile: ".scaffold/build/addon/content/scripts/zotero-bridge.js",
        bundle: true,
        target: "firefox115",
      },
    ],
  },
});
