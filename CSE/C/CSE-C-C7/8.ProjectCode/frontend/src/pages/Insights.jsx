import { ArrowRight, CheckCircle2, Gauge, Lightbulb, Target, TriangleAlert, Zap } from 'lucide-react'
import { Alert, Button, Card, EmptyState, KeyValueList, PageHeader, ProgressBar, SkeletonBlock, StatCard } from '../components/ui'
import { BarBlocks, PALETTE } from '../components/ui/Charts'
import { Async } from '../components/app/Async'
import { Stagger } from '../components/motion'
import { get } from '../lib/api'
import { useApi } from '../lib/useApi'
import { ACTION_LABEL, EVENT_LABEL, fmtPct } from '../lib/format'

const FEATURE_LABEL = {
  cum_clicks: 'Total clicks',
  recent_clicks: 'Recent clicks',
  quiz_count: 'Quizzes',
  forum_count: 'Discussions',
  completions: 'Completions',
  engagement: 'Engagement',
  weekly_hours: 'Weekly hours',
  skill_code: 'Skill level',
}

export default function Insights() {
  const q = useApi(() => get('/api/insights'), [])
  return (
    <div className="page-stack">
      <PageHeader
        eyebrow="Insights"
        title="Learning insights"
        description="How your activity reads to the model: strengths, where to focus, and which kind of action is estimated to help most."
      />
      <Async q={q} title="Could not load your insights" skeleton={<SkeletonBlock rows={6} label="Loading insights" />}>
        {(i) => {
          const uplift = Object.entries(i.uplift || {}).map(([k, v]) => ({ key: k, name: ACTION_LABEL[k] || k, short: k.replace('_', ' '), value: v }))
          const features = Object.entries(i.contributing_features || {})
            .filter(([, v]) => typeof v === 'number')
            .map(([k, v]) => ({ key: k, name: FEATURE_LABEL[k] || k, value: v }))
          const types = Object.entries(i.by_type || {}).map(([k, v]) => ({ key: k, name: EVENT_LABEL[k] || k, value: v }))
          const topUplift = Math.max(...uplift.map((u) => u.value), 0)
          return (
            <>
              <Stagger className="grid grid-3" inView={false}>
                <StatCard label="Engagement" value={i.engagement.label} icon={Gauge} hint={`Score ${fmtPct(i.engagement.score)}`} />
                <StatCard label="Est. success" value={fmtPct(i.success_probability)} icon={Target} hint={`Risk ${fmtPct(i.risk)}`} />
                <StatCard label="Best next action" value={i.recommended_action} icon={Zap} tone="lime" />
              </Stagger>
              <div className="two-col">
                <div className="stack" style={{ '--gap': '24px' }}>
                  <Card title="Strengths">
                    <ul className="check-list">
                      {i.strengths.map((s) => (
                        <li key={s}>
                          <CheckCircle2 size={20} aria-hidden="true" /> {s}
                        </li>
                      ))}
                    </ul>
                  </Card>
                  <Card title="Needs attention">
                    {i.attention.length ? (
                      <ul className="check-list">
                        {i.attention.map((s) => (
                          <li key={s}>
                            <TriangleAlert size={20} aria-hidden="true" /> {s}
                          </li>
                        ))}
                      </ul>
                    ) : (
                      <p className="muted">Nothing flagged. Keep going.</p>
                    )}
                  </Card>
                  <Card title="Your interactions by type">
                    {types.length ? (
                      <BarBlocks data={types} xKey="name" yKey="value" name="Events" color={PALETTE.sky} height={260} />
                    ) : (
                      <EmptyState
                        icon={Lightbulb}
                        title="No interactions yet"
                        action={
                          <Button variant="primary" to="/app/recommendations" iconRight={ArrowRight}>
                            Open a recommendation
                          </Button>
                        }
                      >
                        Open, start or save a course and the breakdown appears here.
                      </EmptyState>
                    )}
                  </Card>
                </div>
                <div className="stack" style={{ '--gap': '24px' }}>
                  <Card title="Estimated benefit by action">
                    <p className="small muted" style={{ marginBottom: 14 }}>
                      Based on observed learning patterns, not proven causal effects.
                    </p>
                    <div className="stack" style={{ '--gap': '14px' }}>
                      {uplift.map((u) => (
                        <div key={u.key}>
                          <div className="row-between">
                            <strong>{u.name}</strong>
                            <span className="mono small">{u.value}</span>
                          </div>
                          <ProgressBar value={Math.max(u.value, 0)} max={topUplift || 1} label={`${u.name} estimated benefit`} tone={u.value === topUplift ? undefined : 'coral'} />
                        </div>
                      ))}
                    </div>
                  </Card>
                  <Card title="What shaped your success estimate">
                    {features.length ? (
                      <BarBlocks data={features} xKey="name" yKey="value" name="Importance" color={PALETTE.amber} height={280} decimals={2} />
                    ) : (
                      <Alert tone="info">The selected model does not report per-feature importance, so there is nothing to chart here.</Alert>
                    )}
                  </Card>
                  <Card title="Learner state fed to the model">
                    <KeyValueList items={Object.entries(i.state || {}).map(([k, v]) => ({ label: FEATURE_LABEL[k] || k, value: Number(v).toFixed(2) }))} />
                  </Card>
                </div>
              </div>
            </>
          )
        }}
      </Async>
    </div>
  )
}
