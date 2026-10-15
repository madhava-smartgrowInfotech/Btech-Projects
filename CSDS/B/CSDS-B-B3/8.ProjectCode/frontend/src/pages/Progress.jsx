import { AsyncView, PageSkeleton } from '../components/common'
import { EmptyState, PageHeader, StatCard } from '../components/ui'
import { AreaTrend, ChartCard, DonutChart, GroupedBarChart, HBarChart, useChartColors } from '../components/charts'
import { Stagger } from '../components/motion'
import { inr } from '../lib/format'
import { api } from '../lib/api'
import { useAsync } from '../lib/useAsync'

const pct = (v) => `${Math.round(v)}%`
const barHeight = (n) => Math.max(240, n * 34 + 40)

export default function Progress() {
  const state = useAsync(() => api.get('/progress/analytics'), [])
  const colors = useChartColors()
  return (
    <>
      <PageHeader title="Progress & analytics" description="Your skills, topic completion, interview trend, coding results and marketplace earnings." />
      <AsyncView state={state} skeleton={<PageSkeleton stats={5} cards={4} />}>
        {(d) => {
          const c = d.counts
          const skills = [...d.skills].sort((a, b) => a.Proficiency - b.Proficiency)
          const comp = [...d.completion].sort((a, b) => a.Completion - b.Completion)
          const interviews = d.interviews.map((r) => ({ ...r, label: r.Date.slice(5, 16) }))
          const passRate = d.coding.total ? Math.round((d.coding.passed / d.coding.total) * 100) : 0
          return (
            <div className="stack">
              <Stagger className="grid" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))' }}>
                <StatCard label="Completed" value={c.completed} tone="info" />
                <StatCard label="Strong" value={c.strong} />
                <StatCard label="Weak" value={c.weak} tone="warn" />
                <StatCard label="Recommended" value={c.recommended} />
                <StatCard label="Locked" value={c.locked} />
              </Stagger>

              <div className="grid grid-2">
                <ChartCard title="Skill proficiency" subtitle="Per skill, 0 to 100" height={barHeight(skills.length)}>
                  {skills.length ? (
                    <HBarChart data={skills} labelKey="Skill" valueKey="Proficiency" name="Proficiency" valueFormat={pct} domain={[0, 100]} />
                  ) : (
                    <EmptyState title="No skill data yet">Take a skill assessment or set your skills in your profile.</EmptyState>
                  )}
                </ChartCard>
                <ChartCard title="Learning completion" subtitle="Topics you have started" height={barHeight(comp.length)}>
                  {comp.length ? (
                    <HBarChart data={comp} labelKey="Topic" valueKey="Completion" name="Completion" valueFormat={pct} domain={[0, 100]} />
                  ) : (
                    <EmptyState title="No progress data yet">Mark progress on a topic in the Learning center.</EmptyState>
                  )}
                </ChartCard>
              </div>

              <div className="grid grid-2">
                <ChartCard title="Interview score trend" subtitle="Overall score per mock interview">
                  {interviews.length ? (
                    <AreaTrend data={interviews} xKey="label" yKey="Overall" name="Overall" yDomain={[0, 100]} />
                  ) : (
                    <EmptyState title="No mock interviews yet">Complete a mock interview to see your trend.</EmptyState>
                  )}
                </ChartCard>
                <ChartCard title="Coding submissions" subtitle={d.coding.total ? `Pass rate ${passRate}%` : 'Passed vs not passed'}>
                  {d.coding.total ? (
                    <DonutChart
                      centerValue={`${passRate}%`}
                      centerLabel="pass rate"
                      data={[
                        { name: 'Passed', value: d.coding.passed, color: colors.accent },
                        { name: 'Not passed', value: d.coding.failed, color: colors.danger },
                      ]}
                    />
                  ) : (
                    <EmptyState title="No coding submissions yet">Solve a problem in Coding practice.</EmptyState>
                  )}
                </ChartCard>
              </div>

              <ChartCard title="Marketplace earnings" subtitle="Seller earnings per sale, after the 10% platform fee">
                {d.earnings.length ? (
                  <GroupedBarChart
                    data={d.earnings}
                    xKey="Date"
                    yDomain={[0, 'auto']}
                    valueFormat={inr}
                    series={[{ key: 'Earnings', label: 'Earnings' }]}
                  />
                ) : (
                  <EmptyState title="No sales yet">Upload a resource in the Marketplace to start earning.</EmptyState>
                )}
              </ChartCard>
            </div>
          )
        }}
      </AsyncView>
    </>
  )
}
