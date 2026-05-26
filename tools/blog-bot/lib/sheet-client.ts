/**
 * Schedule client: source of truth è un JSON committato nel repo
 * (`tools/blog-bot/schedule.json`), NON Google Sheets API.
 *
 * Motivo: l'org Google ha policy `iam.disableServiceAccountKeyCreation`
 * che blocca la creazione di chiavi service account → non possiamo
 * autenticare il bot via API. Soluzione pragmatica: scaletta in repo,
 * stato versionato in git.
 *
 * n8n IG può continuare a leggere lo stesso file via raw URL:
 *   https://raw.githubusercontent.com/GigiK2A/K2-AI/main/tools/blog-bot/schedule.json
 *
 * Schema di schedule.json:
 *   {
 *     "version": 1,
 *     "rows": [
 *       {
 *         "row": number,                  riga originale (debug)
 *         "servizio": string,
 *         "categoria": string,
 *         "descrizione": string,
 *         "risultati_kpi": string,
 *         "agevolazione": string,
 *         "url": string,                  pillar URL o /laboratorio
 *         "stato_ig": "da usare" | "usato",
 *         "data_ig": string,              ISO YYYY-MM-DD
 *         "blog_slug": string,
 *         "blog_pubblicato": string,      ISO YYYY-MM-DD
 *         "blog_url": string              path /blog/<slug>
 *       }, ...
 *     ]
 *   }
 */
import { readFileSync, writeFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const SCHEDULE_PATH = resolve(__dirname, "..", "schedule.json");

export interface ScheduleRow {
  row: number;
  servizio: string;
  categoria: string;
  descrizione: string;
  risultati_kpi: string;
  agevolazione: string;
  url: string;
  stato_ig: string;
  data_ig: string;
  blog_slug: string;
  blog_pubblicato: string;
  blog_url: string;
}

interface Schedule {
  version: number;
  updated_at?: string;
  description?: string;
  rows: ScheduleRow[];
}

// Alias retro-compatibile col vecchio nome usato nell'orchestrator.
export type SheetRow = ScheduleRow & {
  rowIndex: number;
  descrizioneAlias?: string;
};

export class SheetClient {
  private schedulePath: string;

  constructor(_spreadsheetId?: string, _sheetName?: string) {
    // I parametri sono ignorati: usiamo schedule.json nel repo.
    this.schedulePath = SCHEDULE_PATH;
  }

  private read(): Schedule {
    const raw = readFileSync(this.schedulePath, "utf-8");
    return JSON.parse(raw) as Schedule;
  }

  private write(s: Schedule): void {
    writeFileSync(this.schedulePath, JSON.stringify(s, null, 2) + "\n", "utf-8");
  }

  async readAll(): Promise<SheetRow[]> {
    const sch = this.read();
    return sch.rows.map((r) => ({
      ...r,
      rowIndex: r.row,
    }));
  }

  /**
   * Prossima riga da pubblicare sul blog:
   * - stato_ig = "da usare" (in coda anche per IG)
   * - blog_pubblicato = vuoto
   */
  async pickNextForBlog(): Promise<SheetRow | null> {
    const all = await this.readAll();
    return (
      all.find(
        (r) =>
          r.servizio.trim().length > 0 &&
          r.stato_ig.trim().toLowerCase() === "da usare" &&
          r.blog_pubblicato.trim() === ""
      ) ?? null
    );
  }

  /**
   * Marca riga come pubblicata sul blog. Scrive blog_slug + blog_pubblicato
   * + blog_url. Lo stato IG resta "da usare" (lo gestirà n8n IG la sera).
   */
  async markBlogPublished(
    rowIndex: number,
    slug: string,
    publishedAtIso: string,
    blogUrl: string
  ): Promise<void> {
    const sch = this.read();
    const target = sch.rows.find((r) => r.row === rowIndex);
    if (!target) throw new Error(`row ${rowIndex} not found in schedule.json`);
    target.blog_slug = slug;
    target.blog_pubblicato = publishedAtIso;
    target.blog_url = blogUrl;
    sch.updated_at = publishedAtIso;
    this.write(sch);
  }
}
