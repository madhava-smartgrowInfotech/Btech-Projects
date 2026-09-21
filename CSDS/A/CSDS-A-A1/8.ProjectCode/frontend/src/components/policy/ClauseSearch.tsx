import { Loader2, Search } from "lucide-react";
import { motion } from "motion/react";
import { useState, type FormEvent } from "react";

import { EmptyState, ErrorState } from "@/components/common/States";
import { SourceChip } from "@/components/policy/SourceChip";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useClauseSearch } from "@/lib/queries";
import { formatMs } from "@/lib/utils";

const MODES = [
  { value: "hybrid_rerank", label: "Hybrid + re-rank" },
  { value: "hybrid", label: "Hybrid (RRF)" },
  { value: "bm25", label: "Keyword (BM25)" },
  { value: "dense", label: "Semantic (embeddings)" },
];

function highlight(text: string, query: string) {
  const words = query
    .toLowerCase()
    .split(/\W+/)
    .filter((w) => w.length > 3);
  if (!words.length) return text;
  const escaped = words.map((w) => w.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")).join("|");
  const re = new RegExp(`(\\b(?:${escaped})\\w*)`, "gi");
  return text.split(re).map((part, i) =>
    words.some((w) => part.toLowerCase().startsWith(w)) && re.test(part) ? (
      <mark key={i} className="rounded bg-amber-200/60 px-0.5 text-inherit dark:bg-amber-400/25">
        {part}
      </mark>
    ) : (
      part
    ),
  );
}

export function ClauseSearch({ policyId, onOpenSource }: { policyId: number; onOpenSource: (page: number, ordinal: number) => void }) {
  const [query, setQuery] = useState("");
  const [mode, setMode] = useState("hybrid_rerank");
  const search = useClauseSearch(policyId);

  function submit(e: FormEvent) {
    e.preventDefault();
    if (query.trim().length >= 2) search.mutate({ query: query.trim(), mode, k: 8 });
  }

  return (
    <div className="space-y-4">
      <form onSubmit={submit} className="flex flex-col gap-2 sm:flex-row">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search clauses, e.g. “cataract waiting period” or “room rent”"
            className="pl-9"
            aria-label="Search clauses"
          />
        </div>
        <Select value={mode} onValueChange={setMode}>
          <SelectTrigger className="sm:w-[210px]" aria-label="Retrieval method">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {MODES.map((m) => (
              <SelectItem key={m.value} value={m.value}>
                {m.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Button type="submit" disabled={search.isPending || query.trim().length < 2}>
          {search.isPending ? <Loader2 className="animate-spin" /> : <Search />} Search
        </Button>
      </form>

      {search.isError ? (
        <ErrorState error={search.error} />
      ) : !search.data ? (
        <EmptyState
          icon={<Search />}
          title="Explore the policy's clauses"
          description="The same hybrid retrieval that grounds every answer: BM25 keyword search and semantic embeddings, fused and re-ranked. Switch the method to compare."
        />
      ) : search.data.items.length === 0 ? (
        <EmptyState icon={<Search />} title="No matching clauses" description="Try different words - for example the medical term." />
      ) : (
        <div className="space-y-3">
          <p className="text-xs text-muted-foreground">
            {search.data.items.length} clauses ·{" "}
            {Object.entries(search.data.timings_ms)
              .map(([k, v]) => `${k} ${formatMs(v)}`)
              .join(" · ")}
          </p>
          <ol className="space-y-3">
            {search.data.items.map((item, i) => (
              <motion.li
                key={item.clause.ordinal}
                initial={{ opacity: 0, y: 6 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.03 }}
                className="rounded-xl border bg-card p-4"
              >
                <div className="flex flex-wrap items-center gap-2">
                  <span className="grid size-6 place-items-center rounded-full bg-primary/10 text-xs font-semibold text-primary">{i + 1}</span>
                  <span className="min-w-0 flex-1 truncate text-sm font-semibold">{item.clause.label}</span>
                  <SourceChip label={item.clause.label} page={item.clause.page_start} onOpen={() => onOpenSource(item.clause.page_start, item.clause.ordinal)} />
                </div>
                <div className="mt-2 flex flex-wrap gap-1.5 text-[11px]">
                  {item.bm25_rank && <Badge variant="outline">Keyword rank {item.bm25_rank}</Badge>}
                  {item.dense_rank && <Badge variant="outline">Semantic rank {item.dense_rank}</Badge>}
                  {item.rerank !== null && <Badge variant="secondary">Relevance {(item.rerank * 100).toFixed(0)}%</Badge>}
                </div>
                <p className="mt-2 line-clamp-5 text-sm leading-relaxed text-muted-foreground">{highlight(item.clause.text, search.data!.query)}</p>
              </motion.li>
            ))}
          </ol>
        </div>
      )}
    </div>
  );
}
