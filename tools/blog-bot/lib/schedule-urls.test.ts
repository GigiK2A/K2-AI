/**
 * Guardia sugli URL della scaletta.
 *
 * Perché esiste: `schedule.json` riga 15 ha puntato per mesi a
 * `/suite-ai/diagnosi-strategica-pmi.html`, pagina mai esistita (il file è
 * `analisi-strategica-pmi.html`). Il difetto era invisibile perché la coda non
 * ci era ancora arrivata: al primo articolo su quella riga il bot avrebbe
 * pubblicato link interni verso un 404, e nessun validator lo avrebbe fermato.
 *
 * Questi test falliscono in CI *prima* della pubblicazione, non dopo.
 */
import { test } from "node:test";
import assert from "node:assert/strict";
import { existsSync, readFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

import { URL_TO_PILLAR, toPath } from "./pillar.js";

const __dirname = dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = resolve(__dirname, "..", "..", "..");
const SRC_DIR = join(REPO_ROOT, "kai-website", "src");
const SCHEDULE_PATH = resolve(__dirname, "..", "schedule.json");

/** Path del sito → file sorgente atteso. Null se il path non è mappabile. */
function sourceFileForPath(path: string): string | null {
  if (path === "/laboratorio") return join(SRC_DIR, "laboratorio.html");
  if (path.startsWith("/suite-ai/")) {
    return join(SRC_DIR, "suite-ai", path.replace("/suite-ai/", ""));
  }
  return null;
}

interface ScheduleRow {
  row: number;
  servizio: string;
  url: string;
}

function readRows(): ScheduleRow[] {
  return JSON.parse(readFileSync(SCHEDULE_PATH, "utf-8")).rows as ScheduleRow[];
}

test("URL_TO_PILLAR: ogni path mappato corrisponde a una pagina esistente", () => {
  const orfani: string[] = [];
  for (const path of Object.keys(URL_TO_PILLAR)) {
    const file = sourceFileForPath(path);
    if (!file) {
      orfani.push(`${path} (path non mappabile a un file sorgente)`);
      continue;
    }
    if (!existsSync(file)) orfani.push(`${path} → ${file} inesistente`);
  }
  assert.deepEqual(orfani, [], `pillar mappati su pagine inesistenti:\n${orfani.join("\n")}`);
});

test("schedule.json: ogni riga punta a una pagina esistente", () => {
  const rotti: string[] = [];
  for (const row of readRows()) {
    if (!row.url?.trim()) continue;
    const path = toPath(row.url);
    const file = sourceFileForPath(path);
    if (!file || !existsSync(file)) {
      rotti.push(`row ${row.row} (${row.servizio}) → ${path}`);
    }
  }
  assert.deepEqual(rotti, [], `righe con URL verso pagine inesistenti:\n${rotti.join("\n")}`);
});

test("schedule.json: ogni riga suite-ai è nota a URL_TO_PILLAR (niente fallback P00 silenzioso)", () => {
  const nonMappate: string[] = [];
  for (const row of readRows()) {
    if (!row.url?.trim()) continue;
    const path = toPath(row.url);
    if (!path.startsWith("/suite-ai/")) continue;
    if (!URL_TO_PILLAR[path]) nonMappate.push(`row ${row.row} (${row.servizio}) → ${path}`);
  }
  assert.deepEqual(
    nonMappate,
    [],
    `righe che finirebbero nel fallback P00 invece del pillar corretto:\n${nonMappate.join("\n")}`
  );
});
