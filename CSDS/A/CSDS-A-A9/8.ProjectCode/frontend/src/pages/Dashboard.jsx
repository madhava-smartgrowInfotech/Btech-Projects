import { Activity, Eraser, Gauge, Network, ScrollText, ShieldCheck, Target, Users } from 'lucide-react'
import { Badge, Button, Card, EmptyState, PageHeader, Stepper, StatCard } from '../components/ui'
import { BarCompare } from '../components/charts'
import { FadeIn, Stagger } from '../components/motion'
import { fmtNum, fmtPct } from '../lib/format'
import Gate from './Gate'
import { CertificateView, statusBadge } from './shared'

function Dash({ s }) {
  const m = s.metrics
  const unlearned = s.contributions.filter((c) => !c.active && s.trained).length
  const hasCert = !!s.latest_certificate
  const step = !s.trained ? 0 : hasCert ? 3 : 1
  const bars = s.trained ? s.contributions.map((c) => ({ name: c.domain, value: c.clipped_norm, highlight: c.active, color: c.active ? undefined : 'var(--rose)' })) : []
  return (
    <div className="stack">
      <PageHeader
        eyebrow="Overview"
        icon={ShieldCheck}
        title="Right-to-be-forgotten, certified"
        lead="Train a federated model, remove a client's contribution without retraining, and keep a tamper-evident record."
        actions={
          <Button to={s.trained ? '/app/unlearning' : '/app/training'} icon={s.trained ? Eraser : Network}>
            {s.trained ? 'Request unlearning' : 'Train the model'}
          </Button>
        }
      />

      <Card hover={false} title="Workflow" subtitle="Where this session stands">
        <Stepper
          current={step}
          steps={[
            { label: 'Train', hint: s.trained ? 'Done' : 'Federated training' },
            { label: 'Unlearn', hint: hasCert ? `${unlearned} client(s) removed` : 'Remove a client' },
            { label: 'Verify', hint: s.audit.valid ? 'Audit chain valid' : 'Audit chain broken' },
          ]}
        />
      </Card>

      <Stagger className="grid-kpi">
        <Stagger.Item><StatCard label="Active clients" tone="lavender" icon={Users} display={m ? String(m.active_clients) : '–'} foot={m ? `of ${s.contributions.length} total` : 'Not trained yet'} /></Stagger.Item>
        <Stagger.Item><StatCard label="DP epsilon" tone="mint" icon={ShieldCheck} display={m ? fmtNum(m.epsilon, 4) : '–'} foot={m ? `δ = ${m.delta}` : 'Not trained yet'} /></Stagger.Item>
        <Stagger.Item><StatCard label="Perplexity" tone="peach" icon={Gauge} display={m ? fmtNum(m.perplexity, 2) : '–'} foot="Public evaluation set" /></Stagger.Item>
        <Stagger.Item><StatCard label="Next-char accuracy" tone="sky" icon={Target} display={m ? fmtPct(m.next_character_accuracy) : '–'} foot="Public evaluation set" /></Stagger.Item>
      </Stagger>

      <div className="grid-2">
        <Card title="Client updates" subtitle="Clipped L2 norm of each tracked update">
          {s.trained ? (
            <BarCompare data={bars} horizontal height={260} yWidth={100} name="Clipped L2" valueFormat={(v) => fmtNum(v, 2)} label="Clipped update norm per client" />
          ) : (
            <EmptyState icon={Network} title="No model yet" message="Train the federated model to see each client's clipped update." action={<Button to="/app/training">Go to training</Button>} compact />
          )}
        </Card>
        <Card
          title="Latest certificate"
          subtitle={hasCert ? undefined : 'Issued after an unlearning request'}
          actions={hasCert ? statusBadge(s.latest_certificate.status) : null}
        >
          {hasCert ? (
            <CertificateView cert={s.latest_certificate} />
          ) : (
            <EmptyState
              icon={Eraser}
              title="No certificate yet"
              message={s.trained ? 'Remove a client to produce a verified certificate.' : 'Train the model first, then request unlearning.'}
              action={<Button to={s.trained ? '/app/unlearning' : '/app/training'}>{s.trained ? 'Request unlearning' : 'Train the model'}</Button>}
              compact
            />
          )}
        </Card>
      </div>

      <FadeIn>
        <Card hover={false} title="Compliance ledger" subtitle="Training and deletion events linked by SHA-256" actions={<Badge tone={s.audit.valid ? 'mint' : 'rose'} dot>{s.audit.valid ? 'Valid' : 'Invalid'}</Badge>}>
          <div className="row between" style={{ flexWrap: 'wrap' }}>
            <span className="muted">
              <Activity size={16} aria-hidden="true" style={{ verticalAlign: -3, marginRight: 6 }} />
              {s.audit.detail}
            </span>
            <Button variant="secondary" to="/app/audit" icon={ScrollText}>
              Open audit ledger
            </Button>
          </div>
        </Card>
      </FadeIn>
    </div>
  )
}

export default function Dashboard() {
  return <Gate>{(s) => <Dash s={s} />}</Gate>
}
