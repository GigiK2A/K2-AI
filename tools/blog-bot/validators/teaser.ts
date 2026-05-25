/**
 * Teaser validator: assicura che articolo NON sveli soluzione implementabile.
 * Combina check strutturali (no <pre>, no <ol> lunghi) + check LLM self-judge.
 */
import * as cheerio from "cheerio";
import Anthropic from "@anthropic-ai/sdk";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const TEASER_CHECK_PROMPT = readFileSync(
  join(__dirname, "..", "prompts", "teaser-check.md"),
  "utf-8"
);

const SCREENSHOT_KEYWORDS = ["screenshot", "dashboard-config", "settings-page"];

export interface TeaserCheckResult {
  ok: boolean;
  errors: string[];
  warnings: string[];
  llmJudgment?: {
    couldImplementAlone: boolean;
    reason: string;
    leakedDetails: string[];
  };
}

export async function validateTeaser(
  fullHtml: string,
  anthropic: Anthropic
): Promise<TeaserCheckResult> {
  const errors: string[] = [];
  const warnings: string[] = [];
  const $ = cheerio.load(fullHtml);

  // Structural: no long code blocks
  $("pre, code").each((_, el) => {
    const txt = $(el).text().trim();
    if (txt.length > 30) {
      errors.push(`code block with ${txt.length} chars (max 30): "${txt.slice(0, 50)}..."`);
    }
  });

  // Structural: no long <ol>
  $("ol").each((_, el) => {
    const count = $(el).find("> li").length;
    if (count > 5) {
      errors.push(`<ol> with ${count} items (max 5) — suggests a step-by-step tutorial`);
    }
  });

  // Structural: no <img> filenames hinting at setup screenshots
  $("img").each((_, el) => {
    const src = $(el).attr("src") ?? "";
    if (SCREENSHOT_KEYWORDS.some((kw) => src.toLowerCase().includes(kw))) {
      warnings.push(`<img src="${src}" looks like a configuration screenshot`);
    }
  });

  // LLM judge
  const article = $("article, main").html() || $("body").html() || "";
  try {
    const resp = await anthropic.messages.create({
      model: "claude-haiku-4-5",
      max_tokens: 600,
      system: TEASER_CHECK_PROMPT,
      messages: [{ role: "user", content: article.slice(0, 15000) }],
    });
    const text = resp.content
      .filter((b): b is Anthropic.TextBlock => b.type === "text")
      .map((b) => b.text)
      .join("");
    // Extract JSON
    const match = text.match(/\{[\s\S]*\}/);
    if (match) {
      const parsed = JSON.parse(match[0]) as {
        could_implement_alone: boolean;
        reason: string;
        leaked_details?: string[];
      };
      const judgment = {
        couldImplementAlone: parsed.could_implement_alone,
        reason: parsed.reason,
        leakedDetails: parsed.leaked_details ?? [],
      };
      if (judgment.couldImplementAlone) {
        errors.push(`LLM teaser-check FAIL: ${judgment.reason}`);
        for (const d of judgment.leakedDetails) {
          errors.push(`  leaked: ${d}`);
        }
      }
      return { ok: errors.length === 0, errors, warnings, llmJudgment: judgment };
    }
  } catch (e) {
    warnings.push(`teaser LLM check failed: ${(e as Error).message}`);
  }

  return { ok: errors.length === 0, errors, warnings };
}
