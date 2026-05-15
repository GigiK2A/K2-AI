import { KpiCard } from "@/components/dashboard/kpi-card";
import { formatEuro, formatNumber } from "@/lib/format";

interface Props {
  mtdCents: number;
  ytdCents: number;
  operationsMonth: number;
}

export function RevenueKpis({ mtdCents, ytdCents, operationsMonth }: Props) {
  return (
    <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
      <KpiCard label="MTD" value={formatEuro(mtdCents)} accent="teal" />
      <KpiCard label="YTD" value={formatEuro(ytdCents)} />
      <KpiCard
        label="Operazioni mese"
        value={formatNumber(operationsMonth)}
        sublabel="eventi registrati questo mese"
      />
    </div>
  );
}
