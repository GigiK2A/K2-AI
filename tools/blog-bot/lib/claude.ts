/**
 * Anthropic client wrapper per draft + revise + teaser-check.
 */
import Anthropic from "@anthropic-ai/sdk";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const DRAFT_PROMPT = readFileSync(
  join(__dirname, "..", "prompts", "article-draft.md"),
  "utf-8"
);
const REVISE_PROMPT = readFileSync(
  join(__dirname, "..", "prompts", "article-revise.md"),
  "utf-8"
);

export interface ArticlePieces {
  bodyHtml: string;
  meta: {
    title_h1: string;
    title_tag: string;
    meta_description: string;
    lede: string;
    slug: string;
    faq_questions: { q: string; a: string }[];
  };
}

export interface BriefInput {
  servizio: string;
  problema: string;
  risultato_kpi: string;
  agevolazione: string;
  pillar_padre: string;
  pillar_url: string;
}

export function createClient(): Anthropic {
  const apiKey = process.env.ANTHROPIC_API_KEY;
  if (!apiKey) throw new Error("ANTHROPIC_API_KEY env var missing");
  return new Anthropic({ apiKey, timeout: 120_000 });
}

function parsePieces(rawText: string): ArticlePieces {
  const metaMatch = rawText.match(/<!--META\s*([\s\S]+?)\s*-->/);
  if (!metaMatch) {
    throw new Error("model output missing <!--META ... --> block");
  }
  const metaJson = metaMatch[1].trim();
  let meta: ArticlePieces["meta"];
  try {
    meta = JSON.parse(metaJson);
  } catch (e) {
    throw new Error(`META block invalid JSON: ${(e as Error).message}`);
  }
  const bodyHtml = rawText.replace(metaMatch[0], "").trim();
  return { bodyHtml, meta };
}

export async function generateDraft(
  client: Anthropic,
  brief: BriefInput
): Promise<ArticlePieces> {
  const userMsg = `Brief per l'articolo:

\`\`\`json
${JSON.stringify(brief, null, 2)}
\`\`\`

Genera l'articolo seguendo il sistema indicato. Output: HTML body + blocco META.`;

  const resp = await client.messages.create({
    model: "claude-sonnet-4-6",
    max_tokens: 8000,
    system: DRAFT_PROMPT,
    messages: [{ role: "user", content: userMsg }],
  });
  const text = resp.content
    .filter((b): b is Anthropic.TextBlock => b.type === "text")
    .map((b) => b.text)
    .join("");
  return parsePieces(text);
}

export async function reviseArticle(
  client: Anthropic,
  draft: ArticlePieces
): Promise<ArticlePieces> {
  const reconstructed = `${draft.bodyHtml}\n\n<!--META\n${JSON.stringify(draft.meta, null, 2)}\n-->`;
  const resp = await client.messages.create({
    model: "claude-haiku-4-5",
    max_tokens: 8000,
    system: REVISE_PROMPT,
    messages: [{ role: "user", content: reconstructed }],
  });
  const text = resp.content
    .filter((b): b is Anthropic.TextBlock => b.type === "text")
    .map((b) => b.text)
    .join("");
  return parsePieces(text);
}
