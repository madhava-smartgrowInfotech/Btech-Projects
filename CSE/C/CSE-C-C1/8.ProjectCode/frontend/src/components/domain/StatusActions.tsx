import { BarChart3, CirclePause, CirclePlay, CircleStop } from "lucide-react";
import { Link } from "react-router";

import { Button } from "@/components/ui/Button";
import { ConfirmModal } from "@/components/ui/Overlay";
import { toast } from "@/components/ui/Toast";
import { errorMessage } from "@/lib/api";
import { useSetStatus } from "@/lib/queries";
import type { ElectionStatus } from "@/lib/types";

/** Open / pause / close buttons for an election, with feedback. Closing publishes results so it asks first. */
export function StatusActions({ id, title, status, showResults = true }: { id: number; title: string; status: ElectionStatus; showResults?: boolean }) {
  const setStatus = useSetStatus();

  async function change(next: ElectionStatus, done: string) {
    try {
      await setStatus.mutateAsync({ id, status: next });
      toast.success(done);
    } catch (err) {
      toast.error(errorMessage(err, "Could not change the election status."));
      throw err;
    }
  }

  return (
    <div className="flex flex-wrap items-center gap-2">
      {status !== "OPEN" && (
        <Button size="sm" magnetic={false} loading={setStatus.isPending} onClick={() => change("OPEN", `"${title}" is now open for voting`).catch(() => undefined)}>
          <CirclePlay /> Open
        </Button>
      )}
      {status === "OPEN" && (
        <Button size="sm" variant="secondary" loading={setStatus.isPending} onClick={() => change("PAUSED", `"${title}" is paused`).catch(() => undefined)}>
          <CirclePause /> Pause
        </Button>
      )}
      {status !== "CLOSED" && (
        <ConfirmModal
          title="Close this election?"
          description={`Voting on "${title}" stops and the tally becomes visible to voters. You can reopen it later from the election page.`}
          confirmLabel="Close election"
          onConfirm={() => change("CLOSED", `"${title}" is closed`)}
          trigger={
            <Button size="sm" variant="secondary">
              <CircleStop /> Close
            </Button>
          }
        />
      )}
      {showResults && (
        <Button asChild size="sm" variant="ghost" magnetic={false}>
          <Link to={`/app/results/${id}`}>
            <BarChart3 /> Results
          </Link>
        </Button>
      )}
    </div>
  );
}
