import { useCallback, useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { ArrowLeft, Trash2 } from 'lucide-react'
import { Alert, Breadcrumbs, Button, Card, ErrorState, KeyValueList, PageHeader, SkeletonBlock, useToast } from '../components/ui'
import { DISCLAIMER_TEXT, EvidenceList, SafetyBadge } from '../components/app/Evidence'
import { ConfirmDelete } from './History'
import { historyApi } from '../lib/api'
import { fmtDate, pct } from '../lib/format'

export default function ConsultationDetail() {
  const { id } = useParams()
  const nav = useNavigate()
  const toast = useToast()
  const [state, setState] = useState({ loading: true, error: null, item: null })
  const [confirm, setConfirm] = useState(false)
  const [deleting, setDeleting] = useState(false)

  const load = useCallback(() => {
    setState({ loading: true, error: null, item: null })
    historyApi
      .get(id)
      .then((item) => setState({ loading: false, error: null, item }))
      .catch((e) => {
        setState({ loading: false, error: e, item: null })
      })
  }, [id])

  useEffect(() => {
    document.title = `Consultation #${id} - CareLens AI`
    load()
  }, [id, load])

  const remove = async () => {
    setDeleting(true)
    try {
      await historyApi.remove(id)
      toast.success(`Consultation #${id} deleted.`)
      nav('/history', { replace: true })
    } catch (e) {
      toast.error(`Could not delete: ${e.message}`)
      setDeleting(false)
    }
  }

  const crumbs = <Breadcrumbs items={[{ label: 'History', to: '/history' }, { label: `#${id}` }]} />
  const { loading, error, item } = state

  if (loading) {
    return (
      <>
        <PageHeader crumbs={crumbs} title={`Consultation #${id}`} />
        <SkeletonBlock rows={6} label="Loading consultation" />
      </>
    )
  }
  if (error) {
    return (
      <>
        <PageHeader crumbs={crumbs} title={`Consultation #${id}`} />
        <ErrorState
          title={error.status === 404 ? 'Consultation not found' : 'Could not load this consultation'}
          error={error}
          hint={error.status === 404 ? 'It may have been deleted. Go back to your history to pick another one.' : undefined}
          onRetry={error.status === 404 ? undefined : load}
        />
        <div style={{ marginTop: 16 }}>
          <Button icon={ArrowLeft} to="/history">
            Back to history
          </Button>
        </div>
      </>
    )
  }

  return (
    <>
      <PageHeader
        crumbs={crumbs}
        eyebrow="Consultation"
        title={item.top_condition || `Consultation #${item.id}`}
        description={fmtDate(item.created_at)}
        actions={
          <>
            <Button icon={ArrowLeft} to="/history">
              Back
            </Button>
            <Button variant="danger" icon={Trash2} onClick={() => setConfirm(true)}>
              Delete
            </Button>
          </>
        }
      />
      <div className="stack" style={{ '--gap': '24px' }}>
        {item.safety_flag === 'emergency' && <Alert tone="error">This consultation was flagged as an emergency. If symptoms are ongoing, seek urgent medical care now.</Alert>}
        {item.safety_flag === 'caution' && <Alert tone="warning">This consultation mentioned potentially serious symptoms. Consider contacting a healthcare professional.</Alert>}
        <Card title="Summary">
          <KeyValueList
            items={[
              { label: 'Symptoms', value: item.symptom_query },
              { label: 'Safety', value: <SafetyBadge flag={item.safety_flag} /> },
              { label: 'Top relevance', value: pct(item.retrieval_score) },
              { label: 'Consultation', value: `#${item.id}` },
            ]}
          />
        </Card>
        <Card title="Assistant answer">
          <div className="answer">{item.generated_response}</div>
        </Card>
        <EvidenceList items={item.retrieved_evidence} />
        <p className="disclaimer">{DISCLAIMER_TEXT}</p>
      </div>
      <ConfirmDelete target={confirm ? item : null} busy={deleting} onCancel={() => setConfirm(false)} onConfirm={remove} />
    </>
  )
}
