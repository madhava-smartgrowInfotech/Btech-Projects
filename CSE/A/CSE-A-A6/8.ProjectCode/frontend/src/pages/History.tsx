import { Activity, AlertTriangle, Download, History as HistoryIcon, Radio, RefreshCw, ShieldCheck } from "lucide-react";
import { useMemo, useState } from "react";
import { Link } from "react-router";
import { CartesianGrid, Line, LineChart, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { axisProps, ChartCard, ChartTooltip, gridProps } from "@/components/charts/Chart";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { StatCard } from "@/components/ui/Display";
import { CardsSkeleton, EmptyState, ErrorState, Skeleton } from "@/components/ui/Feedback";
import { PageHeader } from "@/components/ui/Layout";
import { SearchField } from "@/components/ui/Field";
import { Table, type Column } from "@/components/ui/Table";
import { toast } from "@/components/ui/Toast";
import { Segmented } from "@/components/ui/Toggles";
import { downloadBlob, endpoints, errorMessage } from "@/lib/api";
import { useHistory, useSettings } from "@/lib/queries";
import type { HistoryEvent } from "@/lib/types";
import { fixed, utcStamp, verdictTone } from "@/lib/verdict";

type Filter = "all" | "live" | "simulation";

export default function History() {
  const history = useHistory();
  const settings = useSettings();
  const [filter, setFilter] = useState<Filter>("all");
  const [query, setQuery] = useState("");
  const [exporting, setExporting] = useState(false);

  const events = history.data?.events ?? [];
  const shown = useMemo(() => {
    const q = query.trim().toLowerCase();
    return events.filter(
      (e) =>
        (filter === "all" || (filter === "simulation") === e.simulation) &&
        (!q || `${e.state} ${e.reason} ${e.quality} ${e.source}`.toLowerCase().includes(q)),
    );
  }, [events, filter, query]);

  // chart: Good-quality readings in logged order, live and simulation as separate series (as in the desktop chart)
  const chartData = useMemo(
    () =>
      [...events]
        .filter((e) => e.quality === "Good")
        .reverse()
        .map((e) => ({ id: e.id, live: e.simulation ? null : e.ear, simulation: e.simulation ? e.ear : null })),
    [events],
  );

  async function exportCsv() {
    setExporting(true);
    try {
      downloadBlob(await endpoints.exportHistory(), "rider_events.csv");
      toast.success("Exported all event rows to rider_events.csv");
    } catch (e) {
      toast.error(errorMessage(e, "Export failed"));
    } finally {
      setExporting(false);
    }
  }

  const columns: Column<HistoryEvent>[] = [
    { key: "time", header: "Time (UTC)", cell: (e) => <span className="whitespace-nowrap text-xs">{utcStamp(e.timestamp)}</span>, sortValue: (e) => e.id },
    {
      key: "source",
      header: "Source",
      cell: (e) => <Badge tone={e.simulation ? "magenta" : "cyan"}>{e.source}</Badge>,
      sortValue: (e) => e.source,
    },
    {
      key: "state",
      header: "State",
      cell: (e) => (
        <Badge tone={verdictTone(e.state)}>
          {e.alert && <AlertTriangle />}
          {e.state}
        </Badge>
      ),
      sortValue: (e) => e.state,
    },
    { key: "quality", header: "Quality", cell: (e) => e.quality, sortValue: (e) => e.quality },
    { key: "reason", header: "Reason", cell: (e) => <span className="block max-w-[22rem] text-xs text-muted-foreground">{e.reason}</span> },
    { key: "ear", header: "EAR", align: "right", cell: (e) => <span className="tabular-nums">{fixed(e.ear)}</span>, sortValue: (e) => e.ear },
    { key: "closure", header: "Closure s", align: "right", cell: (e) => <span className="tabular-nums">{fixed(e.closure, 1)}</span>, sortValue: (e) => e.closure },
    { key: "roll", header: "Roll deg", align: "right", cell: (e) => <span className="tabular-nums">{fixed(e.roll, 1)}</span>, sortValue: (e) => e.roll },
  ];

  const summary = history.data?.summary;
  const threshold = settings.data?.settings.ear_threshold;

  return (
    <>
      <PageHeader
        title="Event history"
        eyebrow="Logged locally"
        description="Numeric events only (state changes, 5-second snapshots and alerts). Timestamps are UTC and simulations are labelled. No video or face images are stored."
        actions={
          <>
            <Button variant="secondary" onClick={() => void history.refetch()} loading={history.isFetching && !history.isPending}>
              <RefreshCw /> Refresh
            </Button>
            <Button onClick={() => void exportCsv()} loading={exporting} disabled={!history.data?.total}>
              <Download /> Export CSV
            </Button>
          </>
        }
      />

      {history.isPending ? (
        <div className="space-y-6">
          <CardsSkeleton count={4} className="lg:grid-cols-4" />
          <Skeleton className="h-72 w-full rounded-2xl" />
        </div>
      ) : history.isError ? (
        <ErrorState error={history.error} title="Couldn't load the event history" onRetry={() => void history.refetch()} />
      ) : history.data.total === 0 ? (
        <EmptyState
          icon={<HistoryIcon />}
          title="No events logged yet"
          description="Events appear here after you start monitoring on the Monitor screen, either with the camera or a simulation scenario."
          action={
            <Button asChild>
              <Link to="/app">Go to the monitor</Link>
            </Button>
          }
        />
      ) : (
        <div className="space-y-6">
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <StatCard label="Events logged" value={history.data.total} icon={<HistoryIcon />} hint={`${events.length} shown below`} />
            <StatCard
              label="Warning events"
              value={summary?.warnings ?? 0}
              icon={<AlertTriangle />}
              accent="magenta"
              hint={`${summary?.alerts ?? 0} alert${summary?.alerts === 1 ? "" : "s"} fired`}
            />
            <StatCard label="Normal events" value={summary?.normal ?? 0} icon={<ShieldCheck />} accent="cyan" hint={`${summary?.unknown ?? 0} unable to assess`} />
            <StatCard label="Live vs simulation" display={`${summary?.live ?? 0} / ${summary?.simulation ?? 0}`} icon={<Radio />} hint="live camera / scripted" />
          </div>

          <ChartCard
            title="EAR at logged events"
            description="Sparse event samples with Good signal quality, not a continuous recording."
            icon={<Activity />}
            legend={[
              { label: "Live camera", color: "#22D3EE" },
              { label: "Simulation", color: "#F472B6" },
            ]}
            empty={chartData.length === 0 ? "No Good-quality events to chart yet." : undefined}
            table={{
              columns: ["Event ID", "Live EAR", "Simulation EAR"],
              rows: chartData.map((d) => [d.id, d.live === null ? null : Number(d.live.toFixed(3)), d.simulation === null ? null : Number(d.simulation.toFixed(3))]),
            }}
          >
            <div className="h-64 w-full" role="img" aria-label="Line chart of eye aspect ratio at each logged event, live camera versus simulation">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chartData} margin={{ top: 8, right: 12, bottom: 0, left: -16 }}>
                  <CartesianGrid {...gridProps} />
                  <XAxis dataKey="id" {...axisProps} label={{ value: "Logged event ID", position: "insideBottom", offset: -2, fill: "var(--chart-axis)", fontSize: 11 }} height={36} />
                  <YAxis {...axisProps} domain={[0, 0.5]} />
                  {threshold !== undefined && <ReferenceLine y={threshold} stroke="#FB7185" strokeDasharray="5 4" />}
                  <Tooltip content={<ChartTooltip />} />
                  <Line type="linear" dataKey="live" name="Live camera" stroke="#22D3EE" strokeWidth={2} dot={{ r: 3 }} connectNulls isAnimationActive={false} />
                  <Line type="linear" dataKey="simulation" name="Simulation" stroke="#F472B6" strokeWidth={2} dot={{ r: 3 }} connectNulls isAnimationActive={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </ChartCard>

          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <Segmented
              label="Filter by source"
              value={filter}
              onChange={setFilter}
              options={[
                { value: "all", label: "All" },
                { value: "live", label: "Live camera" },
                { value: "simulation", label: "Simulation" },
              ]}
            />
            <SearchField value={query} onChange={setQuery} placeholder="Search state, reason, quality…" label="Search events" className="sm:w-80" />
          </div>

          <Table
            caption="Logged rider events, newest first"
            columns={columns}
            rows={shown}
            rowKey={(e) => e.id}
            pageSize={12}
            initialSort={{ key: "time", dir: "desc" }}
            empty={
              <EmptyState
                icon={<HistoryIcon />}
                title="No events match"
                description="Try another source filter or clear the search."
                action={
                  <Button
                    variant="secondary"
                    onClick={() => {
                      setFilter("all");
                      setQuery("");
                    }}
                  >
                    Clear filters
                  </Button>
                }
              />
            }
          />
        </div>
      )}
    </>
  );
}
