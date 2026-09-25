import { cn } from '@/lib/utils'

export function Logo({ className, mark = false }: { className?: string; mark?: boolean }) {
  return (
    <span className={cn('flex items-center gap-2.5', className)}>
      <svg viewBox="0 0 28 28" className="h-[22px] w-[22px]" aria-hidden>
        <path
          d="M6 21V7l16 14V7"
          fill="none"
          stroke="currentColor"
          strokeWidth="2.6"
          strokeLinecap="round"
          strokeLinejoin="round"
          className="text-amber-400"
        />
      </svg>
      {!mark && (
        <span className="text-[17px] font-semibold tracking-tightest text-ink-100">Nuvara</span>
      )}
    </span>
  )
}
