import { useEffect } from 'react'
import * as DropdownMenu from '@radix-ui/react-dropdown-menu'
import { motion } from 'framer-motion'
import { Check, ChevronDown, UserRound } from 'lucide-react'
import { usePersonas } from '@/hooks/useQueries'
import { useSession } from '@/store/session'
import { Skeleton } from '@/components/ui/skeleton'
import { toast } from '@/components/ui/toast'
import { cn, seedToUnit } from '@/lib/utils'
import type { Persona } from '@/lib/types'

function personaTint(persona: Persona) {
  const hue = Math.round(seedToUnit(persona.avatar_seed ?? persona.id, 3) * 360)
  return `linear-gradient(135deg, hsl(${hue} 55% 58%), hsl(${(hue + 50) % 360} 48% 34%))`
}

export function PersonaAvatar({
  persona,
  className,
}: {
  persona: Persona
  className?: string
}) {
  const initials = persona.name
    .split(' ')
    .slice(0, 2)
    .map((p) => p[0])
    .join('')
    .toUpperCase()
  return (
    <span
      className={cn(
        'grid shrink-0 place-items-center rounded-full text-[10px] font-semibold text-ink-950/85',
        className,
      )}
      style={{ background: personaTint(persona) }}
    >
      {initials}
    </span>
  )
}

/**
 * Switching the active shopper re-keys every recommendation query, so the rails
 * on screen refetch and visibly re-rank against the new profile.
 */
export function PersonaSwitcher({ compact = false }: { compact?: boolean }) {
  const { data: personas, isLoading, isError } = usePersonas()
  const persona = useSession((s) => s.persona)
  const setPersona = useSession((s) => s.setPersona)

  // Adopt the first profile on cold start so the rails always have a subject.
  useEffect(() => {
    if (!persona && personas && personas.length > 0) setPersona(personas[0])
  }, [persona, personas, setPersona])

  // Keep the stored copy fresh if the service reshapes a profile.
  useEffect(() => {
    if (!persona || !personas) return
    const match = personas.find((p) => p.id === persona.id)
    if (match && match.name !== persona.name) setPersona(match)
  }, [persona, personas, setPersona])

  if (isLoading) {
    return <Skeleton className={cn('h-10 rounded-full', compact ? 'w-10' : 'w-[180px]')} />
  }

  if (isError || !personas || personas.length === 0) {
    return (
      <div
        className="flex h-10 items-center gap-2 rounded-full border border-white/[0.08] px-3 text-[12px] text-ink-500"
        title="Shopper profiles load from the Nuvara service"
      >
        <UserRound className="h-3.5 w-3.5" />
        {!compact && <span>Guest</span>}
      </div>
    )
  }

  const active = persona ?? personas[0]

  return (
    <DropdownMenu.Root>
      <DropdownMenu.Trigger asChild>
        <button
          className={cn(
            'group flex h-10 items-center gap-2.5 rounded-full border border-white/[0.09] bg-white/[0.03] pl-1.5 pr-3 text-left transition-colors duration-300 ease-expo hover:border-white/20 hover:bg-white/[0.06]',
            compact && 'pr-2',
          )}
          aria-label="Switch shopper profile"
        >
          <PersonaAvatar persona={active} className="h-7 w-7" />
          {!compact && (
            <span className="min-w-0">
              <span className="block truncate text-[12.5px] font-medium leading-tight text-ink-100">
                {active.name}
              </span>
              <span className="block truncate text-[10.5px] leading-tight text-ink-500">
                {active.segment}
              </span>
            </span>
          )}
          <ChevronDown className="h-3.5 w-3.5 text-ink-500 transition-transform duration-300 ease-expo group-data-[state=open]:rotate-180" />
        </button>
      </DropdownMenu.Trigger>

      <DropdownMenu.Portal>
        <DropdownMenu.Content
          align="end"
          sideOffset={10}
          className="z-[80] w-[320px] overflow-hidden rounded-2xl border border-white/[0.08] bg-ink-900/95 p-1.5 shadow-lift backdrop-blur-2xl"
          asChild
        >
          <motion.div
            initial={{ opacity: 0, y: -6, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            transition={{ duration: 0.28, ease: [0.16, 1, 0.3, 1] }}
          >
            <div className="px-3 pb-2 pt-2.5">
              <p className="eyebrow">Shopping as</p>
              <p className="mt-1 text-[12px] leading-relaxed text-ink-500">
                Recommendation rails re-rank instantly for the selected profile.
              </p>
            </div>
            {personas.map((p) => {
              const selected = p.id === active.id
              return (
                <DropdownMenu.Item
                  key={p.id}
                  onSelect={() => {
                    if (selected) return
                    setPersona(p)
                    toast({
                      title: `Now shopping as ${p.name}`,
                      description: 'Recommendations are re-ranking for this profile.',
                      tone: 'success',
                    })
                  }}
                  className={cn(
                    'flex cursor-pointer items-start gap-3 rounded-xl px-3 py-2.5 outline-none transition-colors duration-200',
                    'data-[highlighted]:bg-white/[0.06]',
                    selected && 'bg-white/[0.04]',
                  )}
                >
                  <PersonaAvatar persona={p} className="mt-0.5 h-8 w-8" />
                  <span className="min-w-0 flex-1">
                    <span className="flex items-center gap-2">
                      <span className="truncate text-[13px] font-medium text-ink-100">{p.name}</span>
                      {selected && <Check className="h-3.5 w-3.5 shrink-0 text-amber-300" />}
                    </span>
                    <span className="mt-0.5 block text-[11px] uppercase tracking-[0.14em] text-amber-300/70">
                      {p.segment}
                    </span>
                    {p.blurb && (
                      <span className="mt-1 block text-[12px] leading-relaxed text-ink-400">
                        {p.blurb}
                      </span>
                    )}
                  </span>
                </DropdownMenu.Item>
              )
            })}
          </motion.div>
        </DropdownMenu.Content>
      </DropdownMenu.Portal>
    </DropdownMenu.Root>
  )
}
