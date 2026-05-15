import type { Memo } from "@/types/memo";

export function extractAllTags(memos: Memo[]): string[] {
  const set = new Set<string>();
  for (const m of memos) {
    for (const t of m.tags) {
      const v = t.trim();
      if (v) set.add(v);
    }
  }
  return Array.from(set).sort((a, b) => a.localeCompare(b, "it"));
}

export function parseTagsInput(value: string): string[] {
  return value
    .split(",")
    .map((s) => s.trim())
    .filter(Boolean);
}

export function previewBody(body: string, maxLines = 3, maxChars = 220): string {
  const lines = body.split(/\r?\n/).slice(0, maxLines).join("\n");
  if (lines.length <= maxChars) return lines;
  return lines.slice(0, maxChars).trimEnd() + "…";
}
