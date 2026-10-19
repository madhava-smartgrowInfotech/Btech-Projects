import { AlertCircle, ArrowLeft, BadgeCheck, CheckCircle2, Clock, Fingerprint, Lock, ShieldCheck, Vote } from "lucide-react";
import { useEffect, useState, type FormEvent } from "react";
import { Link, useParams } from "react-router";

import { Hash, HashBlock, StatusBadge } from "@/components/domain/common";
import { useBreadcrumb } from "@/components/ui/AppShell";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card, CardBody } from "@/components/ui/Card";
import { KeyValueList } from "@/components/ui/Display";
import { EmptyState, ErrorState, Skeleton } from "@/components/ui/Feedback";
import { FormField, Input } from "@/components/ui/Field";
import { PageHeader } from "@/components/ui/Layout";
import { Stepper } from "@/components/ui/Navigation";
import { toast } from "@/components/ui/Toast";
import { errorMessage } from "@/lib/api";
import { useCastVote, useVerifyAadhaar, useVoterElection } from "@/lib/queries";
import type { Candidate, Receipt } from "@/lib/types";
import { cn, formatDate } from "@/lib/utils";

interface Pending {
  token: string;
  expiresAt: number;
  candidates: Candidate[];
}

const storeKey = (id: number) => `aegisballot-auth-${id}`;

/** The one-time token survives a page reload for its 10 minutes, so a refresh does not lock the voter out. */
function loadPending(id: number): Pending | null {
  try {
    const raw = sessionStorage.getItem(storeKey(id));
    if (!raw) return null;
    const p = JSON.parse(raw) as Pending;
    return p.expiresAt > Date.now() ? p : null;
  } catch {
    return null;
  }
}
function savePending(id: number, p: Pending | null) {
  try {
    if (p) sessionStorage.setItem(storeKey(id), JSON.stringify(p));
    else sessionStorage.removeItem(storeKey(id));
  } catch {
    /* private mode: the flow still works without persistence */
  }
}

const groupAadhaar = (digits: string) => digits.replace(/(\d{4})(?=\d)/g, "$1 ");

function Countdown({ expiresAt, onExpire }: { expiresAt: number; onExpire: () => void }) {
  const [left, setLeft] = useState(() => Math.max(0, expiresAt - Date.now()));
  useEffect(() => {
    const t = setInterval(() => {
      const next = Math.max(0, expiresAt - Date.now());
      setLeft(next);
      if (next === 0) onExpire();
    }, 1000);
    return () => clearInterval(t);
  }, [expiresAt, onExpire]);
  const m = Math.floor(left / 60000);
  const s = Math.floor((left % 60000) / 1000);
  return (
    <span className="inline-flex items-center gap-1.5 tabular-nums" role="timer" aria-label="Time left on your one-time authorization">
      <Clock className="size-4" /> {m}:{String(s).padStart(2, "0")}
    </span>
  );
}

export default function VoteFlow() {
  const id = Number(useParams().id);
  const info = useVoterElection(id);
  const verify = useVerifyAadhaar(id);
  const cast = useCastVote(id);
  useBreadcrumb(info.data?.election.title);

  const [pending, setPending] = useState<Pending | null>(() => loadPending(id));
  const [aadhaar, setAadhaar] = useState("");
  const [selected, setSelected] = useState<number | null>(null);
  const [receipt, setReceipt] = useState<Receipt | null>(null);
  const [error, setError] = useState<string | null>(null);

  const step = receipt ? 2 : pending ? 1 : 0;

  async function submitAadhaar(e: FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      const r = await verify.mutateAsync(aadhaar);
      const p = { token: r.auth_token, expiresAt: Date.now() + r.expires_in * 1000, candidates: r.candidates };
      savePending(id, p);
      setPending(p);
      setAadhaar("");
      toast.success("Identity verified. Your one-time authorization is valid for 10 minutes.");
    } catch (err) {
      setError(errorMessage(err, "Verification failed."));
    }
  }

  async function submitVote() {
    if (!pending || selected === null) return;
    setError(null);
    try {
      const r = await cast.mutateAsync({ candidate_id: selected, auth_token: pending.token });
      savePending(id, null);
      setPending(null);
      setReceipt(r.receipt);
      toast.success("Your vote is recorded on the ledger");
    } catch (err) {
      setError(errorMessage(err, "Your vote could not be recorded."));
    }
  }

  function expire() {
    savePending(id, null);
    setPending(null);
    setSelected(null);
    setError("Your one-time authorization expired. Verify again to continue.");
  }

  const back = (
    <Button asChild variant="secondary" magnetic={false}>
      <Link to="/app/voter"><ArrowLeft /> My elections</Link>
    </Button>
  );

  if (info.isPending) return <><PageHeader title="Verify and vote" /><div className="space-y-4" role="status" aria-label="Loading"><Skeleton className="h-16 rounded-2xl" /><Skeleton className="h-72 rounded-2xl" /></div></>;
  if (info.isError) return <><PageHeader title="Verify and vote" actions={back} /><ErrorState error={info.error} title="Could not load this election" onRetry={() => info.refetch()} /></>;

  const { election, masked_aadhaar, voted, ballot_id, voted_at } = info.data;

  if (voted && !receipt) {
    return (
      <>
        <PageHeader eyebrow="Voter" title={election.title} actions={back} />
        <Card strong className="mx-auto max-w-xl">
          <CardBody className="space-y-4 text-center">
            <span className="mx-auto grid size-14 place-items-center rounded-2xl bg-success/12 text-success"><CheckCircle2 className="size-7" /></span>
            <h2 className="font-display text-xl font-semibold">You have already voted</h2>
            <p className="text-sm text-muted-foreground">Duplicate voting is blocked by the database, your one-time token and the ledger. {voted_at && `You voted on ${formatDate(voted_at, true)}.`}</p>
            {ballot_id && <div className="text-left"><div className="mb-1 text-xs text-muted-foreground">Your ballot receipt ID</div><HashBlock value={ballot_id} /></div>}
          </CardBody>
        </Card>
      </>
    );
  }

  if (election.status !== "OPEN" && !receipt && !pending) {
    return (
      <>
        <PageHeader eyebrow="Voter" title={election.title} actions={back} />
        <EmptyState
          icon={<Lock />}
          title={election.status === "CLOSED" ? "This election is closed" : "Voting is not open right now"}
          description={election.status === "CLOSED" ? "The tally is published, so you can view the results." : "An administrator has this election paused or in draft. Check back later."}
          action={election.status === "CLOSED" ? <Button asChild><Link to={`/app/results/${id}`}>View results</Link></Button> : back}
        />
      </>
    );
  }

  return (
    <>
      <PageHeader
        eyebrow="Voter"
        title={election.title}
        description={<span className="inline-flex flex-wrap items-center gap-2"><StatusBadge status={election.status} /><Badge tone="warning">Demo verification environment · synthetic data only</Badge></span>}
        actions={step < 2 ? back : undefined}
      />
      <Stepper
        className="mb-6"
        current={step}
        steps={[
          { label: "Verify identity", description: "Aadhaar check" },
          { label: "Choose candidate", description: "Confirm your pick" },
          { label: "Receipt", description: "Ledger proof" },
        ]}
      />

      {error && (
        <div role="alert" className="mb-4 flex items-start gap-2 rounded-xl border border-danger/30 bg-danger/10 px-4 py-3 text-sm text-danger">
          <AlertCircle className="mt-0.5 size-4 shrink-0" />
          <div>
            <div className="font-medium">{step === 0 ? "Verification did not pass" : "Could not complete your vote"}</div>
            <div>{error}</div>
            {step === 0 && error.includes("pending") && <div className="mt-1 text-xs opacity-90">An authorization was already issued for this election. It expires 10 minutes after it was created; then you can verify again.</div>}
          </div>
        </div>
      )}

      {step === 0 && (
        <Card strong className="mx-auto max-w-xl">
          <CardBody className="space-y-5">
            <div className="flex items-start gap-3">
              <span className="grid size-11 shrink-0 place-items-center rounded-2xl bg-grad-primary text-white"><Fingerprint className="size-5" /></span>
              <div>
                <h2 className="font-display text-xl font-semibold">Aadhaar verification</h2>
                <p className="text-sm text-muted-foreground">Masked Aadhaar on file: <strong className="font-mono text-foreground">{masked_aadhaar ?? "not available"}</strong></p>
              </div>
            </div>
            <form onSubmit={submitAadhaar} className="space-y-4" noValidate>
              <FormField label="Enter your 12-digit Aadhaar number" hint="Checked for format, the Verhoeff checksum and the synthetic voter registry. Only a salted hash is kept.">
                {(p) => (
                  <Input
                    {...p}
                    inputMode="numeric"
                    autoComplete="off"
                    required
                    value={groupAadhaar(aadhaar)}
                    onChange={(e) => setAadhaar(e.target.value.replace(/\D/g, "").slice(0, 12))}
                    placeholder="2345 6789 0123"
                    className="font-mono tracking-wider"
                  />
                )}
              </FormField>
              <div className="flex flex-wrap items-center gap-3">
                <Button type="submit" size="lg" loading={verify.isPending} disabled={aadhaar.length !== 12}><ShieldCheck /> Verify identity</Button>
                {aadhaar.length > 0 && aadhaar.length < 12 && <span className="text-xs text-muted-foreground">{12 - aadhaar.length} more digits</span>}
              </div>
            </form>
            <p className="border-t border-[var(--glass-border)] pt-4 text-xs text-muted-foreground">
              Demo identities live in <code className="font-mono">data/synthetic_identities.json</code>. Use the Aadhaar assigned to the account you signed in with.
            </p>
          </CardBody>
        </Card>
      )}

      {step === 1 && pending && (
        <div className="space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-2 rounded-2xl border border-success/30 bg-success/10 px-4 py-3 text-sm">
            <span className="inline-flex items-center gap-2 text-success"><BadgeCheck className="size-4" /> Identity verified. One-time authorization issued.</span>
            <Countdown expiresAt={pending.expiresAt} onExpire={expire} />
          </div>

          {pending.candidates.length === 0 ? (
            <EmptyState icon={<Vote />} title="No active candidates" description="This election has no active candidates yet, so there is nothing to vote for." action={back} />
          ) : (
            <>
              <div role="radiogroup" aria-label="Candidates" className="grid gap-4 md:grid-cols-2">
                {pending.candidates.map((c) => {
                  const on = selected === c.id;
                  return (
                    <button
                      key={c.id}
                      type="button"
                      role="radio"
                      aria-checked={on}
                      onClick={() => setSelected(c.id)}
                      className={cn(
                        "glass sweep rounded-2xl p-5 text-left transition-[transform,box-shadow,border-color] duration-300 hover:-translate-y-0.5",
                        on && "border-transparent ring-2 ring-[var(--violet)] shadow-[0_0_28px_-6px_rgba(124,92,255,0.7)]",
                      )}
                    >
                      <div className="flex items-start justify-between gap-3">
                        <div className="min-w-0">
                          <div className="font-display text-lg font-semibold leading-tight">{c.name}</div>
                          <Badge tone="violet" className="mt-1">{c.party}</Badge>
                        </div>
                        <span className={cn("grid size-6 shrink-0 place-items-center rounded-full border", on ? "border-transparent bg-grad-primary text-white" : "border-[var(--input)]")}>
                          {on && <CheckCircle2 className="size-4" />}
                        </span>
                      </div>
                      {c.description && <p className="mt-3 text-sm">{c.description}</p>}
                      {c.manifesto && <p className="mt-1 text-sm text-muted-foreground">{c.manifesto}</p>}
                    </button>
                  );
                })}
              </div>

              <Card strong className={cn("transition-opacity", selected === null && "opacity-60")}>
                <CardBody className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                  <div className="space-y-1">
                    <h3 className="font-display text-lg font-semibold">Confirm your selection</h3>
                    {selected === null ? (
                      <p className="text-sm text-muted-foreground">Select one candidate above to continue.</p>
                    ) : (
                      <p className="text-sm">You selected <strong>{pending.candidates.find((c) => c.id === selected)?.name}</strong>. Your choice is encrypted with AES-256-GCM and recorded on the ledger. You cannot change it afterwards.</p>
                    )}
                  </div>
                  <Button size="lg" onClick={submitVote} loading={cast.isPending} disabled={selected === null} className="shrink-0">
                    <Lock /> Confirm and submit vote
                  </Button>
                </CardBody>
              </Card>
            </>
          )}
        </div>
      )}

      {step === 2 && receipt && (
        <Card strong className="mx-auto max-w-2xl">
          <CardBody className="space-y-5">
            <div className="flex items-start gap-3">
              <span className="grid size-12 shrink-0 place-items-center rounded-2xl bg-success/12 text-success"><CheckCircle2 className="size-6" /></span>
              <div>
                <h2 className="font-display text-xl font-semibold">Vote confirmed</h2>
                <p className="text-sm text-muted-foreground">Your ballot was encrypted and committed to the ledger after 2 of 3 validators signed the block.</p>
              </div>
            </div>
            <KeyValueList
              items={[
                { label: "Election", value: election.title },
                { label: "Ballot receipt ID", value: <Hash value={receipt.ballot_id} head={16} tail={6} /> },
                { label: "Transaction hash", value: <Hash value={receipt.tx_hash} head={16} tail={8} /> },
                { label: "Block number", value: `#${receipt.block_index}` },
                { label: "Block hash", value: <Hash value={receipt.block_hash} head={16} tail={8} /> },
                { label: "Status", value: <Badge tone="success"><BadgeCheck /> Vote confirmed</Badge> },
              ]}
            />
            <p className="rounded-xl border border-[var(--glass-border)] bg-muted/50 p-3 text-xs text-muted-foreground">
              This receipt proves your vote was accepted without revealing your candidate. Keep it. Voting again in this election is rejected by the database constraint, the used token and ledger nonce checks.
            </p>
            <Button asChild size="lg"><Link to="/app/voter">Return to my elections</Link></Button>
          </CardBody>
        </Card>
      )}
    </>
  );
}
