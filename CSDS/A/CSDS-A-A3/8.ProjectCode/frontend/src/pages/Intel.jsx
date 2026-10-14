import { useEffect, useMemo, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { CheckCircle2, CloudDownload, Database, Flag, Hourglass, Radar, RefreshCw, ScanSearch, ShieldAlert, ShieldCheck, XCircle } from 'lucide-react'
import { api } from '../lib/api'
import { useStats } from '../lib/stats'
import { useAsync } from '../lib/useAsync'
import { STATUS, ago, humanize, num, when } from '../lib/format'
import {
  Badge,
  Button,
  Card,
  Container,
  Drawer,
  EmptyState,
  ErrorState,
  IconButton,
  KeyValueList,
  Modal,
  PageHeader,
  ProgressBar,
  SearchField,
  Select,
  Skeleton,
  StatCard,
  Switch,
  Table,
  Timeline,
  Tooltip,
  useToast,
} from '../components/ui'
import { Stagger } from '../components/motion'
import '../styles/pages.css'

const FILTERS = [
  { value: '', label: 'All statuses' },
  { value: 'pending', label: 'Pending' },
  { value: 'confirmed_phishing', label: 'Confirmed phishing' },
  { value: 'confirmed_safe', label: 'Confirmed safe' },
]

function EntryDrawer({ entry, onClose }) {
  const navigate = useNavigate()
  const detail = useAsync(() => (entry ? api.lookup(entry.url_norm) : Promise.resolve(null)), [entry?.url_norm], { enabled: !!entry })
  const e = detail.data?.entry || entry
  return (
    <Drawer open={!!entry} onClose={onClose} title="Threat-intel entry">
      {e && (
        <div className="stack">
          <div>
            <Badge tone={STATUS[e.status]?.tone} dot>
              {STATUS[e.status]?.label || humanize(e.status)}
            </Badge>
            <p className="mono break" style={{ marginTop: 12, fontSize: 14 }}>
              {e.url_norm}
            </p>
          </div>
          <KeyValueList
            items={[
              ['Phishing votes', num(e.phishing_votes)],
              ['Safe votes', num(e.safe_votes)],
              ['Source', e.source],
              ['First seen', when(e.first_seen)],
              ['Last updated', when(e.last_updated)],
              ['Used in training', e.used_in_training ? 'Yes' : 'Not yet'],
            ]}
          />
          <div className="row">
            <Button variant="primary" size="sm" icon={ScanSearch} onClick={() => navigate(`/app/check?url=${encodeURIComponent(e.url_norm)}`)}>
              Check URL
            </Button>
            <Button size="sm" variant="danger" icon={Flag} onClick={() => navigate(`/app/report?url=${encodeURIComponent(e.url_norm)}&verdict=phishing`)}>
              +Phishing
            </Button>
            <Button size="sm" icon={CheckCircle2} onClick={() => navigate(`/app/report?url=${encodeURIComponent(e.url_norm)}&verdict=safe`)}>
              +Safe
            </Button>
          </div>
          <div>
            <h3 style={{ fontSize: 15, margin: '6px 0 14px' }}>Report history</h3>
            {detail.loading ? (
              <div aria-busy="true">
                <Skeleton height={44} />
                <Skeleton height={44} style={{ marginTop: 12 }} />
              </div>
            ) : detail.error ? (
              <ErrorState title="Could not load the report history" error={detail.error} onRetry={detail.reload} />
            ) : detail.data?.entry?.reports?.length ? (
              <Timeline
                items={detail.data.entry.reports.map((r, i) => ({
                  key: i,
                  tone: r.verdict === 'phishing' ? 'danger' : 'safe',
                  title: `${r.verdict === 'phishing' ? 'Phishing' : 'Safe'} · ${r.reporter}`,
                  meta: `${when(r.created_at)} · ${r.source}`,
                  body: r.note || undefined,
                }))}
              />
            ) : (
              <p className="faint">No individual reports recorded.</p>
            )}
            {detail.data?.entry?.reports?.length === 10 && <p className="faint" style={{ marginTop: 10 }}>Showing the 10 most recent reports.</p>}
          </div>
        </div>
      )}
    </Drawer>
  )
}

function SyncModal({ open, onClose, feeds, onSynced }) {
  const [state, setState] = useState({ running: false, result: null, error: null })
  const toast = useToast()
  useEffect(() => {
    if (open) setState({ running: false, result: null, error: null })
  }, [open])

  const run = async () => {
    setState({ running: true, result: null, error: null })
    try {
      const result = await api.sync()
      setState({ running: false, result, error: null })
      const added = Object.values(result).reduce((a, r) => a + (r.ok ? r.added : 0), 0)
      const failed = Object.values(result).filter((r) => !r.ok).length
      toast({
        tone: failed && !added ? 'error' : 'success',
        title: 'Feed sync finished',
        message: `${added} URLs added${failed ? `, ${failed} feed${failed > 1 ? 's' : ''} failed` : ''}.`,
      })
      onSynced()
    } catch (error) {
      setState({ running: false, result: null, error })
    }
  }

  return (
    <Modal
      open={open}
      onClose={onClose}
      dismissable={!state.running}
      title="Sync public phishing feeds"
      footer={
        state.result ? (
          <Button variant="primary" onClick={onClose}>
            Done
          </Button>
        ) : (
          <>
            <Button variant="ghost" onClick={onClose} disabled={state.running}>
              Cancel
            </Button>
            <Button variant="primary" icon={CloudDownload} loading={state.running} onClick={run} data-autofocus>
              {state.error ? 'Try again' : 'Start sync'}
            </Button>
          </>
        )
      }
    >
      {!state.result && !state.running && !state.error && (
        <p>
          Pulls the latest URLs from {feeds?.length ? feeds.join(' and ') : 'OpenPhish and URLhaus'} as <strong>trusted</strong> reports - each one is
          confirmed as phishing immediately. Needs an internet connection; up to 500 URLs per feed.
        </p>
      )}
      {state.running && (
        <div className="stack" style={{ gap: 12 }}>
          <p>Downloading feeds… this can take up to a minute.</p>
          <ProgressBar indeterminate label="Syncing" />
        </div>
      )}
      {state.error && <ErrorState title="Sync request failed" error={state.error} />}
      {state.result && (
        <ul className="feed-results">
          {Object.entries(state.result).map(([name, r]) => (
            <li key={name}>
              {r.ok ? <CheckCircle2 size={18} className="tone-text-safe" aria-hidden="true" /> : <XCircle size={18} className="tone-text-danger" aria-hidden="true" />}
              <div style={{ minWidth: 0 }}>
                <strong>{name}</strong>
                <div className="faint break">{r.ok ? `+${r.added} URLs added` : `failed - ${r.error}`}</div>
              </div>
            </li>
          ))}
        </ul>
      )}
    </Modal>
  )
}

export default function Intel() {
  const { ti, config, refresh, loading: statsLoading } = useStats()
  const [status, setStatus] = useState('')
  const [query, setQuery] = useState('')
  const [live, setLive] = useState(false)
  const [selected, setSelected] = useState(null)
  const [syncOpen, setSyncOpen] = useState(false)
  const navigate = useNavigate()
  const list = useAsync(() => api.intel(200, status || undefined), [status], { poll: live ? 15000 : 0 })

  useEffect(() => {
    if (live) refresh()
  }, [live, list.data, refresh])

  const rows = useMemo(() => {
    const q = query.trim().toLowerCase()
    return (list.data || []).filter((e) => !q || e.url_norm.toLowerCase().includes(q) || e.source.toLowerCase().includes(q))
  }, [list.data, query])

  const stop = (fn) => (e) => {
    e.stopPropagation()
    fn()
  }

  return (
    <Container>
      <PageHeader
        crumbs={[{ label: 'Workspace', to: '/app' }, { label: 'Threat intelligence' }]}
        title="Crowdsourced threat intelligence"
        description={
          ti && config
            ? `Every reported URL, its vote tally and consensus status. Confirmed entries are used to retrain the model; ${ti.awaiting_training} are waiting for the next retrain (automatic after ${config.auto_retrain_every} new confirmations).`
            : 'Every reported URL, its vote tally and consensus status. Confirmed entries are used to retrain the model.'
        }
        actions={
          <>
            <Button icon={RefreshCw} onClick={() => {
                list.reload()
                refresh()
              }}>
              Refresh
            </Button>
            <Button variant="primary" icon={CloudDownload} onClick={() => setSyncOpen(true)}>
              Sync feeds
            </Button>
          </>
        }
      />

      <Stagger className="grid grid-4">
        <StatCard label="URLs tracked" icon={Database} value={ti?.urls_tracked} loading={statsLoading} delta={ti ? `${num(ti.reports)} reports in total` : undefined} />
        <StatCard label="Confirmed phishing" icon={ShieldAlert} tone="danger" value={ti?.confirmed_phishing} loading={statsLoading} />
        <StatCard label="Confirmed safe" icon={ShieldCheck} value={ti?.confirmed_safe} loading={statsLoading} />
        <StatCard
          label="Pending consensus"
          icon={Hourglass}
          tone="warn"
          value={ti?.pending}
          loading={statsLoading}
          delta={ti ? `${ti.awaiting_training} awaiting training` : undefined}
        />
      </Stagger>

      <Card className="mt">
        <div className="toolbar">
          <SearchField value={query} onChange={setQuery} label="Search URLs or sources" placeholder="Search URL or source…" className="toolbar-search" />
          <div className="toolbar-filter">
            <Select label="Status" labelHidden options={FILTERS} value={status} onChange={(e) => setStatus(e.target.value)} />
          </div>
          <Switch label="Auto-refresh" checked={live} onChange={(e) => setLive(e.target.checked)} />
        </div>
        {list.error ? (
          <ErrorState title="Could not load threat intelligence" error={list.error} onRetry={list.reload} />
        ) : (
          <Table
            caption="Threat intelligence entries"
            loading={list.loading && !list.data}
            rows={rows}
            rowKey={(e) => e.url_norm}
            pageSize={12}
            initialSort={{ key: 'last_updated', dir: 'desc' }}
            onRowClick={setSelected}
            empty={
              query || status ? (
                <EmptyState icon={Radar} title="No matching entries" actions={<Button onClick={() => (setQuery(''), setStatus(''))}>Clear filters</Button>}>
                  Nothing matches the current search or status filter.
                </EmptyState>
              ) : (
                <EmptyState
                  icon={Radar}
                  title="No reports yet"
                  actions={
                    <>
                      <Button as={Link} to="/app/check" icon={ScanSearch}>
                        Check a URL
                      </Button>
                      <Button variant="primary" icon={CloudDownload} onClick={() => setSyncOpen(true)}>
                        Sync public feeds
                      </Button>
                    </>
                  }
                >
                  Check a URL and report it, or pull the latest phishing URLs from public feeds.
                </EmptyState>
              )
            }
            columns={[
              { key: 'url_norm', label: 'URL', className: 'url-cell', render: (e) => (e.url_norm.length > 80 ? `${e.url_norm.slice(0, 80)}…` : e.url_norm) },
              {
                key: 'status',
                label: 'Status',
                render: (e) => (
                  <Badge tone={STATUS[e.status]?.tone} dot>
                    {STATUS[e.status]?.label || humanize(e.status)}
                  </Badge>
                ),
              },
              { key: 'phishing_votes', label: 'Phishing', num: true },
              { key: 'safe_votes', label: 'Safe', num: true },
              { key: 'source', label: 'Source' },
              { key: 'last_updated', label: 'Updated', render: (e) => <span className="faint">{ago(e.last_updated)}</span> },
              {
                key: 'actions',
                label: '',
                sortable: false,
                render: (e) => (
                  <span className="row" style={{ gap: 2, flexWrap: 'nowrap' }}>
                    <Tooltip label="Check URL">
                      <IconButton icon={ScanSearch} size="sm" label={`Check ${e.url_norm}`} onClick={stop(() => navigate(`/app/check?url=${encodeURIComponent(e.url_norm)}`))} />
                    </Tooltip>
                    <Tooltip label="+Phishing vote">
                      <IconButton icon={Flag} size="sm" label={`Report ${e.url_norm} as phishing`} onClick={stop(() => navigate(`/app/report?url=${encodeURIComponent(e.url_norm)}&verdict=phishing`))} />
                    </Tooltip>
                    <Tooltip label="+Safe vote">
                      <IconButton icon={CheckCircle2} size="sm" label={`Report ${e.url_norm} as safe`} onClick={stop(() => navigate(`/app/report?url=${encodeURIComponent(e.url_norm)}&verdict=safe`))} />
                    </Tooltip>
                  </span>
                ),
              },
            ]}
          />
        )}
        {list.data?.length === 200 && <div className="table-foot">Showing the 200 most recently updated entries.</div>}
      </Card>

      <EntryDrawer entry={selected} onClose={() => setSelected(null)} />
      <SyncModal
        open={syncOpen}
        onClose={() => setSyncOpen(false)}
        feeds={config?.threat_feeds}
        onSynced={() => {
          list.reload({ quiet: true })
          refresh()
        }}
      />
    </Container>
  )
}
