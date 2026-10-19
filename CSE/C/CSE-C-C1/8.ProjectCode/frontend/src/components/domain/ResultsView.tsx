import { BarChart3, Crown } from "lucide-react";
import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { axisProps, ChartCard, ChartGradients, ChartTooltip, gridProps } from "@/components/charts/Chart";
import { Badge } from "@/components/ui/Badge";
import { Card } from "@/components/ui/Card";
import { Table, type Column } from "@/components/ui/Table";
import type { TallyResult, TallyRow } from "@/lib/types";

const share = (votes: number, total: number) => (total ? (votes / total) * 100 : 0);

/** Bar chart + ranked table for a tally. The table is also the accessible view of the chart. */
export function ResultsView({ tally }: { tally: TallyResult }) {
  const total = tally.total_votes;
  const top = tally.results[0]?.votes ?? 0;
  const tied = tally.results.filter((r) => r.votes === top).length > 1;
  const rows = tally.results;

  const columns: Column<TallyRow & { rank: number }>[] = [
    { key: "rank", header: "Rank", cell: (r) => <span className="tabular-nums">{r.rank}</span> },
    {
      key: "name",
      header: "Candidate",
      cell: (r) => (
        <span className="inline-flex items-center gap-2 font-medium">
          {r.name}
          {total > 0 && r.votes === top && <Badge tone="gradient"><Crown /> {tied ? "Tied for lead" : "Leading"}</Badge>}
        </span>
      ),
    },
    { key: "party", header: "Party", cell: (r) => <span className="text-muted-foreground">{r.party ?? "Independent"}</span> },
    { key: "votes", header: "Votes", cell: (r) => <strong className="tabular-nums">{r.votes}</strong>, align: "right" },
    { key: "share", header: "Share", cell: (r) => <span className="tabular-nums">{share(r.votes, total).toFixed(1)}%</span>, align: "right" },
  ];

  return (
    <div className="space-y-4">
      <ChartCard
        title="Vote share"
        description={`${total} ${total === 1 ? "ballot" : "ballots"} counted from the decrypted ledger`}
        icon={<BarChart3 />}
        table={{ columns: ["Candidate", "Votes", "Share"], rows: rows.map((r) => [r.name, r.votes, `${share(r.votes, total).toFixed(1)}%`]) }}
        empty={rows.length === 0 ? "This election has no candidates yet." : undefined}
      >
        <div style={{ height: Math.max(180, rows.length * 56 + 24) }} className="w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={rows} layout="vertical" margin={{ top: 4, right: 24, left: 8, bottom: 4 }}>
              <ChartGradients />
              <CartesianGrid {...gridProps} horizontal={false} vertical />
              <XAxis type="number" {...axisProps} allowDecimals={false} />
              <YAxis type="category" dataKey="name" width={110} {...axisProps} />
              <Tooltip content={<ChartTooltip formatter={(v) => `${v} votes`} />} cursor={{ fill: "var(--muted)" }} />
              <Bar dataKey="votes" name="Votes" radius={[0, 8, 8, 0]} barSize={26}>
                {rows.map((r, i) => (
                  <Cell key={r.candidate_id} fill={`url(#bar-${i % 3})`} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </ChartCard>
      <Card className="p-4">
        <Table columns={columns} rows={rows.map((r, i) => ({ ...r, rank: i + 1 }))} rowKey={(r) => r.candidate_id} pageSize={12} caption="Election results" />
      </Card>
    </div>
  );
}
