// Controlli lato client sui file allegati (stessi limiti del backend: api/upload.py).
// Il backend resta l'autorità (whitelist, firma reale del contenuto, zip-bomb): qui si
// evita solo di spedire ciò che verrebbe rifiutato e si danno messaggi chiari.
export const ALLOWED_EXT = [
  ".pdf", ".xlsx", ".xls", ".csv", ".png", ".jpg", ".jpeg", ".gif", ".webp",
  ".docx", ".txt", ".md", ".json", ".xml",
];
export const ACCEPT_ATTR = ALLOWED_EXT.join(",");
export const MAX_FILE_BYTES = 20 * 1024 * 1024;
export const MAX_FILES = 10;
export const MAX_TOTAL_BYTES = 60 * 1024 * 1024;

export function validaFile(files: File[]): { ok: File[]; errori: string[] } {
  const ok: File[] = [];
  const errori: string[] = [];
  let totale = 0;
  for (const f of files) {
    const ext = f.name.includes(".") ? "." + f.name.split(".").pop()!.toLowerCase() : "";
    if (!ALLOWED_EXT.includes(ext)) {
      errori.push(`${f.name}: formato non supportato (accetto PDF, Word, Excel, CSV, testo e immagini).`);
    } else if (f.size === 0) {
      errori.push(`${f.name}: il file è vuoto.`);
    } else if (f.size > MAX_FILE_BYTES) {
      errori.push(`${f.name}: supera i 20 MB.`);
    } else if (ok.length >= MAX_FILES) {
      errori.push(`${f.name}: massimo ${MAX_FILES} file per volta.`);
    } else if (totale + f.size > MAX_TOTAL_BYTES) {
      errori.push(`${f.name}: superato il totale di 60 MB per volta.`);
    } else {
      ok.push(f);
      totale += f.size;
    }
  }
  return { ok, errori };
}

export function haFile(e: DragEvent): boolean {
  return Array.from(e.dataTransfer?.types ?? []).includes("Files");
}
