import { build } from "esbuild";
import path from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const rootDir = path.resolve(__dirname, "..");
const entryPoint = path.join(rootDir, "webview", "tree", "index.ts");
const outputFile = path.join(rootDir, "media", "tree_view_bundle.js");

await build({
  entryPoints: [entryPoint],
  outfile: outputFile,
  bundle: true,
  format: "iife",
  target: "es2020",
  platform: "browser",
  sourcemap: false,
  minify: false,
  legalComments: "none",
  charset: "utf8",
  logLevel: "info",
});

console.log(`[OK] built tree webview bundle: ${outputFile}`);
