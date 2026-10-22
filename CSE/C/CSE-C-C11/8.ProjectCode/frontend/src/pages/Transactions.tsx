import { FileSpreadsheet, List, Plus } from "lucide-react";
import { useSearchParams } from "react-router";

import { AddTransactionForm } from "@/components/transactions/AddTransactionForm";
import { ImportPanel } from "@/components/transactions/ImportPanel";
import { TransactionsList } from "@/components/transactions/TransactionsList";
import { ErrorState, Skeleton } from "@/components/ui/Feedback";
import { PageHeader } from "@/components/ui/Layout";
import { TabPanel, Tabs } from "@/components/ui/Navigation";
import { useMeta } from "@/lib/queries";

const TABS = ["add", "manage", "import"] as const;

export default function Transactions() {
  const [params, setParams] = useSearchParams();
  const tab = TABS.includes(params.get("tab") as (typeof TABS)[number]) ? (params.get("tab") as string) : "add";
  const meta = useMeta();

  return (
    <>
      <PageHeader title="Transactions" description="Record what comes in and goes out, review it, or bring in a whole statement." />
      <Tabs
        value={tab}
        onValueChange={(v) => setParams({ tab: v }, { replace: true })}
        tabs={[
          { value: "add", label: "Add", icon: <Plus /> },
          { value: "manage", label: "View / manage", icon: <List /> },
          { value: "import", label: "Import", icon: <FileSpreadsheet /> },
        ]}
      >
        {meta.isError ? (
          <ErrorState error={meta.error} title="Couldn't load the form options" onRetry={() => void meta.refetch()} className="mt-5" />
        ) : !meta.data ? (
          <div className="mt-5 space-y-3" role="status" aria-label="Loading">
            <Skeleton className="h-10 w-full" />
            <Skeleton className="h-64 w-full rounded-2xl" />
          </div>
        ) : (
          <>
            <TabPanel value="add">
              <AddTransactionForm meta={meta.data} />
            </TabPanel>
            <TabPanel value="manage">
              <TransactionsList meta={meta.data} />
            </TabPanel>
            <TabPanel value="import">
              <ImportPanel />
            </TabPanel>
          </>
        )}
      </Tabs>
    </>
  );
}
