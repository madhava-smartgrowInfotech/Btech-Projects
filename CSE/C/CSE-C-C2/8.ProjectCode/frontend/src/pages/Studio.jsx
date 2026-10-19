import { useEffect, useRef, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { BookOpen, ExternalLink, Sparkles } from 'lucide-react'
import { Alert, Button, Card, Checkbox, EmptyState, ErrorState, PageHeader, Select, SkeletonBlock, Textarea, useToast } from '../components/ui'
import StoryView from '../components/story/StoryView'
import { api } from '../lib/api'
import { useMeta } from '../lib/meta'

const MAX_PROMPT = 2000 // backend MAX_PROMPT_CHARS default

function useElapsed(running) {
  const [sec, setSec] = useState(0)
  useEffect(() => {
    if (!running) return undefined
    const start = Date.now()
    setSec(0)
    const t = setInterval(() => setSec(Math.floor((Date.now() - start) / 1000)), 500)
    return () => clearInterval(t)
  }, [running])
  return sec
}

export default function Studio() {
  const toast = useToast()
  const { loading, error, languages, styles, lengths, reload } = useMeta()
  const [params, setParams] = useSearchParams()
  const [form, setForm] = useState({ prompt: '', language_code: 'en', style: 'Adventure', length_option: 'Short', synthesize: true })
  const [fieldError, setFieldError] = useState('')
  const [busy, setBusy] = useState(false)
  const [failure, setFailure] = useState(null)
  const [story, setStory] = useState(null)
  const [restoring, setRestoring] = useState(false)
  const resultRef = useRef(null)
  const elapsed = useElapsed(busy)
  const set = (k) => (v) => setForm((f) => ({ ...f, [k]: v }))

  // A story id in the URL (?story=12) restores the last result after a reload or when coming back from history.
  const storyParam = params.get('story')
  useEffect(() => {
    if (!storyParam || (story && String(story.id) === storyParam)) return
    setRestoring(true)
    api.story(storyParam).then(setStory, () => setParams({}, { replace: true })).finally(() => setRestoring(false))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [storyParam])

  async function submit(e) {
    e?.preventDefault?.()
    if (!form.prompt.trim()) {
      setFieldError('Please enter a story idea.')
      return
    }
    setFieldError('')
    setFailure(null)
    setBusy(true)
    try {
      const made = await api.generate(form)
      setStory(made)
      setParams({ story: made.id }, { replace: true })
      toast.success(made.audio ? 'Story and narration are ready.' : 'Story is ready. Generate narration to hear it.')
      requestAnimationFrame(() => resultRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' }))
    } catch (err) {
      setFailure(err.message)
      toast.error(err.message)
    } finally {
      setBusy(false)
    }
  }

  const over = form.prompt.length > MAX_PROMPT - 100

  return (
    <>
      <PageHeader eyebrow="Studio" title="Write & narrate" description="Share an idea, pick a language and style. StoryVox writes an original story and reads it aloud." />
      <div className="studio-grid">
        <Card title="Your story idea" as="form" onSubmit={submit} noValidate>
          {loading ? (
            <SkeletonBlock rows={5} label="Loading languages and styles" />
          ) : error ? (
            <ErrorState title="Could not load options" error={error} onRetry={reload} />
          ) : (
            <div className="stack" style={{ '--gap': '18px' }}>
              <Textarea
                label="Story idea"
                rows={6}
                maxLength={MAX_PROMPT}
                value={form.prompt}
                onChange={(e) => {
                  set('prompt')(e.target.value)
                  if (fieldError) setFieldError('')
                }}
                placeholder="A young inventor discovers a hidden library…"
                error={fieldError}
                hint={<span className={`char-count ${over ? 'warn' : ''}`}>{form.prompt.length} / {MAX_PROMPT} characters</span>}
                disabled={busy}
              />
              <Select
                label="Language"
                value={form.language_code}
                onChange={(e) => set('language_code')(e.target.value)}
                disabled={busy}
                options={languages.map((l) => ({ value: l.code, label: `${l.name} (${l.code})` }))}
              />
              <div className="form-row">
                <Select label="Style" value={form.style} onChange={(e) => set('style')(e.target.value)} disabled={busy} options={styles.map((s) => ({ value: s, label: s }))} />
                <Select label="Length" value={form.length_option} onChange={(e) => set('length_option')(e.target.value)} disabled={busy} options={lengths.map((s) => ({ value: s, label: s }))} />
              </div>
              <Checkbox label="Narrate the story automatically" checked={form.synthesize} onChange={set('synthesize')} disabled={busy} />
              <Button type="submit" variant="primary" size="lg" block icon={Sparkles} loading={busy}>
                {busy ? 'Working…' : 'Generate story'}
              </Button>
              <p className="tiny muted">Privacy: stories and narration are stored locally on this computer for history and playback.</p>
            </div>
          )}
        </Card>

        <div ref={resultRef} style={{ scrollMarginTop: 80, minWidth: 0 }}>
          {busy ? (
            <Card className="busy-card" aria-busy="true">
              <span className="eyebrow">In progress</span>
              <span className="elapsed" role="timer" aria-label="Elapsed time">
                {elapsed}s
              </span>
              <div className="progress progress-indeterminate" role="progressbar" aria-label="Generating story" />
              <p className="small muted" role="status">
                Writing your story{form.synthesize ? ' and preparing narration' : ''}… the first run in a language can take a few minutes while models load.
              </p>
              <SkeletonBlock rows={4} label="Story is being written" />
            </Card>
          ) : failure ? (
            <ErrorState
              title="Story could not be generated"
              error={failure}
              hint="Check your idea and options, then try again. If it keeps failing, look at the backend console window."
              onRetry={() => submit()}
            />
          ) : restoring ? (
            <Card>
              <SkeletonBlock rows={5} label="Loading story" />
            </Card>
          ) : story ? (
            <>
              <Card
                title="Your story"
                actions={
                  <Button size="sm" to={`/stories/${story.id}`} iconRight={ExternalLink}>
                    Open page
                  </Button>
                }
              >
                <StoryView story={story} onChange={setStory} />
              </Card>
              {story.audio === null && (
                <div style={{ marginTop: 16 }}>
                  <Alert tone="info">Narration was skipped or failed. Use “Generate narration” above to try again.</Alert>
                </div>
              )}
            </>
          ) : (
            <EmptyState icon={BookOpen} title="No story yet" action={<Link className="small" to="/stories">Or revisit a past story in History</Link>}>
              Write an idea on the left and press Generate story. Your story and its narration will appear here.
            </EmptyState>
          )}
        </div>
      </div>
    </>
  )
}
