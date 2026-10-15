import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { Download } from 'lucide-react'
import api from '../api.js'
import { PageHeader } from '../components/ui/Layout.jsx'
import { Alert, Breadcrumbs, Button, Card, ErrorState, SkeletonBlock, Tabs } from '../components/ui/index.js'
import { useToast } from '../components/ui/Toast.jsx'
import { LANGS, failure } from '../lib/product.js'

const LANG_TABS = Object.entries(LANGS).map(([id, label]) => ({ id, label }))

export default function Report() {
  const { id } = useParams()
  const toast = useToast()
  const [lang, setLang] = useState('en')
  const [url, setUrl] = useState(null)
  const [aiStatus, setAiStatus] = useState('ok')
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(true)
  const [attempt, setAttempt] = useState(0)

  useEffect(() => {
    let objectUrl
    let cancelled = false
    setLoading(true)
    setError(null)
    setUrl(null)
    api
      .get(`/scans/${id}/report`, { params: { lang }, responseType: 'blob' })
      .then((r) => {
        if (cancelled) return
        objectUrl = URL.createObjectURL(new Blob([r.data], { type: 'application/pdf' }))
        setUrl(objectUrl)
        try {
          setAiStatus(JSON.parse(r.headers['x-ai-status'] || '"ok"'))
        } catch {
          setAiStatus('ok')
        }
        toast.success(`${LANGS[lang]} report ready.`)
      })
      .catch(async (e) => {
        if (!cancelled) setError(await failure(e))
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
      if (objectUrl) URL.revokeObjectURL(objectUrl)
    }
    // toast is stable from the provider; only the scan and language should restart the request
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id, lang, attempt])

  return (
    <div className="page">
      <PageHeader
        crumbs={<Breadcrumbs items={[{ to: `/scans/${id}`, label: `Scan #${id}` }, { label: 'Report' }]} />}
        eyebrow="Patient report"
        title="PDF report"
        description={
          <>
            Choose the language, then download. The AI writes the plain-language explanation; the clinician confirms the result before it is shared.{' '}
            <Link to={`/scans/${id}`}>Back to the result</Link>
          </>
        }
        actions={
          url ? (
            <Button variant="primary" icon={Download} href={url} download={`pulmovision_scan${id}_${lang}.pdf`}>
              Download PDF
            </Button>
          ) : (
            <Button variant="primary" icon={Download} disabled>
              Download PDF
            </Button>
          )
        }
      />

      <Tabs tabs={LANG_TABS} value={lang} onChange={setLang} label="Report language" />

      {aiStatus !== 'ok' && url && (
        <Alert tone="warning">The report was generated without the AI explanation: {String(aiStatus)}</Alert>
      )}

      {error && (
        <ErrorState
          title="The report could not be created"
          error={error.message}
          hint="Try again. If it keeps failing, check that the API window is running and that the Gemini key in .env is valid."
          onRetry={() => setAttempt((n) => n + 1)}
        />
      )}

      {!error && loading && (
        <Card>
          <p className="small muted" role="status" style={{ marginBottom: 12 }}>
            Preparing the {LANGS[lang]} report. The AI writes the explanation, so this can take a few seconds.
          </p>
          <SkeletonBlock rows={4} label={`Preparing the ${LANGS[lang]} report`} />
        </Card>
      )}

      {url && <iframe title={`PDF report in ${LANGS[lang]}`} src={url} className="pdf-frame" />}
    </div>
  )
}
