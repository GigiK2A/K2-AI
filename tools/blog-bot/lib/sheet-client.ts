/**
 * Google Sheets client per la "Servizi" sheet del piano IG/Blog.
 *
 * Schema atteso (riga 1 = header):
 *
 *  A  Servizio
 *  B  Problema
 *  C  Risultato/KPI
 *  D  Agevolazione
 *  E  Stato                  ("da usare" | "usato")          ← IG
 *  F  Data                   (compilata da n8n IG)            ← IG
 *  G  blog_slug              (auto-compilata da blog bot)     ← BLOG
 *  H  blog_pubblicato        (data ISO compilata da blog bot) ← BLOG
 *  I  blog_url               (path /blog/<slug> da blog bot)  ← BLOG
 *  J  pillar_padre           (P01-P20, manuale)               ← shared
 *  K  pillar_url             (/suite-ai/<slug>.html, manuale) ← shared
 *
 * Il blog bot:
 * 1. Cerca la prima riga con Stato="da usare" AND blog_pubblicato vuoto
 * 2. Genera articolo, scrive blog_slug + blog_pubblicato + blog_url
 * 3. Lascia Stato="da usare" (sarà n8n IG a marcarlo "usato" la sera)
 */
import { google, sheets_v4 } from "googleapis";

export interface SheetRow {
  rowIndex: number; // 1-based
  servizio: string;
  problema: string;
  risultatoKpi: string;
  agevolazione: string;
  stato: string;
  data: string;
  blogSlug: string;
  blogPubblicato: string;
  blogUrl: string;
  pillarPadre: string;
  pillarUrl: string;
}

export class SheetClient {
  private sheets: sheets_v4.Sheets;
  constructor(private spreadsheetId: string, private sheetName = "Servizi") {
    const credentialsJson = process.env.GOOGLE_SHEETS_CREDENTIALS;
    if (!credentialsJson) {
      throw new Error("GOOGLE_SHEETS_CREDENTIALS env var missing");
    }
    const credentials = JSON.parse(credentialsJson);
    const auth = new google.auth.GoogleAuth({
      credentials,
      scopes: ["https://www.googleapis.com/auth/spreadsheets"],
    });
    this.sheets = google.sheets({ version: "v4", auth: auth as never });
  }

  async readAll(): Promise<SheetRow[]> {
    const res = await this.sheets.spreadsheets.values.get({
      spreadsheetId: this.spreadsheetId,
      range: `${this.sheetName}!A1:K1000`,
    });
    const values = res.data.values ?? [];
    // skip header row
    const rows: SheetRow[] = [];
    for (let i = 1; i < values.length; i++) {
      const r = values[i] ?? [];
      rows.push({
        rowIndex: i + 1,
        servizio: r[0] ?? "",
        problema: r[1] ?? "",
        risultatoKpi: r[2] ?? "",
        agevolazione: r[3] ?? "",
        stato: r[4] ?? "",
        data: r[5] ?? "",
        blogSlug: r[6] ?? "",
        blogPubblicato: r[7] ?? "",
        blogUrl: r[8] ?? "",
        pillarPadre: r[9] ?? "",
        pillarUrl: r[10] ?? "",
      });
    }
    return rows;
  }

  /**
   * Prossima riga da pubblicare sul blog:
   * - Stato = "da usare" (in coda anche per IG)
   * - blog_pubblicato = vuoto
   * Pubblichiamo il blog SOLO per righe che IG NON ha ancora pubblicato,
   * così IG (alle 18:00 stessa data) trova blog_pubblicato!=vuoto e include link.
   */
  async pickNextForBlog(): Promise<SheetRow | null> {
    const all = await this.readAll();
    return all.find(
      (r) =>
        r.servizio.trim().length > 0 &&
        r.stato.trim().toLowerCase() === "da usare" &&
        r.blogPubblicato.trim() === ""
    ) ?? null;
  }

  /**
   * Aggiorna le colonne blog_slug (G), blog_pubblicato (H), blog_url (I)
   * della riga specificata. Lascia Stato e Data invariati (le aggiorna n8n IG).
   */
  async markBlogPublished(
    rowIndex: number,
    slug: string,
    publishedAtIso: string,
    blogUrl: string
  ): Promise<void> {
    await this.sheets.spreadsheets.values.update({
      spreadsheetId: this.spreadsheetId,
      range: `${this.sheetName}!G${rowIndex}:I${rowIndex}`,
      valueInputOption: "RAW",
      requestBody: {
        values: [[slug, publishedAtIso, blogUrl]],
      },
    });
  }
}
