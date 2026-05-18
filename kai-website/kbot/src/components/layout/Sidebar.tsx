import { AnimatePresence, motion } from "framer-motion";
import { PanelLeftClose, Plus } from "lucide-react";
import { Conversation, Mode } from "@/types/chat";
import { AIStatusIndicator } from "@/components/ui/AIStatusIndicator";
import { ModeSwitcher } from "@/components/chat/ModeSwitcher";
import { ConversationList } from "@/components/layout/ConversationList";

export function Sidebar({
  open,
  mode,
  onMode,
  conversations,
  activeId,
  onSelect,
  onNew,
  onDelete,
  onRename,
  onClose,
}: {
  open: boolean;
  mode: Mode;
  onMode: (m: Mode) => void;
  conversations: Conversation[];
  activeId: string;
  onSelect: (id: string) => void;
  onNew: () => void;
  onDelete?: (id: string) => void;
  onRename?: (id: string, title: string) => void;
  onClose: () => void;
}) {
  return (
    <AnimatePresence>
      {open && (
        <motion.aside
          initial={{ x: -30, opacity: 0 }}
          animate={{ x: 0, opacity: 1 }}
          exit={{ x: -20, opacity: 0 }}
          className="k2-panel fixed inset-y-0 left-0 z-40 w-[290px] border-r p-4 lg:static lg:block"
        >
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xl font-semibold tracking-tight">K2 AI</p>
              <AIStatusIndicator online label="Stato AI: Online" />
            </div>
            <button onClick={onClose} className="rounded-lg border border-[var(--line)] p-2 lg:hidden">
              <PanelLeftClose size={16} />
            </button>
          </div>

          <div className="mt-6 space-y-5">
            <div>
              <p className="mb-2 text-xs uppercase tracking-[0.14em] text-[var(--text-muted)]">Modalita</p>
              <ModeSwitcher mode={mode} onChange={onMode} />
            </div>

            <div>
              <button onClick={onNew} className="flex w-full items-center justify-center gap-2 rounded-xl border border-[var(--line)] px-3 py-2 text-sm hover:border-[var(--line-strong)]">
                <Plus size={15} /> Nuova chat
              </button>
            </div>

            <div>
              <p className="mb-2 text-xs uppercase tracking-[0.14em] text-[var(--text-muted)]">Cronologia</p>
              <ConversationList conversations={conversations} activeId={activeId} onSelect={onSelect} onDelete={onDelete} onRename={onRename} />
            </div>
          </div>

          <div className="absolute inset-x-4 bottom-4 rounded-xl border border-[var(--line)] p-3 text-xs text-[var(--text-soft)]">
            <p className="font-medium text-white">Account K2-AI</p>
            <p>Consulenza enterprise attiva</p>
          </div>
        </motion.aside>
      )}
    </AnimatePresence>
  );
}
