import { Camera, CameraOff } from 'lucide-react'
import { label as pretty } from '../format'
import { Badge, Card, ScoreBar } from './ui/display'
import { Button } from './ui/controls'
import { ErrorState } from './ui/feedback'
import { Tabs, TabPanel } from './ui/nav'

export const MODES = [
  { id: 'words', label: 'Words · 50 signs' },
  { id: 'letters', label: 'Fingerspelling · A-Z 1-9' },
]

/** Webcam preview with the hand skeleton overlay, FPS / latency readouts and the live top-3 guess. */
export default function CameraView({ rec, mode, setMode, tabsId = 'mode', showLive = true }) {
  const { videoRef, overlayRef, running, starting, error, frame, rtt, start, stop } = rec
  const hint = mode === 'words' ? 'Raise your hands to sign; lower them briefly between signs.' : 'Hold a letter shape steady for about a second.'
  return (
    <div className="space-y-4">
      <Card title="camera.feed" bodyClass="p-0"
        action={running ? (
          <Button size="sm" variant="secondary" icon={CameraOff} onClick={stop}>Stop</Button>
        ) : null}>
        <div className="relative aspect-[4/3] overflow-hidden bg-black">
          <video ref={videoRef} muted playsInline aria-label="Your camera" className="absolute inset-0 h-full w-full -scale-x-100 object-cover" />
          <canvas ref={overlayRef} aria-hidden="true" className="pointer-events-none absolute inset-0 h-full w-full -scale-x-100" />
          {!running && (
            <div className="absolute inset-0 grid place-items-center bg-panel/90 p-6 text-center">
              <div className="max-w-xs">
                <Camera size={26} className="mx-auto mb-3 text-ok" aria-hidden="true" />
                <p className="mb-4 text-sm text-muted">Sit about an arm's length from the camera with your upper body in view. Frames are processed by the local server only.</p>
                <Button icon={Camera} loading={starting} onClick={start}>Start camera</Button>
              </div>
            </div>
          )}
          {running && (
            <>
              <div className="absolute left-2 top-2 flex flex-wrap gap-1.5">
                <Badge tone="neutral" className="bg-black/70"><span className="text-white">{frame?.fps ?? 0} FPS</span></Badge>
                <Badge tone="neutral" className="bg-black/70">
                  <span className="text-white" title="Round trip / server processing">{rtt ?? '-'} ms · srv {frame?.latency_ms?.total ?? '-'} ms</span>
                </Badge>
              </div>
              <div className="absolute right-2 top-2">
                <Badge tone={frame?.hands ? 'ok' : 'neutral'} dot className="bg-black/70"><span className={frame?.hands ? 'text-ok' : 'text-white'}>{frame?.hands ? 'Hands detected' : 'No hands'}</span></Badge>
              </div>
              {mode === 'letters' && frame?.spelling && (
                <div className="absolute bottom-2 left-2 rounded-[4px] border border-ok/60 bg-black/75 px-3 py-1 font-mono text-lg tracking-[0.3em] text-ok" aria-live="polite">{frame.spelling}</div>
              )}
            </>
          )}
        </div>
      </Card>
      {setMode && (
        <div>
          <Tabs id={tabsId} tabs={MODES} value={mode} onChange={setMode} label="Recognition mode" />
          <TabPanel tabsId={tabsId} value={mode} className="pt-2"><p className="text-xs text-dim">{hint}</p></TabPanel>
        </div>
      )}
      {error && <ErrorState compact title="Camera" error={{ message: error, hint: running ? 'Recognition keeps retrying; stop and restart the camera if it persists.' : undefined }} />}
      {showLive && running && (
        <Card title="live guess" eyebrow={mode === 'words' ? 'top 3 signs' : 'top 3 letters'} bodyClass="p-4 space-y-3">
          {frame?.live
            ? frame.live.map((t) => <ScoreBar key={t.label} label={pretty(t.label)} value={t.confidence} display={`${Math.round(t.confidence * 100)}%`} tone="cyan" />)
            : <p className="font-mono text-xs text-dim">waiting for a hand…</p>}
        </Card>
      )}
    </div>
  )
}
