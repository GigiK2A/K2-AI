"use client";

import { useMemo, useState } from "react";
import type { Approval, ApprovalKind, ApprovalStatus } from "@/types/approval";
import type { Contact, Lead } from "@/types/lead";
import { apiClient } from "@/lib/api-client";
import { ApprovalToolbar, type SortKey, type TabKey } from "./approval-toolbar";
import { ApprovalCard } from "./approval-card";
import { ApprovalDrawer } from "./approval-drawer";
import { ManualDraftButton } from "./manual-draft-button";

interface Props {
  initialApprovals: Approval[];
  leads: Lead[];
  // contacts kept for future use / props parity with sprint spec
  contacts: Contact[];
}

const DECIDED_STATUSES: ApprovalStatus[] = [
  "approved",
  "rejected",
  "edited_and_sent",
];

export function ApprovalsList({ initialApprovals, leads }: Props) {
  const [approvals, setApprovals] = useState<Approval[]>(initialApprovals);
  const [tab, setTab] = useState<TabKey>("pending");
  const [kinds, setKinds] = useState<Set<ApprovalKind>>(new Set());
  const [sort, setSort] = useState<SortKey>("newest");
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [drawer, setDrawer] = useState<Approval | null>(null);
  const [busyIds, setBusyIds] = useState<Set<string>>(new Set());
  const [bulkBusy, setBulkBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const leadsById = useMemo(() => {
    const m = new Map<string, Lead>();
    for (const l of leads) m.set(l.id, l);
    return m;
  }, [leads]);

  const pendingCount = useMemo(
    () => approvals.filter((a) => a.status === "pending").length,
    [approvals],
  );
  const decidedCount = useMemo(
    () => approvals.filter((a) => DECIDED_STATUSES.includes(a.status)).length,
    [approvals],
  );

  const visible = useMemo(() => {
    let list = approvals;
    if (tab === "pending") {
      list = list.filter((a) => a.status === "pending");
    } else if (tab === "decisi") {
      list = list.filter((a) => DECIDED_STATUSES.includes(a.status));
    }
    if (kinds.size > 0) {
      list = list.filter((a) => kinds.has(a.kind));
    }
    const sorted = [...list].sort((a, b) => {
      const tA = new Date(a.created_at).getTime();
      const tB = new Date(b.created_at).getTime();
      return sort === "newest" ? tB - tA : tA - tB;
    });
    return sorted;
  }, [approvals, tab, kinds, sort]);

  function setBusy(id: string, on: boolean) {
    setBusyIds((cur) => {
      const next = new Set(cur);
      if (on) next.add(id);
      else next.delete(id);
      return next;
    });
  }

  function applyUpdate(updated: Approval) {
    setApprovals((cur) =>
      cur.map((a) => (a.id === updated.id ? updated : a)),
    );
  }

  function applyDelete(id: string) {
    setApprovals((cur) => cur.filter((a) => a.id !== id));
    setSelected((cur) => {
      const next = new Set(cur);
      next.delete(id);
      return next;
    });
  }

  async function decide(approval: Approval, status: ApprovalStatus) {
    setBusy(approval.id, true);
    setError(null);
    // optimistic
    const optimistic: Approval = {
      ...approval,
      status,
      decided_at: new Date().toISOString(),
    };
    applyUpdate(optimistic);
    try {
      const saved = await apiClient<Approval>(
        `/api/approvals/${approval.id}`,
        {
          method: "PATCH",
          body: JSON.stringify({
            status,
            decided_at: new Date().toISOString(),
          }),
        },
      );
      applyUpdate(saved);
    } catch (err) {
      // revert
      applyUpdate(approval);
      setError(err instanceof Error ? err.message : "Errore di salvataggio");
    } finally {
      setBusy(approval.id, false);
    }
  }

  function toggleSelect(id: string) {
    setSelected((cur) => {
      const next = new Set(cur);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  async function bulkDecide(status: ApprovalStatus) {
    const ids = Array.from(selected).filter((id) => {
      const a = approvals.find((x) => x.id === id);
      return a?.status === "pending";
    });
    if (ids.length === 0) return;
    setBulkBusy(true);
    setError(null);

    const snapshot = approvals;
    // optimistic
    setApprovals((cur) =>
      cur.map((a) =>
        ids.includes(a.id)
          ? { ...a, status, decided_at: new Date().toISOString() }
          : a,
      ),
    );

    try {
      const results = await Promise.all(
        ids.map((id) =>
          apiClient<Approval>(`/api/approvals/${id}`, {
            method: "PATCH",
            body: JSON.stringify({
              status,
              decided_at: new Date().toISOString(),
            }),
          }),
        ),
      );
      setApprovals((cur) => {
        const byId = new Map(results.map((r) => [r.id, r]));
        return cur.map((a) => byId.get(a.id) ?? a);
      });
      setSelected(new Set());
    } catch (err) {
      setApprovals(snapshot);
      setError(err instanceof Error ? err.message : "Errore bulk");
    } finally {
      setBulkBusy(false);
    }
  }

  function handleCreated(created: Approval) {
    setApprovals((cur) => [created, ...cur]);
    setTab("pending");
  }

  const totalCount = approvals.length;
  const showBulk = tab === "pending" && pendingCount > 1;
  const emptyOnPending = tab === "pending" && visible.length === 0;
  const emptyOnDecisi = tab === "decisi" && visible.length === 0;
  const emptyOnTutti = tab === "tutti" && visible.length === 0;

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <p className="text-sm text-[color:var(--color-text-soft)]">
          <span className="font-semibold text-[color:var(--color-text)]">
            {pendingCount}
          </span>{" "}
          in attesa
        </p>
        <ManualDraftButton onCreated={handleCreated} />
      </div>

      <ApprovalToolbar
        tab={tab}
        onTabChange={(t) => {
          setTab(t);
          setSelected(new Set());
        }}
        kinds={kinds}
        onKindsChange={setKinds}
        sort={sort}
        onSortChange={setSort}
        pendingCount={pendingCount}
        decidedCount={decidedCount}
        totalCount={totalCount}
        selectedCount={selected.size}
        showBulk={showBulk}
        onBulkApprove={() => bulkDecide("approved")}
        onBulkReject={() => bulkDecide("rejected")}
        bulkBusy={bulkBusy}
      />

      {error && (
        <div className="rounded-lg border border-[color:var(--color-danger)]/50 bg-[color:var(--color-danger)]/10 px-3 py-2 text-xs text-[color:var(--color-danger)]">
          {error}
        </div>
      )}

      {emptyOnPending && (
        <EmptyState
          title="Nessuna approvazione in attesa."
          subtitle="Stai lavorando libero."
          tone="positive"
        />
      )}
      {emptyOnDecisi && (
        <EmptyState title="Nessuna decisione ancora." tone="muted" />
      )}
      {emptyOnTutti && (
        <EmptyState
          title="Giuseppina non ha ancora preparato niente da approvare."
          tone="muted"
          cta={<ManualDraftButton onCreated={handleCreated} variant="ghost" />}
        />
      )}

      {visible.length > 0 && (
        <div className="grid grid-cols-1 gap-3 lg:grid-cols-2">
          {visible.map((a) => (
            <ApprovalCard
              key={a.id}
              approval={a}
              lead={a.lead_id ? leadsById.get(a.lead_id) ?? null : null}
              selectable={showBulk}
              selected={selected.has(a.id)}
              onToggleSelect={toggleSelect}
              onOpen={(x) => setDrawer(x)}
              onApprove={(x) => decide(x, "approved")}
              onReject={(x) => decide(x, "rejected")}
              busy={busyIds.has(a.id) || bulkBusy}
            />
          ))}
        </div>
      )}

      <ApprovalDrawer
        open={!!drawer}
        approval={drawer}
        onClose={() => setDrawer(null)}
        onSaved={applyUpdate}
        onDeleted={applyDelete}
      />
    </div>
  );
}

function EmptyState({
  title,
  subtitle,
  tone,
  cta,
}: {
  title: string;
  subtitle?: string;
  tone: "positive" | "muted";
  cta?: React.ReactNode;
}) {
  return (
    <div
      className={
        "flex flex-col items-center gap-3 rounded-xl border px-6 py-10 text-center " +
        (tone === "positive"
          ? "border-[color:var(--color-teal)]/30 bg-[color:var(--color-teal)]/5"
          : "border-[color:var(--color-line)] bg-[color:var(--color-bg-soft)]")
      }
    >
      <p
        className={
          "font-display text-lg " +
          (tone === "positive"
            ? "text-[color:var(--color-teal)]"
            : "text-[color:var(--color-text)]")
        }
      >
        {title}
      </p>
      {subtitle && (
        <p className="text-sm text-[color:var(--color-text-soft)]">{subtitle}</p>
      )}
      {cta}
    </div>
  );
}
