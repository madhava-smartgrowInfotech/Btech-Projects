import { Link, useParams } from 'react-router-dom'
import { ArrowLeft, FileSearch } from 'lucide-react'
import { Button, Container, EmptyState, ErrorState, PageHeader, Skeleton } from '../components/ui'
import AnalysisResult from '../components/AnalysisResult'
import { useAsync } from '../lib/useAsync'
import { api } from '../lib/api'

export default function AnalysisDetail() {
  const { id } = useParams()
  const { data, error, loading, reload } = useAsync(() => api.analysis(id), [id])
  const notFound = error?.status === 404

  return (
    <Container>
      <PageHeader
        crumbs={[{ label: 'Workspace', to: '/app' }, { label: 'History', to: '/app/history' }, { label: `Analysis #${id}` }]}
        title={data?.filename || `Analysis #${id}`}
        description={data ? 'Saved analysis loaded from the history database.' : undefined}
        actions={
          <Button as={Link} to="/app/history" icon={ArrowLeft}>
            Back to history
          </Button>
        }
      />
      {loading && (
        <div aria-busy="true" aria-label="Loading analysis">
          <div className="grid grid-4">
            {[0, 1, 2, 3].map((i) => (
              <Skeleton key={i} height={110} radius="18px" />
            ))}
          </div>
          <Skeleton height={260} style={{ marginTop: 24 }} radius="18px" />
        </div>
      )}
      {notFound && (
        <EmptyState
          icon={FileSearch}
          title="That analysis does not exist"
          actions={
            <Button as={Link} to="/app/history" variant="primary">
              Open history
            </Button>
          }
        >
          Analysis #{id} was not found. It may have been removed, or the link is wrong.
        </EmptyState>
      )}
      {error && !notFound && <ErrorState title="Could not load this analysis" error={error} onRetry={reload} />}
      {data && <AnalysisResult result={data} id={Number(id)} />}
    </Container>
  )
}
