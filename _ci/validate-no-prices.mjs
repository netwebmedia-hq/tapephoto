// Carlos, 2026-11-05: no public prices anywhere on tapephoto.com. Work is quoted
// (contact form / WhatsApp), prints included. This fails the deploy if any page
// in the sitemap, llms.txt or llms-full.txt carries a currency amount or schema
// price field. Generic words ("precio", "price list") stay allowed.
import { readFile } from "node:fs/promises";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const PRICE = new RegExp(
  [
    String.raw`\$\s?\d`,
    String.raw`\b(CLP|USD|UF|EUR)\s?\$?\d`,
    String.raw`\d[\d.,]*\s*(CLP|USD|UF|EUR)\b`,
    String.raw`US\$`,
    String.raw`\d[\d.,]*\s*(mil\s+pesos|pesos|lucas|d[oó]lares|dollars)\b`,
    String.raw`\b(diez|veinte|treinta|cincuenta|cien)\s+mil\s+pesos`,
    String.raw`"price(Range|Currency)?"\s*:`,
    String.raw`"@type"\s*:\s*"(Offer|AggregateOffer)"`,
    String.raw`itemprop="price`,
    String.raw`\bdesde\s+\$`,
    String.raw`\bfrom\s+\$`,
  ].join("|"),
  "i",
);

const sitemap = await readFile(join(root, "sitemap.xml"), "utf8");
const pages = [...sitemap.matchAll(/<loc>https:\/\/tapephoto\.com\/([^<]*)<\/loc>/g)].map((m) => m[1] || "index.html");
const files = [...new Set([...pages.map((p) => (p.endsWith("/") ? p + "index.html" : p)), "llms.txt", "llms-full.txt", "404.html", "main.js"])];
const errors = [];
for (const rel of files) {
  let text;
  try { text = await readFile(join(root, rel), "utf8"); } catch { errors.push(`${rel}: listed but missing`); continue; }
  text.split(/\r?\n/).forEach((line, i) => {
    const m = line.match(PRICE);
    if (m) errors.push(`${rel}:${i + 1}: price pattern "${m[0]}"`);
  });
}
if (errors.length) {
  console.error(`No-prices check failed (${errors.length}):`);
  for (const e of errors.slice(0, 40)) console.error(`- ${e}`);
  process.exit(1);
}
console.log(`No-prices check passed (${files.length} files).`);
