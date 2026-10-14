export default function Logo({ compact = false }) {
  return (
    <span className="inline-flex items-center gap-2 font-mono text-sm font-semibold tracking-tight text-fg">
      <span className="relative grid h-6 w-6 place-items-center rounded-[5px] border border-ok/50 bg-ok/10">
        <span className="dot-live h-2 w-2 bg-ok" />
      </span>
      {!compact && <span>tax<span className="text-ok">/</span>sentinel</span>}
    </span>
  )
}
