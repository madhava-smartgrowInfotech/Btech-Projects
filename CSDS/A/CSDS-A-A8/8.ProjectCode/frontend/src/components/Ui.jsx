import { AlertTriangle, FileText, Loader2, Sparkles } from 'lucide-react'

export function Spinner({ text = 'Working...' }) {
  return (
    <div className="flex items-center gap-2 text-sm text-slate-500">
      <Loader2 className="animate-spin" size={16} /> {text}
    </div>
  )
}

export function ErrorBox({ error }) {
  if (!error) return null
  return (
    <div className="flex items-start gap-2 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">
      <AlertTriangle size={16} className="mt-0.5 shrink-0" /> <span>{error}</span>
    </div>
  )
}

export function PageTitle({ title, subtitle }) {
  return (
    <div className="mb-5">
      <h1 className="text-2xl font-semibold text-slate-900">{title}</h1>
      {subtitle && <p className="mt-1 text-sm text-slate-500">{subtitle}</p>}
    </div>
  )
}

export function Stat({ label, value, hint }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-slate-50 p-3">
      <div className="text-xs uppercase tracking-wide text-slate-500">{label}</div>
      <div className="mt-1 text-lg font-semibold text-slate-900">{value ?? '-'}</div>
      {hint && <div className="text-xs text-slate-500">{hint}</div>}
    </div>
  )
}

export function ReportCard({ report }) {
  if (!report) return null
  const r = report.report || {}
  const ai = report.source === 'gemini'
  return (
    <div className="card">
      <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
        <h2 className="flex items-center gap-2 text-lg font-semibold text-slate-900">
          <FileText size={18} className="text-teal-600" /> {r.title || 'Structured report'}
        </h2>
        <span className={`inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-medium ${ai ? 'bg-teal-50 text-teal-700' : 'bg-amber-50 text-amber-700'}`}>
          <Sparkles size={12} /> {ai ? `Written by ${report.model}` : 'Plain summary (AI report service unavailable)'}
        </span>
      </div>
      {r.summary && <p className="text-sm text-slate-700">{r.summary}</p>}
      {r.findings?.length > 0 && (
        <Section title="Findings">
          <ul className="list-disc space-y-1 pl-5">{r.findings.map((f, i) => <li key={i}>{f}</li>)}</ul>
        </Section>
      )}
      {r.measurements?.length > 0 && (
        <Section title="Measurements">
          <div className="grid gap-2 sm:grid-cols-2">
            {r.measurements.map((m, i) => (
              <div key={i} className="flex justify-between gap-3 rounded border border-slate-100 bg-slate-50 px-3 py-1.5">
                <span className="text-slate-500">{m.name}</span><span className="text-right font-medium">{m.value}</span>
              </div>
            ))}
          </div>
        </Section>
      )}
      {r.interpretation && <Section title="Interpretation"><p>{r.interpretation}</p></Section>}
      {r.limitations?.length > 0 && (
        <Section title="Limitations">
          <ul className="list-disc space-y-1 pl-5">{r.limitations.map((f, i) => <li key={i}>{f}</li>)}</ul>
        </Section>
      )}
      {r.recommendation && <Section title="Recommendation"><p>{r.recommendation}</p></Section>}
    </div>
  )
}

function Section({ title, children }) {
  return (
    <div className="mt-4 text-sm text-slate-700">
      <div className="label">{title}</div>
      {children}
    </div>
  )
}

const COLORS = ['bg-teal-600', 'bg-indigo-500', 'bg-amber-500', 'bg-slate-400', 'bg-rose-500']

// groups: [{ label, bars: [{ name, value }] }] ; values in 0..max
export function BarChart({ groups, max = 1, format = (v) => v.toFixed(3), legend }) {
  return (
    <div>
      <div className="flex h-64 items-end gap-6 border-b border-l border-slate-300 px-4 pt-6">
        {groups.map((g) => (
          <div key={g.label} className="flex h-full flex-1 flex-col justify-end">
            <div className="flex h-full items-end justify-center gap-1.5">
              {g.bars.map((b, i) => (
                <div key={b.name} className="flex h-full w-full max-w-14 flex-col items-center justify-end">
                  <span className="mb-1 text-[11px] font-medium text-slate-700">{b.value == null ? 'n/a' : format(b.value)}</span>
                  <div className={`w-full rounded-t ${COLORS[i % COLORS.length]}`} style={{ height: `${Math.max(0, (b.value || 0) / max) * 85}%` }} title={`${b.name}: ${b.value}`} />
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
      <div className="flex gap-6 px-4 pt-2">
        {groups.map((g) => <div key={g.label} className="flex-1 text-center text-sm font-medium text-slate-600">{g.label}</div>)}
      </div>
      {legend && (
        <div className="mt-4 flex flex-wrap gap-4 text-xs text-slate-600">
          {legend.map((l, i) => (
            <span key={l} className="flex items-center gap-1.5"><span className={`h-3 w-3 rounded-sm ${COLORS[i % COLORS.length]}`} /> {l}</span>
          ))}
        </div>
      )}
    </div>
  )
}
