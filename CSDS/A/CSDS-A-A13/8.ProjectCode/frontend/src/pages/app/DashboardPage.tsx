import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { Grid3x3, Hash, Settings, Shuffle } from "lucide-react";
import { PageHeader } from "@/components/common/PageHeader";
import { CardsSkeleton, ErrorState } from "@/components/common/States";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { Rules } from "@/lib/types";

function greeting() {
  const hour = new Date().getHours();
  return hour < 12 ? "Good morning" : hour < 18 ? "Good afternoon" : "Good evening";
}

export default function DashboardPage() {
  const { user } = useAuth();
  const rules = useQuery({ queryKey: ["rules"], queryFn: async () => (await api.get<Rules>("/settings/rules")).data });

  return (
    <>
      <PageHeader title={`${greeting()}, ${user?.full_name.split(" ")[0]}`} description="Your seating workspace at a glance." />
      {rules.isPending && <CardsSkeleton count={3} />}
      {rules.isError && <ErrorState error={rules.error} onRetry={() => rules.refetch()} />}
      {rules.data && (
        <Card>
          <CardHeader className="flex-row items-center justify-between">
            <CardTitle>Seating rules in force</CardTitle>
            {user?.role === "admin" && (
              <Button asChild variant="outline" size="sm">
                <Link to="/app/settings">
                  <Settings /> Change
                </Link>
              </Button>
            )}
          </CardHeader>
          <CardContent className="grid gap-3 sm:grid-cols-3">
            <div className="flex items-center gap-3 rounded-lg bg-muted/60 p-3">
              <Grid3x3 className="size-5 text-primary" aria-hidden />
              <div>
                <div className="text-sm font-medium">{rules.data.adjacency} neighbours</div>
                <div className="text-xs text-muted-foreground">never share a paper</div>
              </div>
            </div>
            <div className="flex items-center gap-3 rounded-lg bg-muted/60 p-3">
              <Hash className="size-5 text-primary" aria-hidden />
              <div>
                <div className="text-sm font-medium">{rules.data.roll_gap ? `Roll gap ${rules.data.roll_gap}` : "No roll gap"}</div>
                <div className="text-xs text-muted-foreground">between neighbours</div>
              </div>
            </div>
            <div className="flex items-center gap-3 rounded-lg bg-muted/60 p-3">
              <Shuffle className="size-5 text-primary" aria-hidden />
              <div>
                <div className="text-sm font-medium">{rules.data.department_mix ? "Department mix on" : "Department mix off"}</div>
                <div className="text-xs text-muted-foreground">{rules.data.fill_strategy} hall usage</div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </>
  );
}
