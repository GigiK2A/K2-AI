"use client";

import { memo, useMemo } from "react";
import ReactMarkdown, { type Components } from "react-markdown";
import remarkGfm from "remark-gfm";
import { preparaTesto, type Citazione } from "@/lib/citazioni";

// HTML grezzo NON interpretato (react-markdown lo ignora senza rehype-raw); i link ammessi sono http(s), mailto e i nostri.
function urlSicuro(url: string): string {
  if (/^(https?:|mailto:|kbot-fonte:|kbot-pag:|#)/i.test(url)) return url;
  return "";
}

type Apri = (c: Citazione) => void;

function componenti(citazioni: Citazione[], apri?: Apri): Components {
  return {
    a({ href, children }) {
      if (href?.startsWith("kbot-fonte:")) {
        const c = citazioni[Number(href.slice(11))];
        if (!c) return <>{children}</>;
        const titolo = c.stato === "ok" ? "Apri il documento al passaggio citato"
          : c.stato === "pag" ? "Apri la pagina (passaggio esatto non localizzabile)" : "Apri il documento";
        return (
          <button
            type="button"
            title={titolo}
            data-testid="citazione"
            onClick={() => apri?.(c)}
            className="mx-0.5 inline-flex items-baseline rounded-md border border-[var(--teal)]/40 bg-[var(--teal-soft)] px-1.5 text-[11px] font-medium text-[var(--teal)] underline-offset-2 hover:underline"
          >
            {children}
          </button>
        );
      }
      if (href?.startsWith("kbot-pag:")) {
        return <span className="mx-0.5 rounded-md border border-[var(--line)] px-1 text-[11px] text-[var(--text-soft)]">{children}</span>;
      }
      return <a href={href} target="_blank" rel="noopener noreferrer" className="font-medium text-[var(--teal)] underline underline-offset-2">{children}</a>;
    },
    table: ({ children }) => (
      <div className="my-3 overflow-x-auto rounded-md border border-[var(--line)]">
        <table className="w-full border-collapse text-[14px]">{children}</table>
      </div>
    ),
    thead: ({ children }) => <thead className="bg-[var(--bg-2)] text-left">{children}</thead>,
    th: ({ children }) => <th className="border-b border-[var(--line-strong)] px-3 py-2 font-semibold">{children}</th>,
    td: ({ children }) => <td className="border-b border-[var(--line)] px-3 py-2 align-top">{children}</td>,
    h1: ({ children }) => <h3 className="font-doc mb-2 mt-5 text-xl font-semibold">{children}</h3>,
    h2: ({ children }) => <h3 className="font-doc mb-2 mt-5 text-lg font-semibold">{children}</h3>,
    h3: ({ children }) => <h4 className="mb-1.5 mt-4 text-base font-semibold">{children}</h4>,
    h4: ({ children }) => <h4 className="mb-1 mt-3 text-[15px] font-semibold">{children}</h4>,
    p: ({ children }) => <p className="my-2 first:mt-0 last:mb-0">{children}</p>,
    strong: ({ children }) => <strong className="font-semibold text-[var(--text-main)]">{children}</strong>,
    em: ({ children }) => <em className="italic">{children}</em>,
    ul: ({ children }) => <ul className="my-2 list-disc space-y-1 pl-6">{children}</ul>,
    ol: ({ children }) => <ol className="my-2 list-decimal space-y-1 pl-6">{children}</ol>,
    blockquote: ({ children }) => <blockquote className="my-3 border-l-2 border-[var(--teal)] pl-4 text-[var(--text-soft)]">{children}</blockquote>,
    hr: () => <hr className="my-4 border-[var(--line)]" />,
    pre: ({ children }) => <pre className="my-3 overflow-x-auto rounded-md bg-[var(--bg-2)] p-3 text-[13px] leading-6">{children}</pre>,
    code: ({ children, className }) => (
      className ? <code className={className}>{children}</code>
        : <code className="rounded bg-[var(--bg-2)] px-1 py-0.5 text-[13px]">{children}</code>
    ),
  };
}

/** Divide in blocchi (righe vuote) senza spezzare i blocchi di codice: i blocchi chiusi non si rifanno a ogni token. */
function blocchi(testo: string): string[] {
  const out: string[] = [];
  let corrente = "";
  let inCodice = false;
  for (const parte of testo.split(/(\n{2,})/)) {
    corrente += parte;
    inCodice = (corrente.match(/^```/gm)?.length ?? 0) % 2 === 1;
    if (!inCodice && !/^\n+$/.test(parte)) { out.push(corrente); corrente = ""; }
  }
  if (corrente) out.push(corrente);
  return out;
}

const Blocco = memo(function Blocco({ testo, citazioni, apri }: { testo: string; citazioni: Citazione[]; apri?: Apri }) {
  const comp = useMemo(() => componenti(citazioni, apri), [citazioni, apri]);
  return <ReactMarkdown remarkPlugins={[remarkGfm]} components={comp} urlTransform={urlSicuro}>{testo}</ReactMarkdown>;
});

export const Markdown = memo(function Markdown({ testo, onCitazione }: { testo: string; onCitazione?: Apri }) {
  const { testo: pronto, citazioni } = useMemo(() => preparaTesto(testo), [testo]);
  const parti = useMemo(() => blocchi(pronto), [pronto]);
  // le citazioni si indicizzano sul testo intero: ogni blocco riceve la stessa lista, l'indice nei link resta valido
  return <div className="text-[15px] leading-7 text-[var(--text-main)]">{parti.map((b, i) => <Blocco key={i} testo={b} citazioni={citazioni} apri={onCitazione} />)}</div>;
});
