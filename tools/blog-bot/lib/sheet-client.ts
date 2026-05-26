/**
 * Google Sheets client per la "Servizi" sheet del piano IG/Blog.
 *
 * Schema reale (riga 1 = header):
 *
 *  A  Servizio
 *  B  Categoria
 *  C  Descrizione                 (= Problema)
 *  D  Risultati_KPI
 *  E  Agevolazione
 *  F  URL                         (pillar URL o /laboratorio)
 *  G  Stato                       ("da usare" | "usato")          ← IG
 *  H  Data                        (compilata da n8n IG)            ← IG
 *  I  blog_slug                   (auto-compilata da blog bot)     ← BLOG
 *  J  blog_pubblicato             (data ISO compilata da blog bot) ← BLOG
 *  K  blog_url                    (path /blog/<slug> da blog bot)  ← BLOG
 *
 * Il blog bot:
 * 1. Cerca la prima riga con Stato="da usare" AND blog_pubblicato vuoto
 * 2. Genera articolo, scrive blog_slug + blog_pubblicato + blog_url
 * 3. Lascia Stato="da usare" (sarà n8n IG a marcarlo "usato" la sera)
 *
 * Il codice pillar (P01-P20) viene derivato dall'URL al runtime —
 * non serve una colonna pillar_padre nel foglio.
 */
import { google, sheets_v4 } from "googleapis";

export interface SheetRow {
  rowIndex: number; // 1-based
  servizio: string;
  categoria: string;
  descrizione: string;       // ex problema
  risultatoKpi: string;
  agevolazione: string;
  url: string;               // pillar url o /laboratorio
  stato: string;
  data: string;
  blogSlug: string;
  blogPubblicato: string;
  blogUrl: string;
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
        categoria: r[1] ?? "",
        descrizione: r[2] ?? "",
        risultatoKpi: r[3] ?? "",
        agevolazione: r[4] ?? "",
        url: r[5] ?? "",
        stato: r[6] ?? "",
        data: r[7] ?? "",
        blogSlug: r[8] ?? "",
        blogPubblicato: r[9] ?? "",
        blogUrl: r[10] ?? "",
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
   * Aggiorna le colonne blog_slug (I), blog_pubblicato (J), blog_url (K)
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
      range: `${this.sheetName}!I${rowIndex}:K${rowIndex}`,
      valueInputOption: "RAW",
      requestBody: {
        values: [[slug, publishedAtIso, blogUrl]],
      },
    });
  }
}
