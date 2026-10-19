import { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Download, Eye, Library, PenLine, Play, RefreshCw, Trash2, X } from 'lucide-react'
import { Badge, Button, EmptyState, ErrorState, Modal, PageHeader, SearchField, SkeletonBlock, Table, useToast } from '../components/ui'
import { api, audioUrl } from '../lib/api'
import { fmtDate, fmtInt } from '../lib/format'
import { useAsync } from '../lib/useAsync'

export default function History() {
  const nav = useNavigate()
  const toast = useToast()
  const { loading, error, data, reload, setData } = useAsync(() => api.stories(200), [])
  const [q, setQ] = useState('')
  const [playing, setPlaying] = useState(null)
  const [toDelete, setToDelete] = useState(null)
  const [deleting, setDeleting] = useState(false)

  const rows = useMemo(() => {
    const needle = q.trim().toLowerCase()
    const all = data || []
    return needle ? all.filter((s) => `${s.title} ${s.language_name} ${s.style}`.toLowerCase().includes(needle)) : all
  }, [data, q])

  async function confirmDelete() {
    setDeleting(true)
    try {
      await api.deleteStory(toDelete.id)
      setData((data || []).filter((s) => s.id !== toDelete.id))
      if (playing?.id === toDelete.id) setPlaying(null)
      toast.success(`Deleted “${toDelete.title}” and its audio.`)
      setToDelete(null)
    } catch (e) {
      toast.error(e.message)
    } finally {
      setDeleting(false)
    }
  }

  const stop = (e) => e.stopPropagation()
  const columns = [
    { key: 'title', label: 'Story', render: (s) => <span className="cell-title">{s.title}</span> },
    { key: 'language_name', label: 'Language' },
    { key: 'style', label: 'Style', render: (s) => <Badge>{s.style}</Badge> },
    { key: 'word_count', label: 'Words', numeric: true, render: (s) => fmtInt(s.word_count) },
    { key: 'created_at', label: 'Created', render: (s) => fmtDate(s.created_at) },
    { key: 'has_audio', label: 'Audio', sortValue: (s) => (s.has_audio ? 1 : 0), render: (s) => (s.has_audio ? <Badge tone="pass">Available</Badge> : <Badge>None</Badge>) },
    {
      key: 'actions',
      label: 'Actions',
      sortable: false,
      render: (s) => (
        <div className="row-actions" onClick={stop} onKeyDown={stop}>
          <Button size="sm" icon={Eye} onClick={() => nav(`/stories/${s.id}`)} aria-label={`View ${s.title}`}>
            View
          </Button>
          <Button size="sm" icon={Play} disabled={!s.has_audio} onClick={() => setPlaying(s)} aria-label={`Play ${s.title}`}>
            Play
          </Button>
          {s.has_audio ? (
            <Button size="sm" icon={Download} href={audioUrl(s.audio_id)} download={`storyvox_${s.id}.wav`} aria-label={`Download ${s.title}`}>
              Download
            </Button>
          ) : (
            <Button size="sm" icon={Download} disabled aria-label={`Download ${s.title} (no audio)`}>
              Download
            </Button>
          )}
          <Button size="sm" variant="danger" icon={Trash2} onClick={() => setToDelete(s)} aria-label={`Delete ${s.title}`}>
            Delete
          </Button>
        </div>
      ),
    },
  ]

  return (
    <>
      <PageHeader
        eyebrow="History"
        title="Story library"
        description="Every story you have generated on this computer. Play, download or delete them."
        actions={
          <>
            <Button icon={RefreshCw} onClick={reload} loading={loading && !!data}>
              Refresh
            </Button>
            <Button variant="primary" icon={PenLine} to="/studio">
              New story
            </Button>
          </>
        }
      />

      {playing && (
        <div className="now-playing" role="region" aria-label="Now playing">
          <div className="row-between">
            <strong>Now playing: {playing.title}</strong>
            <Button size="sm" icon={X} onClick={() => setPlaying(null)} aria-label="Close player">
              Close
            </Button>
          </div>
          <audio key={playing.audio_id} controls autoPlay src={audioUrl(playing.audio_id)} aria-label={`Narration of ${playing.title}`} />
        </div>
      )}

      {loading && !data ? (
        <SkeletonBlock rows={6} label="Loading stories" />
      ) : error ? (
        <ErrorState title="Could not load your stories" error={error} onRetry={reload} />
      ) : !data.length ? (
        <EmptyState
          icon={Library}
          title="No stories yet"
          action={
            <Button variant="primary" icon={PenLine} to="/studio">
              Create your first story
            </Button>
          }
        >
          Stories you generate are saved here with their narration.
        </EmptyState>
      ) : (
        <>
          <div className="toolbar">
            <SearchField value={q} onChange={setQ} label="Search stories" placeholder="Search by title, language or style" />
            <span className="small mono muted" aria-live="polite">
              {rows.length} of {data.length}
            </span>
          </div>
          <Table
            columns={columns}
            rows={rows}
            pageSize={8}
            initialSort={{ key: 'created_at', dir: 'desc' }}
            caption="Generated stories"
            onRowClick={(s) => nav(`/stories/${s.id}`)}
            empty={
              <EmptyState title="No matches" action={<Button onClick={() => setQ('')}>Clear search</Button>}>
                No story matches “{q}”.
              </EmptyState>
            }
          />
        </>
      )}

      <Modal
        open={!!toDelete}
        onClose={() => !deleting && setToDelete(null)}
        title="Delete this story?"
        footer={
          <>
            <Button onClick={() => setToDelete(null)} disabled={deleting} data-autofocus>
              Keep it
            </Button>
            <Button variant="danger" icon={Trash2} loading={deleting} onClick={confirmDelete}>
              Delete story
            </Button>
          </>
        }
      >
        <p>“{toDelete?.title}” and its narration audio will be permanently removed from this computer.</p>
      </Modal>
    </>
  )
}
