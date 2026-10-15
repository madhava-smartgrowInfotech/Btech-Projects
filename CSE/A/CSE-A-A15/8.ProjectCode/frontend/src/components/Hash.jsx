// Full SHA-256 in a monospace box. ok: true = green (match), false = red (mismatch), undefined = neutral.
export default function Hash({ label, value, ok }) {
  const box = ok === false ? 'border-alert/50 bg-alert/[0.07] text-alert'
    : ok ? 'border-ok/40 bg-ok/[0.07] text-ok'
      : 'border-line bg-panel-2 text-muted'
  return (
    <div>
      <div className="mb-1.5 font-mono text-[11px] uppercase tracking-[0.12em] text-muted">{label}</div>
      <code className={`block break-all rounded-[6px] border px-2.5 py-2 font-mono text-xs ${box}`}>{value}</code>
    </div>
  )
}
