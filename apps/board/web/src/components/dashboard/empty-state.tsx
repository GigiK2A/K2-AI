import Link from "next/link";
import { Card } from "@/components/ui/card";
import { ArrowRight, UserPlus, FileText, CalendarCheck } from "lucide-react";

const STEPS = [
  { href: "/pipeline", label: "Aggiungi un lead", Icon: UserPlus },
  { href: "/memos", label: "Crea un memo", Icon: FileText },
  { href: "/calendario", label: "Sincronizza il calendario", Icon: CalendarCheck },
];

export function EmptyState({ username }: { username: string }) {
  return (
    <Card className="flex flex-col gap-6 p-8">
      <div>
        <h2 className="font-display text-2xl">Tutto pulito, {username}.</h2>
        <p className="mt-2 text-sm text-[color:var(--color-text-soft)]">
          Nessuna urgenza in coda. Buon momento per impostare i prossimi passi.
        </p>
      </div>
      <ul className="grid gap-2 sm:grid-cols-3">
        {STEPS.map(({ href, label, Icon }) => (
          <li key={href}>
            <Link
              href={href}
              className="group flex items-center justify-between gap-3 rounded-xl border border-[color:var(--color-line)] bg-[color:var(--color-bg-elevated)] px-4 py-3 transition-colors hover:border-[color:var(--color-teal)]"
            >
              <span className="flex items-center gap-3 text-sm">
                <Icon className="h-4 w-4 text-[color:var(--color-teal)]" />
                {label}
              </span>
              <ArrowRight className="h-4 w-4 text-[color:var(--color-text-muted)] group-hover:text-[color:var(--color-teal)]" />
            </Link>
          </li>
        ))}
      </ul>
    </Card>
  );
}
