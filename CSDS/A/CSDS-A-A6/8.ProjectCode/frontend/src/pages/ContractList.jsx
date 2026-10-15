import { useQuery } from "@tanstack/react-query";
import { FileText, UploadCloud } from "lucide-react";
import { Link, useNavigate } from "react-router";

import { GradeBadge } from "@/components/app/RiskBadges.jsx";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { CardsSkeleton, EmptyState, ErrorState } from "@/components/ui/Feedback";
import { PageHeader } from "@/components/ui/Layout";
import { Table } from "@/components/ui/Table";
import { contractsApi } from "@/lib/api.js";
import { formatDate } from "@/lib/utils";
import { keys } from "@/lib/queries.js";

export default function ContractList() {
  const navigate = useNavigate();
  const query = useQuery({
    queryKey: keys.contracts,
    queryFn: async () => (await contractsApi.list()).data,
  });

  const contracts = query.data ?? [];

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Your contracts"
        title="My contracts"
        description="Every contract you have analysed. Open one for its complexity grade and flagged clauses."
        actions={
          <Button asChild>
            <Link to="/app/upload">
              <UploadCloud /> Upload contract
            </Link>
          </Button>
        }
      />

      {query.isPending && <CardsSkeleton count={3} />}

      {query.isError && (
        <ErrorState
          error={query.error}
          title="Couldn't load your contracts"
          hint="Check that the backend is running, then try again."
          onRetry={() => query.refetch()}
        />
      )}

      {query.isSuccess && contracts.length === 0 && (
        <EmptyState
          icon={<FileText />}
          title="No contracts yet"
          description="Upload a PDF or DOCX to get its clause-by-clause risk report."
          action={
            <Button asChild>
              <Link to="/app/upload">Upload a contract</Link>
            </Button>
          }
        />
      )}

      {query.isSuccess && contracts.length > 0 && (
        <Card className="p-2 sm:p-4">
          <Table
            caption="Your contracts"
            rowKey={(c) => c.id}
            rows={contracts}
            initialSort={{ key: "uploaded", dir: "desc" }}
            onRowClick={(c) => navigate(`/app/contracts/${c.id}`)}
            columns={[
              {
                key: "filename",
                header: "Contract",
                cell: (c) => (
                  <Link to={`/app/contracts/${c.id}`} className="font-medium text-foreground underline-offset-4 hover:underline">
                    {c.filename}
                  </Link>
                ),
                sortValue: (c) => c.filename.toLowerCase(),
              },
              { key: "grade", header: "Grade", cell: (c) => <GradeBadge grade={c.complexity_grade} />, sortValue: (c) => c.complexity_grade },
              {
                key: "flags",
                header: "Flags",
                cell: (c) => c.flag_count,
                align: "right",
                sortValue: (c) => c.flag_count,
              },
              {
                key: "uploaded",
                header: "Uploaded",
                cell: (c) => formatDate(c.uploaded_at, true),
                sortValue: (c) => c.uploaded_at,
                hideOnCard: true,
              },
            ]}
          />
        </Card>
      )}
    </div>
  );
}
