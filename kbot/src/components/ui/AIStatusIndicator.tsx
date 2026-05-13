import { cx } from "@/lib/utils";

export function AIStatusIndicator({ online, label = "AI Online" }: { online: boolean; label?: string }) {
  return (
    <span className="inline-flex items-center gap-2 text-xs text-[var(--text-soft)]">
      <span className={cx("h-2 w-2 rounded-full", online ? "bg-emerald-400" : "bg-red-400")} />
      {label}
    </span>
  );
}
