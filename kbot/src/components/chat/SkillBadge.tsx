import { motion } from "framer-motion";

export function SkillBadge({ name }: { name: string }) {
  return (
    <motion.span
      initial={{ opacity: 0, y: 4 }}
      animate={{ opacity: 1, y: 0 }}
      className="inline-flex items-center rounded-full border border-[var(--line)] bg-[rgba(255,255,255,0.02)] px-2.5 py-1 text-[11px] text-[var(--text-soft)]"
    >
      {name}
    </motion.span>
  );
}
