export function ReportCard({ title, value }: { title: string; value: string }) {
  return (
    <article className="rounded-xl border border-[var(--line)] bg-[rgba(255,255,255,0.02)] p-4">
      <p className="text-xs uppercase tracking-[0.12em] text-[var(--text-muted)]">{title}</p>
      <p className="mt-2 text-sm text-[var(--text-main)]">{value}</p>
    </article>
  );
}
