import { test } from "node:test";
import assert from "node:assert/strict";

import { toPath, resolvePillarFromUrl } from "./pillar.js";

test("toPath: URL assoluto → pathname", () => {
  assert.equal(
    toPath("https://www.k2-ai.it/suite-ai/automazioni-amministrative.html"),
    "/suite-ai/automazioni-amministrative.html"
  );
});

test("toPath: path relativo invariato", () => {
  assert.equal(toPath("/laboratorio"), "/laboratorio");
});

test("toPath: senza leading slash → aggiunge slash", () => {
  assert.equal(toPath("suite-ai/x.html"), "/suite-ai/x.html");
});

test("toPath: rimuove trailing slash (non root)", () => {
  assert.equal(toPath("https://www.k2-ai.it/laboratorio/"), "/laboratorio");
});

test("resolvePillarFromUrl: URL assoluto suite-ai matcha il pillar corretto", () => {
  const r = resolvePillarFromUrl(
    "https://www.k2-ai.it/suite-ai/automazioni-amministrative.html"
  );
  assert.equal(r.code, "P02");
  assert.equal(r.label, "Automazioni amministrative");
  // url è l'href canonico per gli internal link: senza estensione .html
  assert.equal(r.url, "/suite-ai/automazioni-amministrative");
});

test("resolvePillarFromUrl: agenti email & CRM → P01", () => {
  assert.equal(
    resolvePillarFromUrl("https://www.k2-ai.it/suite-ai/agenti-email-crm.html").code,
    "P01"
  );
});

test("resolvePillarFromUrl: laboratorio assoluto → LAB", () => {
  const r = resolvePillarFromUrl("https://www.k2-ai.it/laboratorio");
  assert.equal(r.code, "LAB");
  assert.equal(r.url, "/laboratorio");
});

test("resolvePillarFromUrl: path relativo matcha (retro-compat)", () => {
  assert.equal(
    resolvePillarFromUrl("/suite-ai/ai-legale-contratti.html").code,
    "P03"
  );
});

test("resolvePillarFromUrl: URL sconosciuto → fallback P00", () => {
  const r = resolvePillarFromUrl("https://www.k2-ai.it/pagina-inesistente.html");
  assert.equal(r.code, "P00");
  assert.equal(r.url, "/suite-ai");
});
