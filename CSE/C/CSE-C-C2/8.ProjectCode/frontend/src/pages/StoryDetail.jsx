import { useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { Library, Trash2 } from 'lucide-react'
import { Breadcrumbs, Button, Card, EmptyState, ErrorState, Modal, PageHeader, SkeletonBlock, Tabs, useToast } from '../components/ui'
import StoryView from '../components/story/StoryView'
import { api } from '../lib/api'
import { useAsync } from '../lib/useAsync'

export default function StoryDetail() {
  const { id } = useParams()
  const nav = useNavigate()
  const toast = useToast()
  const { loading, error, data, reload, setData } = useAsync(() => api.story(id), [id])
  const [tab, setTab] = useState('story')
  const [confirm, setConfirm] = useState(false)
  const [deleting, setDeleting] = useState(false)

  async function remove() {
    setDeleting(true)
    try {
      await api.deleteStory(id)
      toast.success('Story deleted.')
      nav('/stories')
    } catch (e) {
      toast.error(e.message)
      setDeleting(false)
    }
  }

  const crumbs = <Breadcrumbs items={[{ label: 'History', to: '/stories' }, { label: data ? data.title : `Story ${id}` }]} />

  if (loading && !data) {
    return (
      <>
        <PageHeader crumbs={crumbs} title="Loading…" />
        <Card>
          <SkeletonBlock rows={6} label="Loading story" />
        </Card>
      </>
    )
  }
  if (error?.status === 404) {
    return (
      <EmptyState icon={Library} title="Story not found" action={<Button variant="primary" to="/stories">Back to history</Button>}>
        It may have been deleted.
      </EmptyState>
    )
  }
  if (error) return <ErrorState title="Could not load this story" error={error} onRetry={reload} />

  return (
    <>
      <PageHeader
        crumbs={crumbs}
        eyebrow={`Story #${data.id}`}
        title={data.title}
        actions={
          <Button variant="danger" icon={Trash2} onClick={() => setConfirm(true)}>
            Delete
          </Button>
        }
      />
      <Tabs label="Story sections" value={tab} onChange={setTab} tabs={[{ id: 'story', label: 'Story' }, { id: 'details', label: 'Details' }]} />
      <Card>
        <StoryView story={data} onChange={setData} showDetails={tab === 'details'} hideTitle />
      </Card>
      <Modal
        open={confirm}
        onClose={() => !deleting && setConfirm(false)}
        title="Delete this story?"
        footer={
          <>
            <Button onClick={() => setConfirm(false)} disabled={deleting} data-autofocus>
              Keep it
            </Button>
            <Button variant="danger" icon={Trash2} loading={deleting} onClick={remove}>
              Delete story
            </Button>
          </>
        }
      >
        <p>“{data.title}” and its narration audio will be permanently removed from this computer.</p>
      </Modal>
    </>
  )
}
