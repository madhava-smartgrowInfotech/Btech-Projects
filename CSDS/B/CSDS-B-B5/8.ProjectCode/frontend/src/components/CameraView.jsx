import { Camera, CameraOff, Loader2 } from 'lucide-react'
import { ConfidenceBar, ErrorBox } from './ui.jsx'

export default function CameraView({ rec, mode, setMode, showLive = true }) {
  const { videoRef, overlayRef, running, starting, error, frame, rtt, start, stop } = rec
  return (
    <div className="space-y-3">
      <div className="relative aspect-[4/3] bg-slate-900 rounded-2xl overflow-hidden">
        <video ref={videoRef} muted playsInline className="absolute inset-0 w-full h-full object-cover -scale-x-100" />
        <canvas ref={overlayRef} className="absolute inset-0 w-full h-full -scale-x-100 pointer-events-none" />
        {!running && (
          <div className="absolute inset-0 grid place-items-center text-center p-6">
            <div>
              <p className="text-slate-300 text-sm mb-3">Sit about an arm's length from the camera with your upper body in view.</p>
              <button className="btn-primary" onClick={start} disabled={starting}>
                {starting ? <Loader2 size={16} className="animate-spin" /> : <Camera size={16} />} Start camera
              </button>
            </div>
          </div>
        )}
        {running && (
          <>
            <div className="absolute top-2 left-2 flex gap-1.5">
              <span className="chip bg-black/60 text-white">{frame?.fps ?? 0} FPS</span>
              <span className="chip bg-black/60 text-white" title="Round trip / server processing">
                {rtt ?? '-'} ms · server {frame?.latency_ms?.total ?? '-'} ms
              </span>
            </div>
            <div className="absolute top-2 right-2">
              <span className={`chip ${frame?.hands ? 'bg-emerald-500 text-white' : 'bg-black/60 text-slate-200'}`}>
                {frame?.hands ? 'Hands detected' : 'No hands'}
              </span>
            </div>
            {mode === 'letters' && frame?.spelling && (
              <div className="absolute bottom-2 left-2 chip bg-indigo-600 text-white text-base !px-3 !py-1 tracking-widest">{frame.spelling}</div>
            )}
            <button className="absolute bottom-2 right-2 btn-secondary !py-1 !px-2 !text-xs" onClick={stop}><CameraOff size={14} /> Stop</button>
          </>
        )}
      </div>
      {setMode && (
        <div className="flex rounded-xl bg-slate-100 p-1 text-sm font-medium">
          {[['words', 'Words (50 signs)'], ['letters', 'Fingerspelling A-Z, 1-9']].map(([m, label]) => (
            <button key={m} onClick={() => setMode(m)}
              className={`flex-1 rounded-lg py-1.5 ${mode === m ? 'bg-white shadow-sm text-indigo-700' : 'text-slate-600'}`}>{label}</button>
          ))}
        </div>
      )}
      <ErrorBox error={error} />
      {showLive && running && (
        <div className="card p-3 space-y-2">
          <div className="text-xs font-semibold uppercase tracking-wide text-slate-500">Live guess</div>
          {frame?.live ? frame.live.map((t) => <ConfidenceBar key={t.label} label={t.label} value={t.confidence} />)
            : <p className="text-xs text-slate-400">{mode === 'words' ? 'Raise your hands to sign; lower them briefly between signs.' : 'Hold a letter shape steady for a moment.'}</p>}
        </div>
      )}
    </div>
  )
}
