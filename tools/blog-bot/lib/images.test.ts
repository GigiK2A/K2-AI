import { test } from "node:test";
import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import { mkdtempSync, existsSync, statSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

import { findImageMagick, optimizeArticleImages } from "./images.js";

const im = findImageMagick();

function size(file: string): string {
  const bin = im === "magick" ? ["magick", "identify"] : ["identify"];
  return execFileSync(bin[0] as string, [...bin.slice(1), "-format", "%wx%h", file]).toString();
}

function makePngs(dir: string, slug: string) {
  const mk = (name: string, geom: string) => {
    const p = join(dir, name);
    execFileSync(im!, ["-size", geom, "gradient:#334-#cdf", p]);
    return p;
  };
  return {
    cover: mk(`${slug}-cover.png`, "1536x1024"),
    inline1: mk(`${slug}-inline-1.png`, "1024x1024"),
    inline2: mk(`${slug}-inline-2.png`, "1024x1024"),
  };
}

test("images: WebP (cover 1280 px) + JPG og 1200x630, PNG di lavoro rimossi", { skip: !im }, () => {
  const dir = mkdtempSync(join(tmpdir(), "bb-img-"));
  const ogDir = mkdtempSync(join(tmpdir(), "bb-og-"));
  const png = makePngs(dir, "prova");
  const r = optimizeArticleImages("prova", dir, ogDir, png);
  if (r.cover.endsWith(".png")) return; // ImageMagick senza WebP: ripiego già coperto dal test sotto
  assert.equal(r.cover, "prova-cover.webp");
  assert.equal(size(join(dir, r.cover)), "1280x853");
  assert.deepEqual(r.coverSize, { width: 1280, height: 853 });
  assert.equal(size(join(dir, r.inline1)), "1024x1024");
  assert.equal(r.og, "prova.jpg");
  assert.equal(size(join(ogDir, "prova.jpg")), "1200x630");
  assert.ok(statSync(join(ogDir, "prova.jpg")).size < 300 * 1024);
  assert.ok(!existsSync(png.cover) && !existsSync(png.inline1));
});

test("images: senza ImageMagick restano i PNG e og = null (nessun file mancante)", { skip: !im }, () => {
  const dir = mkdtempSync(join(tmpdir(), "bb-img-"));
  const ogDir = mkdtempSync(join(tmpdir(), "bb-og-"));
  const png = makePngs(dir, "prova2");
  const oldPath = process.env.PATH;
  process.env.PATH = "";
  try {
    const r = optimizeArticleImages("prova2", dir, ogDir, png);
    assert.equal(r.cover, "prova2-cover.png");
    assert.equal(r.og, null);
    assert.deepEqual(r.coverSize, { width: 1536, height: 1024 });
    assert.ok(existsSync(png.cover));
  } finally {
    process.env.PATH = oldPath;
  }
});
