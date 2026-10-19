import { Link } from 'react-router-dom'
import { AlertTriangle, CalendarClock, Gauge, Flame, ShieldAlert, Star, Wallet } from 'lucide-react'
import { Badge, Button, Card, CardHeader, EmptyState, ErrorState, KeyValueList, PageHeader, ProgressBar, Skeleton, StatCard, Timeline } from '../components/ui'
import { SlideUp, Stagger } from '../components/motion'
import { Api } from '../lib/api'
import { useAuth } from '../lib/auth'
import { useAsync } from '../lib/useAsync'
import { TRUST_EVENT, ago, money, when } from '../lib/format'

function Stars({ score }) {
  const full = Math.round(score)
  return (
    <div className="stars" role="img" aria-label={`${score} out of 5`}>
      {[1, 2, 3, 4, 5].map((i) => (
        <Star key={i} size={26} aria-hidden="true" className={i <= full ? 'on' : ''} />
      ))}
    </div>
  )
}

export default function Trust() {
  const { user } = useAuth()
  const { data: t, error, loading, reload } = useAsync(() => Api.trust(), [])
  const suspended = user?.suspended_until && new Date(user.suspended_until) > new Date()
  const streakTotal = t ? t.benefit_streak + t.next_reward_in : 0

  return (
    <div className="container">
      <PageHeader title="Trust score" description="Check out on time and your score climbs, which lowers your fee multiplier. Late checkouts do the opposite." />

      {error ? (
        <ErrorState title="Could not load your trust score" error={error} onRetry={() => reload()} />
      ) : (
        <>
          {suspended && (
            <div className="state-inline bad" role="alert" style={{ marginBottom: 18 }}>
              <ShieldAlert size={18} aria-hidden="true" />
              <div>
                <strong>Booking is paused until {when(user.suspended_until)}</strong>
                <div>Your score is below the minimum and a recent late checkout was recorded. On-time history restores access.</div>
              </div>
            </div>
          )}

          <Stagger className="grid grid-4">
            <StatCard label="Trust score" value={t ? `${t.trust_score} / 5` : undefined} icon={Gauge} loading={loading} />
            <StatCard label="Fee multiplier" value={t ? `x${t.fee_multiplier}` : undefined} icon={Star} loading={loading} tone={t && t.fee_multiplier > 1 ? 'warn' : undefined} delta={t ? (t.fee_multiplier < 1 ? 'Discount applied' : t.fee_multiplier > 1 ? 'Surcharge applied' : 'Standard rate') : undefined} deltaTone={t && t.fee_multiplier < 1 ? 'up' : t && t.fee_multiplier > 1 ? 'down' : undefined} />
            <StatCard label="On-time streak" value={t ? t.benefit_streak : undefined} icon={Flame} loading={loading} delta={t ? `${t.next_reward_in} more for +1 trust` : undefined} />
            <StatCard label="Recent warnings" value={t ? t.warning_count : undefined} icon={AlertTriangle} tone={t && t.warning_count > 0 ? 'danger' : undefined} loading={loading} />
          </Stagger>

          <div className="split mt">
            <SlideUp inView>
              <Card>
                <CardHeader title="History" subtitle="Your 20 most recent trust events" />
                <div className="card-body">
                  {loading ? (
                    <div aria-busy="true" aria-label="Loading history">
                      {[0, 1, 2].map((i) => (
                        <Skeleton key={i} height={20} style={{ margin: '14px 0' }} />
                      ))}
                    </div>
                  ) : t.events.length === 0 ? (
                    <EmptyState icon={CalendarClock} title="No trust events yet" actions={<Button as={Link} to="/app/find" variant="primary">Find parking</Button>}>
                      Your first on-time or late checkout shows up here.
                    </EmptyState>
                  ) : (
                    <Timeline
                      items={t.events.map((e, i) => {
                        const k = TRUST_EVENT[e.kind] || { label: e.kind, tone: 'neutral' }
                        return { key: i, title: k.label, tone: k.tone === 'neutral' ? undefined : k.tone === 'safe' ? 'safe' : 'danger', meta: ago(e.at), body: e.detail }
                      })}
                    />
                  )}
                </div>
              </Card>
            </SlideUp>

            <SlideUp inView delay={0.1}>
              <Card>
                <CardHeader title="Your standing" />
                <div className="card-body stack" style={{ gap: 18 }}>
                  {loading ? (
                    <Skeleton height={90} />
                  ) : (
                    <>
                      <Stars score={t.trust_score} />
                      <ProgressBar value={t.benefit_streak} max={Math.max(1, streakTotal)} label="Progress to next trust point" valueLabel={`${t.benefit_streak} of ${streakTotal} on-time checkouts`} />
                      <KeyValueList
                        items={[
                          ['Trust score', `${t.trust_score} / 5`],
                          ['Fee multiplier', `x${t.fee_multiplier}`],
                          ['Account credit', <span key="c"><Wallet size={13} aria-hidden="true" style={{ display: 'inline', verticalAlign: '-2px' }} /> {money(user?.account_credit ?? 0)}</span>],
                          ['Status', suspended ? <Badge key="s" tone="danger">Paused</Badge> : <Badge key="s" tone="safe">Can book</Badge>],
                        ]}
                      />
                      <p className="faint">Check out within 10 minutes of your window ending to count as on time.</p>
                    </>
                  )}
                </div>
              </Card>
            </SlideUp>
          </div>
        </>
      )}
    </div>
  )
}
