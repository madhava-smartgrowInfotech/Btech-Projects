import { useEffect, useId, useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { CheckCircle2, Flag, History, ScanSearch, Send, ShieldAlert, ShieldCheck, Users } from 'lucide-react'
import { api } from '../lib/api'
import { useStats } from '../lib/stats'
import { STATUS, ago, humanize, num } from '../lib/format'
import {
  Badge,
  Button,
  Card,
  CardHeader,
  Container,
  EmptyState,
  ErrorState,
  Input,
  KeyValueList,
  PageHeader,
  ProgressBar,
  Skeleton,
  Stepper,
  Textarea,
  Timeline,
  useToast,
} from '../components/ui'
import { SlideUp } from '../components/motion'
import '../styles/pages.css'

const VERDICTS = [
  { value: 'phishing', label: 'Phishing / malicious', hint: 'It imitates a brand, steals credentials or delivers malware.', icon: ShieldAlert, tone: 'danger' },
  { value: 'safe', label: 'Safe / legitimate', hint: 'A false positive - this is a genuine site.', icon: ShieldCheck, tone: 'safe' },
]

function useDebounced(value, ms) {
  const [v, setV] = useState(value)
  useEffect(() => {
    const t = setTimeout(() => setV(value), ms)
    return () => clearTimeout(t)
  }, [value, ms])
  return v
}

function CommunityStatus({ url, threshold }) {
  const target = useDebounced(url.trim(), 450)
  const [state, setState] = useState({ loading: false, entry: undefined, error: null })

  useEffect(() => {
    if (!target) {
      setState({ loading: false, entry: undefined, error: null })
      return undefined
    }
    const ctrl = new AbortController()
    setState((s) => ({ ...s, loading: true, error: null }))
    api
      .lookup(target, { signal: ctrl.signal })
      .then((d) => setState({ loading: false, entry: d.entry, error: null }))
      .catch((e) => e.name !== 'AbortError' && setState({ loading: false, entry: undefined, error: e }))
    return () => ctrl.abort()
  }, [target])

  const { loading, entry, error } = state
  return (
    <Card>
      <CardHeader title="Current community status" subtitle="Live tally for the URL you are reporting" />
      <div className="card-body">
        {!target ? (
          <EmptyState icon={Users} title="Enter a URL">
            Its existing reports and consensus progress will appear here.
          </EmptyState>
        ) : loading && entry === undefined ? (
          <div aria-busy="true" aria-label="Loading community status">
            <Skeleton height={18} width="60%" />
            <Skeleton height={10} style={{ margin: '18px 0' }} />
            <Skeleton height={60} />
          </div>
        ) : error ? (
          <ErrorState title="Could not load community status" error={error} />
        ) : !entry ? (
          <EmptyState icon={Users} title="No reports yet">
            Nobody has reported this URL. Your report starts its tally as <strong>pending</strong>.
          </EmptyState>
        ) : (
          <div className="stack" style={{ gap: 16 }}>
            <div className="row" style={{ justifyContent: 'space-between' }}>
              <Badge tone={STATUS[entry.status]?.tone} dot>
                {STATUS[entry.status]?.label || humanize(entry.status)}
              </Badge>
              <span className="faint">source: {entry.source}</span>
            </div>
            <div className="tally">
              <div>
                <strong className="tone-text-danger">{num(entry.phishing_votes)}</strong>
                <span>phishing</span>
              </div>
              <div>
                <strong className="tone-text-safe">{num(entry.safe_votes)}</strong>
                <span>safe</span>
              </div>
              <div>
                <strong>{entry.phishing_votes - entry.safe_votes > 0 ? '+' : ''}{entry.phishing_votes - entry.safe_votes}</strong>
                <span>net</span>
              </div>
            </div>
            {entry.status === 'pending' && (
              <ProgressBar
                label="Progress to consensus"
                value={Math.min(threshold, Math.abs(entry.phishing_votes - entry.safe_votes))}
                max={threshold}
                valueLabel={`${Math.abs(entry.phishing_votes - entry.safe_votes)} / ${threshold} net votes`}
              />
            )}
            {entry.reports?.length > 0 && (
              <>
                <div className="faint row" style={{ gap: 6 }}>
                  <History size={14} aria-hidden="true" /> Latest reports
                </div>
                <Timeline
                  items={entry.reports.map((r, i) => ({
                    key: i,
                    tone: r.verdict === 'phishing' ? 'danger' : 'safe',
                    title: `${r.verdict === 'phishing' ? 'Phishing' : 'Safe'} · ${r.reporter}`,
                    meta: `${ago(r.created_at)} · ${r.source}`,
                    body: r.note || undefined,
                  }))}
                />
              </>
            )}
          </div>
        )}
      </div>
    </Card>
  )
}

export default function Report() {
  const [params] = useSearchParams()
  const navigate = useNavigate()
  const toast = useToast()
  const { config, refresh } = useStats()
  const threshold = config?.consensus_threshold ?? 2
  const [url, setUrl] = useState(params.get('url') || '')
  const [verdict, setVerdict] = useState(params.get('verdict') === 'safe' ? 'safe' : 'phishing')
  const [picked, setPicked] = useState(!!params.get('verdict'))
  const [reporter, setReporter] = useState('')
  const [note, setNote] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState(null)
  const [urlError, setUrlError] = useState(null)
  const groupId = useId()

  const step = !url.trim() ? 0 : !picked ? 1 : 2

  const submit = async (e) => {
    e.preventDefault()
    if (!url.trim()) {
      setUrlError('Enter the URL you want to report.')
      document.getElementById('report-url')?.focus()
      return
    }
    setSubmitting(true)
    setError(null)
    try {
      const entry = await api.report({ url: url.trim(), verdict, reporter: reporter.trim() || 'anonymous', note: note.trim() })
      toast({
        title: 'Report recorded',
        message: `${STATUS[entry.status]?.label || entry.status} · ${entry.phishing_votes} phishing / ${entry.safe_votes} safe votes`,
      })
      refresh()
      // same flow as the original UI: go straight to the check result for the reported URL
      navigate(`/app/check?url=${encodeURIComponent(entry.url_norm)}`)
    } catch (err) {
      setError(err)
      toast({ tone: 'error', title: 'Report not saved', message: err.message })
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <Container>
      <PageHeader
        crumbs={[{ label: 'Workspace', to: '/app' }, { label: 'Report' }]}
        title="Report a URL"
        description={`Crowdsourced reports keep the system current with newly created phishing sites. A URL is confirmed once ${threshold} more people agree than disagree; confirmed URLs override the model instantly and are folded into the next retraining.`}
      />
      <div className="split">
        <SlideUp>
          <Card as="form" onSubmit={submit} noValidate>
            <div className="card-body stack" style={{ gap: 22, paddingTop: 22 }}>
              <Stepper steps={['URL', 'Verdict', 'Details']} current={step} />
              <Input
                id="report-url"
                label="URL"
                mono
                value={url}
                onChange={(e) => {
                  setUrl(e.target.value)
                  setUrlError(null)
                }}
                placeholder="http://example-login.verify.tk/account"
                error={urlError}
                autoComplete="off"
                spellCheck={false}
                required
              />
              <fieldset className="verdict-choice" aria-describedby={`${groupId}-hint`}>
                <legend className="field-label">Your verdict</legend>
                <div className="grid grid-2" style={{ gap: 12 }}>
                  {VERDICTS.map((v) => (
                    <label key={v.value} className={`choice tone-${v.tone} ${verdict === v.value ? 'selected' : ''}`}>
                      <input
                        type="radio"
                        name="verdict"
                        value={v.value}
                        checked={verdict === v.value}
                        onChange={() => {
                          setVerdict(v.value)
                          setPicked(true)
                        }}
                      />
                      <v.icon size={22} aria-hidden="true" />
                      <span>
                        <strong>{v.label}</strong>
                        <span className="faint">{v.hint}</span>
                      </span>
                    </label>
                  ))}
                </div>
                <span id={`${groupId}-hint`} className="sr-only">
                  Choose phishing or safe
                </span>
              </fieldset>
              <Input label="Your name or handle (optional)" value={reporter} onChange={(e) => setReporter(e.target.value)} placeholder="anonymous" maxLength={80} />
              <Textarea
                label="What did you see? (optional)"
                value={note}
                onChange={(e) => setNote(e.target.value)}
                rows={3}
                placeholder="e.g. fake bank login page asking for OTP"
                maxLength={500}
              />
              {error && (
                <div className="inline-error" role="alert">
                  <strong>Report not saved.</strong> {error.message}
                </div>
              )}
              <div className="row" style={{ justifyContent: 'flex-end' }}>
                <Button as={Link} to="/app/check" variant="ghost">
                  Cancel
                </Button>
                {url.trim() && (
                  <Button as={Link} to={`/app/check?url=${encodeURIComponent(url.trim())}`} icon={ScanSearch}>
                    Check it first
                  </Button>
                )}
                <Button type="submit" variant={verdict === 'phishing' ? 'danger' : 'primary'} icon={verdict === 'phishing' ? Flag : Send} loading={submitting}>
                  Submit report
                </Button>
              </div>
            </div>
          </Card>
        </SlideUp>
        <SlideUp delay={0.08}>
          <div className="stack">
            <CommunityStatus url={url} threshold={threshold} />
            <Card pad>
              <h3 style={{ fontSize: 15, marginBottom: 12 }}>How consensus works</h3>
              <KeyValueList
                items={[
                  ['Confirm phishing', `net phishing votes ≥ ${threshold}`],
                  ['Confirm safe', `net safe votes ≥ ${threshold}`],
                  ['Trusted feeds', 'confirm phishing on first report'],
                  ['Auto-retrain', config ? `after ${config.auto_retrain_every} new confirmations` : '-'],
                  ['Training weight', config ? `confirmed URLs count ×${config.crowd_sample_weight}` : '-'],
                ]}
              />
              <p className="faint" style={{ marginTop: 14 }}>
                <CheckCircle2 size={13} style={{ display: 'inline', verticalAlign: -2 }} aria-hidden="true" /> Pending reports still nudge the model score by ±15% per net vote.
              </p>
            </Card>
          </div>
        </SlideUp>
      </div>
    </Container>
  )
}
