/**
 * Image generation per articolo blog via OpenAI gpt-image-2 (model id: gpt-image-2, API da mag 2026).
 *
 * Stile foto realistica ufficio (scelto da Luca): luce naturale,
 * shallow depth of field, no testo visibile su schermi, no loghi.
 *
 * Per ogni articolo genera:
 * - 1 cover orizzontale 1536x1024 (pagina: WebP max 1280 px; social: JPG 1200x630)
 * - 2 inline quadrate 1024x1024 (WebP; tra sezione 02-03 e tra sezione 04-05)
 *
 * Costo per immagine variabile con gpt-image-2 (quality medium, stesse size
 * 1536x1024 / 1024x1024, entrambe supportate; risposta b64_json di default).
 */
import OpenAI from "openai";
import { writeFileSync, mkdirSync, existsSync, unlinkSync, statSync } from "node:fs";
import { execFileSync } from "node:child_process";
import { join } from "node:path";

export interface ImageScenes {
  cover: string;
  inline1: string;
  inline2: string;
}

export interface ImageSize {
  width: number;
  height: number;
}

export interface GeneratedImages {
  /** Nomi file in blog/img/ (WebP se la conversione è disponibile, altrimenti PNG). */
  cover: string;
  inline1: string;
  inline2: string;
  /** Dimensioni reali dei file scritti, per width/height nel markup. */
  coverSize: ImageSize;
  inlineSize: ImageSize;
  /**
   * Nome del JPG 1200x630 in public/blog/og/ (es. "slug.jpg"), usato da
   * og:image, twitter:image e JSON-LD. null se la conversione non è disponibile:
   * il template ripiega allora su /assets/og-home.png (un file che esiste).
   */
  og: string | null;
}

/** Larghezza massima della cover in pagina (come gli articoli già pubblicati). */
const COVER_MAX_WIDTH = 1280;
const OG_WIDTH = 1200;
const OG_HEIGHT = 630;

/** Cerca ImageMagick (7: magick, 6: convert). Ritorna null se non c'è. */
export function findImageMagick(): string | null {
  for (const cmd of ["magick", "convert"]) {
    try {
      execFileSync(cmd, ["-version"], { stdio: "ignore" });
      return cmd;
    } catch {
      /* prossimo */
    }
  }
  return null;
}

function nonEmpty(path: string): boolean {
  return existsSync(path) && statSync(path).size > 0;
}

/** PNG -> WebP q80 (cover ridimensionata a COVER_MAX_WIDTH). false se fallisce. */
function toWebp(im: string, src: string, dest: string, maxWidth?: number): boolean {
  try {
    const args = [src];
    if (maxWidth) args.push("-resize", `${maxWidth}x>`);
    args.push("-quality", "80", "-define", "webp:method=6", dest);
    execFileSync(im, args, { stdio: "ignore" });
    return nonEmpty(dest);
  } catch {
    return false;
  }
}

/**
 * Cover 3:2 -> JPG 1200x630 per le anteprime social (crop leggermente sopra il
 * centro, come per gli articoli già pubblicati). false se fallisce.
 */
function toOgJpeg(im: string, src: string, dest: string): boolean {
  try {
    const scaledHeight = Math.round((OG_WIDTH * 1024) / 1536); // cover 1536x1024
    const offsetY = Math.max(0, Math.round((scaledHeight - OG_HEIGHT) * 0.35));
    execFileSync(
      im,
      [
        src,
        "-resize", `${OG_WIDTH}x`,
        "-crop", `${OG_WIDTH}x${OG_HEIGHT}+0+${offsetY}`,
        "+repage",
        "-quality", "82",
        "-interlace", "Plane",
        dest,
      ],
      { stdio: "ignore" }
    );
    return nonEmpty(dest);
  } catch {
    return false;
  }
}

const STYLE_SUFFIX = [
  "Realistic editorial photography in an Italian SME office.",
  "Soft natural window light, late afternoon warm tones, shallow depth of field.",
  "Muted color grading, documentary feel, restrained composition.",
  "Critical constraints: no visible legible text on monitors or paper, no logos,",
  "no readable signs, no brand names. People (if present) shown from angles that",
  "avoid identifiable faces. No stock-photo posing, no exaggerated smiles.",
].join(" ");

export function createOpenAIClient(): OpenAI {
  const apiKey = process.env.OPENAI_API_KEY;
  if (!apiKey) throw new Error("OPENAI_API_KEY env var missing");
  return new OpenAI({ apiKey, timeout: 180_000 });
}

async function generateOne(
  client: OpenAI,
  scene: string,
  size: "1024x1024" | "1536x1024"
): Promise<Buffer> {
  const prompt = `${scene}\n\n${STYLE_SUFFIX}`;
  const resp = await client.images.generate({
    model: "gpt-image-2",
    prompt,
    size,
    quality: "medium",
    n: 1,
  });
  const b64 = resp.data?.[0]?.b64_json;
  if (!b64) throw new Error("OpenAI image API returned no b64_json");
  return Buffer.from(b64, "base64");
}

export async function generateArticleImages(
  client: OpenAI,
  scenes: ImageScenes,
  slug: string,
  imgDir: string,
  ogDir: string
): Promise<GeneratedImages> {
  if (!existsSync(imgDir)) mkdirSync(imgDir, { recursive: true });
  if (!existsSync(ogDir)) mkdirSync(ogDir, { recursive: true });

  // Sequenziale per rate-limit safety e log leggibile. I PNG grezzi vengono
  // scritti come file di lavoro e poi convertiti (vedi sotto).
  console.log("[images] generating cover...");
  const coverBuf = await generateOne(client, scenes.cover, "1536x1024");
  const coverPng = join(imgDir, `${slug}-cover.png`);
  writeFileSync(coverPng, coverBuf);

  console.log("[images] generating inline 1...");
  const inline1Buf = await generateOne(client, scenes.inline1, "1024x1024");
  const inline1Png = join(imgDir, `${slug}-inline-1.png`);
  writeFileSync(inline1Png, inline1Buf);

  console.log("[images] generating inline 2...");
  const inline2Buf = await generateOne(client, scenes.inline2, "1024x1024");
  const inline2Png = join(imgDir, `${slug}-inline-2.png`);
  writeFileSync(inline2Png, inline2Buf);

  return optimizeArticleImages(slug, imgDir, ogDir, {
    cover: coverPng,
    inline1: inline1Png,
    inline2: inline2Png,
  });
}

/**
 * Converte i PNG grezzi: cover e inline in WebP (cover max 1280 px), og in JPG
 * 1200x630. Servono ImageMagick con supporto WebP. Se manca (o una conversione
 * fallisce) si ripiega, senza bloccare la pubblicazione, su PNG per la pagina e
 * su /assets/og-home.png per le anteprime social (og = null).
 * Esportata per poterla provare senza chiamare l'API immagini.
 */
export function optimizeArticleImages(
  slug: string,
  imgDir: string,
  ogDir: string,
  png: { cover: string; inline1: string; inline2: string }
): GeneratedImages {
  const fallback: GeneratedImages = {
    cover: `${slug}-cover.png`,
    inline1: `${slug}-inline-1.png`,
    inline2: `${slug}-inline-2.png`,
    coverSize: { width: 1536, height: 1024 },
    inlineSize: { width: 1024, height: 1024 },
    og: null,
  };
  const im = findImageMagick();
  if (!im) {
    console.warn("[images] ImageMagick non trovato: restano PNG e og:image di ripiego (og-home).");
    return fallback;
  }

  const coverWebp = join(imgDir, `${slug}-cover.webp`);
  const in1Webp = join(imgDir, `${slug}-inline-1.webp`);
  const in2Webp = join(imgDir, `${slug}-inline-2.webp`);
  const ogJpg = join(ogDir, `${slug}.jpg`);

  const webpOk =
    toWebp(im, png.cover, coverWebp, COVER_MAX_WIDTH) &&
    toWebp(im, png.inline1, in1Webp) &&
    toWebp(im, png.inline2, in2Webp);
  const ogOk = toOgJpeg(im, png.cover, ogJpg);

  if (!ogOk) console.warn("[images] og JPG non creato: og:image di ripiego (og-home).");

  if (!webpOk) {
    console.warn("[images] conversione WebP fallita: restano PNG per la pagina.");
    for (const f of [coverWebp, in1Webp, in2Webp]) if (existsSync(f)) unlinkSync(f);
    return { ...fallback, og: ogOk ? `${slug}.jpg` : null };
  }

  // WebP ok: i PNG di lavoro non servono più (non vanno committati).
  for (const f of [png.cover, png.inline1, png.inline2]) if (existsSync(f)) unlinkSync(f);
  return {
    cover: `${slug}-cover.webp`,
    inline1: `${slug}-inline-1.webp`,
    inline2: `${slug}-inline-2.webp`,
    coverSize: { width: COVER_MAX_WIDTH, height: Math.round((COVER_MAX_WIDTH * 1024) / 1536) },
    inlineSize: { width: 1024, height: 1024 },
    og: ogOk ? `${slug}.jpg` : null,
  };
}
