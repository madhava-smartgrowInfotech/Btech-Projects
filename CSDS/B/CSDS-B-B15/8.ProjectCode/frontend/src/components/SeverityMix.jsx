import { SEVERITIES, SEVERITY_VAR } from '../format'

/** Segmented bar + count per triage level. counts: { mild, moderate, severe, critical } */
export default function SeverityMix({ counts = {}, showLegend = true, height = 'h-3' }) {
  const total = SEVERITIES.reduce((s, l) => s + (counts[l] || 0), 0)
  return (
    <div>
      <div className={`flex w-full ${height} overflow-hidden rounded-[3px] bg-panel-2`} role="img"
        aria-label={total ? SEVERITIES.map((l) => `${counts[l] || 0} ${l}`).join(', ') : 'No bookings'}>
        {total > 0 &&
          SEVERITIES.map((l) =>
            counts[l] ? <div key={l} title={`${l}: ${counts[l]}`} style={{ width: `${(100 * counts[l]) / total}%`, background: SEVERITY_VAR[l] }} /> : null,
          )}
      </div>
      {showLegend && (
        <ul className="mt-2 grid grid-cols-2 gap-x-3 gap-y-1 font-mono text-[11px] text-muted">
          {SEVERITIES.map((l) => (
            <li key={l} className="flex items-center gap-2">
              <span className="h-2 w-2 rounded-[2px]" style={{ background: SEVERITY_VAR[l] }} aria-hidden="true" />
              <span className="flex-1 capitalize">{l}</span>
              <span className="tabular-nums text-fg">{counts[l] || 0}</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
