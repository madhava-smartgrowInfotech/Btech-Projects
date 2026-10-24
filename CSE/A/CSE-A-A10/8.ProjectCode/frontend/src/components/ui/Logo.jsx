export default function Logo({ compact = false }) {
  return (
    <span className="inline-flex items-center gap-2 font-mono text-sm font-semibold tracking-tight text-fg">
      <span className="relative grid h-6 w-6 place-items-center rounded-[5px] border border-ok/50 bg-ok/10" aria-hidden="true">
        <span className="flex flex-col gap-[2px]">
          <span className="h-[3px] w-[3px] rounded-full bg-alert/50" />
          <span className="h-[3px] w-[3px] rounded-full bg-warn/50" />
          <span className="dot-live h-[3px] w-[3px] rounded-full bg-ok" />
        </span>
      </span>
      {!compact && <span>flow<span className="text-ok">/</span>sense</span>}
    </span>
  )
}
