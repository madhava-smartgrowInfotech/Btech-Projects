import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { MapContainer, TileLayer, ZoomControl } from "react-leaflet";
import { useQueryClient } from "@tanstack/react-query";
import { AnimatePresence, motion } from "motion/react";
import { Layers, LocateFixed, MapPinned, Megaphone, Navigation, SlidersHorizontal, X } from "lucide-react";
import { toast } from "sonner";
import "@/components/map/leaflet-setup";
import { HeatLayer } from "@/components/map/HeatLayer";
import { FitBounds, HexLayer, LivePointsLayer, NodesLayer } from "@/components/map/layers";
import { ComplaintsLayer, PredictedLayer, SuggestionLayer } from "@/components/map/extraLayers";
import { ReportDialog } from "@/components/complaints/ReportDialog";
import { MapFilters } from "@/components/map/MapFilters";
import { ZoneDetails } from "@/components/map/ZoneDetails";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Sheet, SheetContent, SheetDescription, SheetTitle } from "@/components/ui/sheet";
import { Skeleton } from "@/components/ui/skeleton";
import { Switch } from "@/components/ui/switch";
import { api, apiError } from "@/lib/api";
import { DEFAULT_FILTERS, useCoverageSummary, useHeat, useHexes, useLiveStream, useNodes, usePoints, type CoverageFilters, type HexProps, type LivePoint } from "@/lib/coverage";
import { cn, safeStorage } from "@/lib/utils";
import { ZONE_COLOR, ZONE_TEXT, type ZoneLabel } from "@/lib/zones";

const FILTER_KEY = "signalscout-map-filters";
const LAYER_KEY = "signalscout-map-layers";
type LayerKey = "hex" | "heat" | "live" | "nodes" | "complaints" | "predicted";
const LAYER_LABEL: Record<LayerKey, string> = { hex: "Zones (hexagons)", heat: "Problem heat", live: "Recent readings", nodes: "Sensor nodes", complaints: "Open complaints", predicted: "Predicted coverage" };

function load<T>(key: string, fallback: T): T {
  try {
    const raw = safeStorage.get(key);
    return raw ? { ...fallback, ...JSON.parse(raw) } : fallback;
  } catch {
    return fallback;
  }
}

function useIsDesktop() {
  const [desktop, setDesktop] = useState(() => window.matchMedia("(min-width: 1024px)").matches);
  useEffect(() => {
    const mq = window.matchMedia("(min-width: 1024px)");
    const on = () => setDesktop(mq.matches);
    mq.addEventListener("change", on);
    return () => mq.removeEventListener("change", on);
  }, []);
  return desktop;
}

export default function CoverageMap() {
  const qc = useQueryClient();
  const desktop = useIsDesktop();
  const [filters, setFilters] = useState<CoverageFilters>(() => load(FILTER_KEY, DEFAULT_FILTERS));
  const [layers, setLayers] = useState<Record<LayerKey, boolean>>(() => load(LAYER_KEY, { hex: true, heat: false, live: true, nodes: true, complaints: true, predicted: false }));
  const [selected, setSelected] = useState<HexProps | null>(null);
  const [filtersOpen, setFiltersOpen] = useState(false);
  const [layersOpen, setLayersOpen] = useState(false);
  const [live, setLive] = useState<LivePoint[]>([]);
  const [fitKey, setFitKey] = useState("initial");
  const [locateBounds, setLocateBounds] = useState<[[number, number], [number, number]] | null>(null);
  const refreshTimer = useRef<number | undefined>(undefined);
  const [suggestion, setSuggestion] = useState<{ from: [number, number]; to: [number, number] | null; message: string } | null>(null);
  const [suggesting, setSuggesting] = useState(false);
  const [reportAt, setReportAt] = useState<{ at: [number, number]; operator: string | null } | null>(null);
  const [predictedInfo, setPredictedInfo] = useState<{ operator: string | null; target: string | null; cells: number } | null>(null);

  useEffect(() => safeStorage.set(FILTER_KEY, JSON.stringify(filters)), [filters]);
  useEffect(() => safeStorage.set(LAYER_KEY, JSON.stringify(layers)), [layers]);

  const summary = useCoverageSummary();
  const hex = useHexes(filters);
  const heat = useHeat(filters, layers.heat);
  const points = usePoints(filters, layers.live);
  const nodes = useNodes(layers.nodes);

  useEffect(() => setLive(points.data ?? []), [points.data]);

  const onLive = useCallback(
    (pts: LivePoint[]) => {
      const keep = pts.filter((p) => (!filters.operator || p.operator === filters.operator) && (!filters.sources.length || filters.sources.includes(p.source)));
      if (!keep.length) return;
      setLive((prev) => [...keep.map((p) => ({ ...p, fresh: true })), ...prev.map((p) => ({ ...p, fresh: false }))].slice(0, 600));
      window.clearTimeout(refreshTimer.current);   // refresh the zones shortly after a burst of new readings
      refreshTimer.current = window.setTimeout(() => qc.invalidateQueries({ queryKey: ["coverage-hex"] }), 4000);
    },
    [filters.operator, filters.sources, qc],
  );
  const connected = useLiveStream(layers.live, { readings: onLive });

  const bounds = useMemo<[[number, number], [number, number]] | null>(() => {
    const feats = hex.data?.features ?? [];
    if (feats.length) {
      let [a, b, c, d] = [90, 180, -90, -180];
      for (const f of feats) {
        const [lat, lon] = f.properties.center;
        a = Math.min(a, lat); b = Math.min(b, lon); c = Math.max(c, lat); d = Math.max(d, lon);
      }
      return [[a, b], [c, d]];
    }
    return summary.data?.bounds ?? null;
  }, [hex.data, summary.data]);

  const totals = useMemo(() => {
    const t = { Strong: 0, Weak: 0, Dead: 0 } as Record<ZoneLabel, number>;
    for (const f of hex.data?.features ?? []) {
      t.Strong += f.properties.strong; t.Weak += f.properties.weak; t.Dead += f.properties.dead;
    }
    return t;
  }, [hex.data]);

  const locate = () => {
    if (!navigator.geolocation) return toast.error("Location is not available in this browser");
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        const { latitude: lat, longitude: lon } = pos.coords;
        setFitKey(`me-${Date.now()}`);
        setLocateBounds([[lat - 0.005, lon - 0.007], [lat + 0.005, lon + 0.007]]);
      },
      () => toast.error("Couldn't get your location - allow location access for this site"),
      { enableHighAccuracy: true, timeout: 10000 },
    );
  };

  const mainOperator = (z: HexProps) => filters.operator ?? Object.entries(z.operators).sort((a, b) => b[1].n - a[1].n)[0]?.[0] ?? null;
  const findBetter = async (z: HexProps) => {
    setSuggesting(true);
    try {
      const { data } = await api.get<{ found: boolean; status: string; message: string; lat: number | null; lon: number | null }>("/api/suggest", {
        params: { lat: z.center[0], lon: z.center[1], ...(mainOperator(z) ? { operator: mainOperator(z) } : {}) },
      });
      setSuggestion({ from: z.center, to: data.found && data.status === "found" && data.lat != null && data.lon != null ? [data.lat, data.lon] : null, message: data.message });
    } catch (e) {
      toast.error(apiError(e));
    } finally {
      setSuggesting(false);
    }
  };
  const zoneActions = (z: HexProps) => (
    <div className="space-y-2 border-t pt-4">
      {suggestion && suggestion.from[0] === z.center[0] && suggestion.from[1] === z.center[1] && (
        <p className="rounded-lg bg-primary/10 px-3 py-2 text-sm">{suggestion.message}</p>
      )}
      <div className="grid grid-cols-2 gap-2">
        <Button variant="outline" size="sm" onClick={() => findBetter(z)} loading={suggesting}><Navigation /> Better signal</Button>
        <Button variant="outline" size="sm" onClick={() => setReportAt({ at: z.center, operator: mainOperator(z) })}><Megaphone /> Report</Button>
      </div>
    </div>
  );

  const filterCount = [filters.operator, filters.days, filters.hours, filters.sources.length ? 1 : null, filters.includeWifi || null].filter(Boolean).length;
  const empty = hex.isSuccess && hex.data.features.length === 0;

  const layerToggles = (
    <div className="space-y-2.5">
      {(Object.keys(LAYER_LABEL) as LayerKey[]).map((k) => (
        <label key={k} className="flex items-center justify-between gap-4 text-sm">
          {LAYER_LABEL[k]}
          <Switch checked={layers[k]} onCheckedChange={(v) => setLayers((l) => ({ ...l, [k]: v }))} />
        </label>
      ))}
    </div>
  );

  return (
    <div className="relative isolate h-[calc(100dvh-4rem)] w-full overflow-hidden">
      <MapContainer center={[22.5, 79]} zoom={5} zoomControl={false} className="h-full w-full" preferCanvas>
        <TileLayer attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors' url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" maxZoom={19} />
        <ZoomControl position="bottomright" />
        <FitBounds bounds={locateBounds ?? bounds} fitKey={locateBounds ? fitKey : bounds ? "data" : "none"} />
        {layers.heat && heat.data && <HeatLayer points={heat.data.points} />}
        {layers.hex && hex.data && <HexLayer data={hex.data} selected={selected?.cell ?? null} onSelect={setSelected} />}
        {layers.live && <LivePointsLayer points={live} />}
        {layers.nodes && nodes.data && <NodesLayer nodes={nodes.data} />}
        {layers.predicted && <PredictedLayer operator={filters.operator} onInfo={setPredictedInfo} />}
        {layers.complaints && <ComplaintsLayer />}
        {suggestion?.to && <SuggestionLayer from={suggestion.from} to={suggestion.to} />}
      </MapContainer>

      {/* top bar */}
      <div className="pointer-events-none absolute inset-x-0 top-0 z-[1000] flex items-start justify-between gap-2 p-3">
        <Card className="pointer-events-auto w-full max-w-[380px] p-3 shadow-lg lg:p-4">
          <div className="flex items-center justify-between gap-2">
            <div className="min-w-0">
              <h1 className="flex items-center gap-2 text-base font-bold lg:text-lg">
                <MapPinned className="h-4 w-4 text-primary" aria-hidden /> Coverage map
              </h1>
              <p className="truncate text-xs text-muted-foreground">
                {hex.isPending ? "Loading zones…" : `${(hex.data?.readings ?? 0).toLocaleString()} readings · ${hex.data?.features.length ?? 0} zones`}
                {layers.live && (
                  <span className="ml-2 inline-flex items-center gap-1">
                    <span className={cn("h-1.5 w-1.5 rounded-full", connected ? "bg-zone-strong" : "bg-muted-foreground")} aria-hidden />
                    {connected ? "live" : "connecting"}
                  </span>
                )}
              </p>
            </div>
            <div className="flex shrink-0 gap-1">
              <Button size="sm" variant={filtersOpen ? "secondary" : "outline"} onClick={() => setFiltersOpen((o) => !o)} aria-expanded={filtersOpen} aria-label={filterCount ? `Filters (${filterCount} active)` : "Filters"}>
                <SlidersHorizontal /> <span className="hidden sm:inline">Filters</span>
                {filterCount > 0 && <span className="rounded-full bg-primary px-1.5 text-[10px] text-primary-foreground">{filterCount}</span>}
              </Button>
              <Button size="icon" variant="outline" className="h-9 w-9 lg:hidden" onClick={() => setLayersOpen(true)} aria-label="Map layers">
                <Layers />
              </Button>
            </div>
          </div>
          <AnimatePresence initial={false}>
            {filtersOpen && desktop && (
              <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: "auto", opacity: 1 }} exit={{ height: 0, opacity: 0 }} className="overflow-hidden">
                <div className="pt-4">
                  <MapFilters value={filters} onChange={setFilters} summary={summary.data} />
                  {filterCount > 0 && (
                    <Button variant="link" size="sm" className="mt-2 h-auto px-0" onClick={() => setFilters(DEFAULT_FILTERS)}>
                      Clear filters
                    </Button>
                  )}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </Card>

        <Card className="pointer-events-auto hidden w-60 p-4 shadow-lg lg:block">
          <p className="mb-3 flex items-center gap-2 text-sm font-semibold">
            <Layers className="h-4 w-4 text-primary" aria-hidden /> Layers
          </p>
          {layerToggles}
          <Button variant="outline" size="sm" className="mt-4 w-full" onClick={locate}>
            <LocateFixed /> Show my area
          </Button>
        </Card>
      </div>

      {/* legend */}
      <Card className="absolute bottom-3 left-3 z-[1000] max-w-[calc(100%-5rem)] p-3 shadow-lg">
        <ul className="space-y-1.5">
          {(Object.keys(ZONE_COLOR) as ZoneLabel[]).map((z) => (
            <li key={z} className="flex items-center gap-2 text-xs">
              <span className="h-3 w-3 rounded" style={{ backgroundColor: ZONE_COLOR[z] }} aria-hidden />
              <span className="w-12 font-semibold">{z}</span>
              <span className="hidden text-muted-foreground sm:inline">{ZONE_TEXT[z]}</span>
              <span className="ml-auto pl-2 tabular text-muted-foreground">{totals[z].toLocaleString()}</span>
            </li>
          ))}
        </ul>
        {layers.predicted && (
          <div className="mt-2 border-t pt-2 text-xs">
            <p className="mb-1 font-medium">Predicted chance of strong signal</p>
            <div className="h-2 w-40 rounded-full" style={{ background: "linear-gradient(90deg, rgba(24,79,149,0.08), rgba(24,79,149,0.63))" }} aria-hidden />
            <p className="mt-1 flex w-40 justify-between text-muted-foreground"><span>0%</span><span>100%</span></p>
            <p className="text-muted-foreground">{predictedInfo?.cells ? `${predictedInfo.operator ?? ""} · ${predictedInfo.target === "log_dl" ? "from phone speed tests" : "from signal level"}` : "Move the map over measured streets"}</p>
          </div>
        )}
      </Card>

      {/* states */}
      {hex.isPending && (
        <div className="absolute inset-0 z-[900] flex items-center justify-center bg-background/40">
          <Skeleton className="h-10 w-48" />
        </div>
      )}
      {hex.isError && (
        <Card className="absolute left-1/2 top-1/2 z-[1000] w-[min(90%,360px)] -translate-x-1/2 -translate-y-1/2 p-5 text-center shadow-xl" role="alert">
          <p className="font-semibold">Couldn't load coverage</p>
          <p className="mt-1 text-sm text-muted-foreground">{apiError(hex.error)}</p>
          <Button size="sm" className="mt-3" onClick={() => hex.refetch()}>Try again</Button>
        </Card>
      )}
      {empty && !hex.isFetching && (
        <Card className="absolute left-1/2 top-1/2 z-[1000] w-[min(90%,380px)] -translate-x-1/2 -translate-y-1/2 p-5 text-center shadow-xl">
          <p className="font-semibold">No readings match these filters</p>
          <p className="mt-1 text-sm text-muted-foreground">
            {filterCount ? "Try a wider period or time of day, or clear the filters." : "Connect a phone or sensor node to start collecting readings."}
          </p>
          {filterCount > 0 && <Button size="sm" variant="outline" className="mt-3" onClick={() => setFilters(DEFAULT_FILTERS)}>Clear filters</Button>}
        </Card>
      )}

      {/* zone details: side card on desktop, bottom sheet on phones */}
      <AnimatePresence>
        {selected && desktop && (
          <motion.div initial={{ opacity: 0, x: 24 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: 24 }} transition={{ duration: 0.2 }}
            className="absolute bottom-3 right-14 top-[16.5rem] z-[1000] w-[360px]">
            <Card className="h-full overflow-y-auto p-4 shadow-xl">
              <div className="mb-3 flex items-center justify-between">
                <h2 className="text-base font-semibold">Zone details</h2>
                <Button size="icon" variant="ghost" className="h-8 w-8" onClick={() => setSelected(null)} aria-label="Close zone details">
                  <X />
                </Button>
              </div>
              <ZoneDetails zone={selected} actions={zoneActions(selected)} />
            </Card>
          </motion.div>
        )}
      </AnimatePresence>
      <Sheet open={!!selected && !desktop} onOpenChange={(o) => !o && setSelected(null)}>
        <SheetContent side="bottom" className="p-5 pb-8">
          <SheetTitle className="mb-3 text-base font-semibold">Zone details</SheetTitle>
          <SheetDescription className="sr-only">Readings and metrics for the selected zone</SheetDescription>
          <div className="overflow-y-auto">{selected && <ZoneDetails zone={selected} actions={zoneActions(selected)} />}</div>
        </SheetContent>
      </Sheet>

      <Sheet open={filtersOpen && !desktop} onOpenChange={setFiltersOpen}>
        <SheetContent side="bottom" className="p-5 pb-8">
          <SheetTitle className="mb-4 text-base font-semibold">Filters</SheetTitle>
          <SheetDescription className="sr-only">Choose which readings appear on the map</SheetDescription>
          <div className="overflow-y-auto">
            <MapFilters value={filters} onChange={setFilters} summary={summary.data} />
            <div className="mt-5 flex gap-2">
              <Button variant="outline" className="flex-1" onClick={() => setFilters(DEFAULT_FILTERS)}>Clear</Button>
              <Button className="flex-1" onClick={() => setFiltersOpen(false)}>Show results</Button>
            </div>
          </div>
        </SheetContent>
      </Sheet>
      <ReportDialog open={!!reportAt} onOpenChange={(o) => !o && setReportAt(null)} at={reportAt?.at ?? null} operator={reportAt?.operator ?? null} />
      <Sheet open={layersOpen} onOpenChange={setLayersOpen}>
        <SheetContent side="bottom" className="p-5 pb-8">
          <SheetTitle className="mb-4 text-base font-semibold">Map layers</SheetTitle>
          <SheetDescription className="sr-only">Show or hide map layers</SheetDescription>
          {layerToggles}
          <Button variant="outline" className="mt-5 w-full" onClick={() => { setLayersOpen(false); locate(); }}>
            <LocateFixed /> Show my area
          </Button>
        </SheetContent>
      </Sheet>
    </div>
  );
}
