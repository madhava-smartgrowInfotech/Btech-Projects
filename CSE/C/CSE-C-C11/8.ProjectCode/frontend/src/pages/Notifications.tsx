import { useMutation } from "@tanstack/react-query";
import { Link } from "react-router";
import { AlertOctagon, AlertTriangle, BellOff, CheckCheck, CheckCircle2, Info } from "lucide-react";

import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { EmptyState, ErrorState, Skeleton } from "@/components/ui/Feedback";
import { PageHeader } from "@/components/ui/Layout";
import { Timeline } from "@/components/ui/Display";
import { toast } from "@/components/ui/Toast";
import { api, errorMessage } from "@/lib/api";
import { useNotifications, useRefreshData } from "@/lib/queries";
import { cn, formatDate, timeAgo } from "@/lib/utils";

const TONES: Record<string, { icon: typeof Info; cls: string }> = {
  danger: { icon: AlertOctagon, cls: "text-danger" },
  warning: { icon: AlertTriangle, cls: "text-warning" },
  success: { icon: CheckCircle2, cls: "text-success" },
  info: { icon: Info, cls: "text-info" },
};

export default function Notifications() {
  const q = useNotifications();
  const refresh = useRefreshData();
  const readAll = useMutation({
    mutationFn: async () => api.post("/notifications/read-all"),
    onSuccess: async () => {
      toast.success("All notifications marked as read");
      await refresh();
    },
    onError: (e) => toast.error("Could not mark them as read", { description: errorMessage(e) }),
  });

  return (
    <>
      <PageHeader
        title="Notifications"
        description="Budget and goal alerts appear here as your spending changes."
        actions={
          q.data && q.data.unread > 0 && (
            <Button variant="secondary" loading={readAll.isPending} onClick={() => readAll.mutate()}>
              <CheckCheck /> Mark all as read
            </Button>
          )
        }
      />
      {q.isPending ? (
        <div className="space-y-3" role="status" aria-label="Loading notifications">
          {Array.from({ length: 3 }).map((_, i) => (
            <Skeleton key={i} className="h-16 w-full rounded-2xl" />
          ))}
        </div>
      ) : q.isError ? (
        <ErrorState error={q.error} title="Couldn't load notifications" onRetry={() => void q.refetch()} />
      ) : q.data.items.length === 0 ? (
        <EmptyState
          icon={<BellOff />}
          title="No notifications yet"
          description="They show up when a budget passes 75%, 90% or 100%. Set a budget and keep adding transactions."
          action={
            <Button asChild>
              <Link to="/app/budgets">Set a budget</Link>
            </Button>
          }
        />
      ) : (
        <Card className="p-4 sm:p-6">
          <Timeline
            items={q.data.items.map((n) => {
              const tone = TONES[n.type] ?? TONES.info;
              const Icon = tone.icon;
              return {
                icon: <Icon className={cn(tone.cls)} />,
                title: <span className={cn("whitespace-normal", !n.is_read && "font-semibold")}>{n.message}</span>,
                meta: n.created_at ? `${timeAgo(n.created_at)} · ${formatDate(n.created_at, true)}` : undefined,
                trailing: n.is_read ? undefined : <Badge tone="violet">New</Badge>,
              };
            })}
          />
        </Card>
      )}
    </>
  );
}
