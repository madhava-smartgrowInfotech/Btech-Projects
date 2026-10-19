import { useState } from 'react'
import { Download, Mic, RefreshCw } from 'lucide-react'
import { Alert, Badge, Button, KeyValueList, useToast } from '../ui'
import { api, audioUrl } from '../../lib/api'
import { fmtDuration, fmtMinutes, fmtNum, plural } from '../../lib/format'

/** A generated story: title, badges, body, narration player with download / regenerate. */
export default function StoryView({ story, onChange, showDetails = false, hideTitle = false }) {
  const toast = useToast()
  const [busy, setBusy] = useState(false)
  const [audioError, setAudioError] = useState(false)
  const [error, setError] = useState(null)
  const audio = story.audio

  async function narrate() {
    setBusy(true)
    setError(null)
    setAudioError(false)
    try {
      const fresh = await api.synthesize(story.id)
      onChange({ ...story, audio: fresh, listening_time_minutes: fresh.duration_seconds / 60 })
      toast.success('Fresh narration is ready.')
    } catch (e) {
      setError(e.message)
      toast.error(e.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="stack" style={{ '--gap': '22px' }}>
      <div className="stack" style={{ '--gap': '12px' }}>
        {!hideTitle && (
          <h2 className="story-title" dir="auto">
            {story.title}
          </h2>
        )}
        <div className="story-meta">
          <Badge tone="info">{story.language_name}</Badge>
          <Badge>{story.style}</Badge>
          <Badge>{story.length_option}</Badge>
          <Badge>{plural(story.word_count, 'word')}</Badge>
          <Badge>{fmtMinutes(story.listening_time_minutes)} listen</Badge>
          <Badge>written in {fmtDuration(story.generation_time_seconds)}</Badge>
        </div>
      </div>

      <section className="player" aria-label="Narration">
        <div className="player-head">
          <strong className="row" style={{ '--gap': '8px' }}>
            <Mic size={18} aria-hidden="true" /> Narration
          </strong>
          <div className="row">
            {audio && (
              <Button size="sm" icon={Download} href={audioUrl(audio.id)} download={`storyvox_${story.id}.wav`}>
                Download WAV
              </Button>
            )}
            <Button size="sm" icon={RefreshCw} loading={busy} onClick={narrate}>
              {audio ? 'Regenerate narration' : 'Generate narration'}
            </Button>
          </div>
        </div>
        {audio ? (
          <>
            <audio key={audio.id} controls preload="metadata" src={audioUrl(audio.id)} onError={() => setAudioError(true)} aria-label={`Narration of ${story.title}`} />
            {audioError && <Alert tone="warning">The audio file could not be played - it may have been removed from disk. Regenerate the narration.</Alert>}
            <span className="tiny mono muted">
              {fmtDuration(audio.duration_seconds)} · {audio.sample_rate} Hz · voice {audio.tts_model}
            </span>
          </>
        ) : (
          <Alert tone="warning">
            No narration yet. Generate it to listen to this story.
          </Alert>
        )}
        {error && <Alert tone="error">{error}</Alert>}
      </section>

      <p className="story-text" dir="auto">{story.story_text}</p>

      {showDetails && (
        <KeyValueList
          items={[
            { label: 'Your idea', value: story.prompt },
            { label: 'Created', value: new Date(story.created_at).toLocaleString() },
            { label: 'Reading time', value: fmtMinutes(story.reading_time_minutes) },
            { label: 'Narration model', value: audio?.tts_model },
            { label: 'Synthesis time', value: audio ? fmtDuration(audio.synthesis_time_seconds) : undefined },
            { label: 'Real-time factor', value: audio ? fmtNum(audio.rtf, 3) : undefined },
          ]}
        />
      )}
    </div>
  )
}
