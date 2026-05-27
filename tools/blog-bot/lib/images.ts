/**
 * Image generation per articolo blog via OpenAI gpt-image-1.
 *
 * Stile foto realistica ufficio (scelto da Luca): luce naturale,
 * shallow depth of field, no testo visibile su schermi, no loghi.
 *
 * Per ogni articolo genera:
 * - 1 cover orizzontale 1536x1024 (anche og:image)
 * - 2 inline quadrate 1024x1024 (tra sezione 02-03 e tra sezione 04-05)
 *
 * Costo medio: ~$0.15/articolo (medium quality).
 */
import OpenAI from "openai";
import { writeFileSync, mkdirSync, existsSync } from "node:fs";
import { join } from "node:path";

export interface ImageScenes {
  cover: string;
  inline1: string;
  inline2: string;
}

export interface GeneratedImages {
  cover: string;
  inline1: string;
  inline2: string;
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
    model: "gpt-image-1",
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
  imgDir: string
): Promise<GeneratedImages> {
  if (!existsSync(imgDir)) mkdirSync(imgDir, { recursive: true });

  // Sequenziale per rate-limit safety e log leggibile.
  console.log("[images] generating cover...");
  const coverBuf = await generateOne(client, scenes.cover, "1536x1024");
  const coverName = `${slug}-cover.png`;
  writeFileSync(join(imgDir, coverName), coverBuf);

  console.log("[images] generating inline 1...");
  const inline1Buf = await generateOne(client, scenes.inline1, "1024x1024");
  const inline1Name = `${slug}-inline-1.png`;
  writeFileSync(join(imgDir, inline1Name), inline1Buf);

  console.log("[images] generating inline 2...");
  const inline2Buf = await generateOne(client, scenes.inline2, "1024x1024");
  const inline2Name = `${slug}-inline-2.png`;
  writeFileSync(join(imgDir, inline2Name), inline2Buf);

  return { cover: coverName, inline1: inline1Name, inline2: inline2Name };
}
