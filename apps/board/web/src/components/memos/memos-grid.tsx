"use client";

import { useMemo, useState } from "react";
import type { Memo } from "@/types/memo";
import type { Contact, Lead } from "@/types/lead";
import { extractAllTags } from "@/lib/memos";
import { MemosToolbar, type MemoSortKey } from "./memos-toolbar";
import { MemoCard } from "./memo-card";
import { MemoDrawer } from "./memo-drawer";

interface Props {
  initialMemos: Memo[];
  leads: Lead[];
  contacts: Contact[];
}

type DrawerState =
  | { mode: "edit"; memo: Memo }
  | { mode: "create" }
  | null;

export function MemosGrid({ initialMemos, leads, contacts }: Props) {
  const [memos, setMemos] = useState<Memo[]>(initialMemos);
  const [drawer, setDrawer] = useState<DrawerState>(null);
  const [search, setSearch] = useState("");
  const [selectedTags, setSelectedTags] = useState<Set<string>>(new Set());
  const [sort, setSort] = useState<MemoSortKey>("recent");

  const allTags = useMemo(() => extractAllTags(memos), [memos]);

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();
    return memos.filter((m) => {
      if (selectedTags.size > 0) {
        const has = m.tags.some((t) => selectedTags.has(t));
        if (!has) return false;
      }
      if (q) {
        const hay = [m.subject, m.body, ...m.tags].join(" ").toLowerCase();
        if (!hay.includes(q)) return false;
      }
      return true;
    });
  }, [memos, search, selectedTags]);

  const sorted = useMemo(() => {
    const list = [...filtered];
    if (sort === "subject") {
      list.sort((a, b) =>
        a.subject.localeCompare(b.subject, "it", { sensitivity: "base" }),
      );
    } else {
      list.sort(
        (a, b) =>
          new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime(),
      );
    }
    return list;
  }, [filtered, sort]);

  function toggleTag(t: string) {
    setSelectedTags((prev) => {
      const next = new Set(prev);
      if (next.has(t)) next.delete(t);
      else next.add(t);
      return next;
    });
  }

  function handleSaved(memo: Memo) {
    setMemos((curr) => {
      const idx = curr.findIndex((m) => m.id === memo.id);
      if (idx === -1) return [memo, ...curr];
      const next = [...curr];
      next[idx] = memo;
      return next;
    });
  }

  function handleDeleted(id: string) {
    setMemos((curr) => curr.filter((m) => m.id !== id));
  }

  return (
    <div className="flex flex-col gap-4">
      <MemosToolbar
        search={search}
        onSearch={setSearch}
        allTags={allTags}
        selectedTags={selectedTags}
        onToggleTag={toggleTag}
        sort={sort}
        onSort={setSort}
        onNewMemo={() => setDrawer({ mode: "create" })}
      />

      {sorted.length === 0 ? (
        <div className="flex flex-col items-center gap-3 rounded-xl border border-[color:var(--color-line)] bg-[color:var(--color-bg-soft)] px-6 py-10 text-center">
          <p className="font-display text-lg">Nessun memo.</p>
          <p className="text-sm text-[color:var(--color-text-soft)]">
            Crea il primo memo per iniziare a tenere traccia di pensieri e contesto.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
          {sorted.map((m) => (
            <MemoCard
              key={m.id}
              memo={m}
              onOpen={(memo) => setDrawer({ mode: "edit", memo })}
            />
          ))}
        </div>
      )}

      {drawer?.mode === "edit" && (
        <MemoDrawer
          mode="edit"
          open
          memo={drawer.memo}
          leads={leads}
          contacts={contacts}
          onClose={() => setDrawer(null)}
          onSaved={handleSaved}
          onDeleted={handleDeleted}
        />
      )}
      {drawer?.mode === "create" && (
        <MemoDrawer
          mode="create"
          open
          leads={leads}
          contacts={contacts}
          onClose={() => setDrawer(null)}
          onSaved={handleSaved}
        />
      )}
    </div>
  );
}
