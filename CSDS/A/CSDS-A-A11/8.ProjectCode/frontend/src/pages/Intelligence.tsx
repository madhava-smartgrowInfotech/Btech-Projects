import { useSearchParams } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Activity, FlaskConical, GitBranch, Terminal } from 'lucide-react'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Badge } from '@/components/ui/badge'
import { DigitalTwinLab } from '@/components/intelligence/DigitalTwinLab'
import { FeedbackPanel } from '@/components/intelligence/FeedbackPanel'
import { TrafficCenter } from '@/components/intelligence/TrafficCenter'
import { useSession } from '@/store/session'
import { API_BASE_URL } from '@/lib/api'
import { EASE_EXPO } from '@/lib/utils'

const TABS = [
  {
    value: 'twin',
    label: 'Digital Twin Lab',
    icon: FlaskConical,
    blurb:
      'Simulate a candidate weighting against the live strategy before it ever touches real traffic.',
  },
  {
    value: 'learning',
    label: 'Learning Loop',
    icon: GitBranch,
    blurb: 'Watch the orchestrator weights drift as real reinforcement lands.',
  },
  {
    value: 'traffic',
    label: 'Traffic Control',
    icon: Activity,
    blurb: 'Live service telemetry and synthetic load profiles.',
  },
]

export default function Intelligence() {
  const [params, setParams] = useSearchParams()
  const sessionId = useSession((s) => s.sessionId)
  const persona = useSession((s) => s.persona)

  const tab = params.get('tab') ?? 'twin'
  const active = TABS.find((t) => t.value === tab) ?? TABS[0]

  const setTab = (value: string) => {
    const next = new URLSearchParams(params)
    next.set('tab', value)
    setParams(next, { replace: true })
  }

  return (
    <Tabs value={active.value} onValueChange={setTab}>
      <div className="min-h-screen pb-24">
        {/* console chrome — deliberately distinct from the storefront */}
        <header className="border-b border-white/[0.07] bg-ink-900/40 backdrop-blur-sm">
          <div className="container py-10 sm:py-12">
            <div className="flex flex-wrap items-center gap-2">
              <span className="inline-flex items-center gap-2 rounded-md border border-amber-400/25 bg-amber-400/[0.07] px-2.5 py-1 font-mono text-[10.5px] uppercase tracking-[0.18em] text-amber-200">
                <Terminal className="h-3 w-3" />
                Internal
              </span>
              <Badge variant="outline" className="font-mono text-[10.5px]">
                {API_BASE_URL}
              </Badge>
              {persona && (
                <Badge variant="outline" className="font-mono text-[10.5px]">
                  subject: {persona.id}
                </Badge>
              )}
              <Badge variant="outline" className="font-mono text-[10.5px]">
                session: {sessionId.slice(0, 8)}
              </Badge>
            </div>

            <h1 className="mt-6 text-[34px] font-medium leading-[1.05] tracking-tighter text-ink-100 sm:text-[46px]">
              Nuvara Intelligence
            </h1>
            <p className="mt-3 max-w-2xl text-[15px] leading-relaxed text-ink-400">
              The control surface behind the storefront: the ensemble that ranks every rail, the
              simulation lab that vets changes to it, and the service keeping it inside its
              latency budget.
            </p>

            <div className="mt-8 flex flex-wrap items-center gap-x-6 gap-y-3">
              <TabsList className="flex-wrap">
                {TABS.map((item) => (
                  <TabsTrigger key={item.value} value={item.value}>
                    <item.icon className="h-3.5 w-3.5" />
                    {item.label}
                  </TabsTrigger>
                ))}
              </TabsList>

              <motion.p
                key={active.value}
                initial={{ opacity: 0, x: -6 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.45, ease: EASE_EXPO }}
                className="max-w-md text-[12.5px] leading-relaxed text-ink-500"
              >
                {active.blurb}
              </motion.p>
            </div>
          </div>
        </header>

        <div className="container pt-8 sm:pt-10">
          <TabsContent value="twin">
            <DigitalTwinLab />
          </TabsContent>
          <TabsContent value="learning">
            <FeedbackPanel />
          </TabsContent>
          <TabsContent value="traffic">
            <TrafficCenter />
          </TabsContent>
        </div>
      </div>
    </Tabs>
  )
}
