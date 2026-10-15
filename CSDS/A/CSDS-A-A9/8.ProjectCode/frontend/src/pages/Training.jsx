import { useState } from 'react'
import { Gauge, Network, Play, RotateCcw, ShieldCheck, Target, Users } from 'lucide-react'
import { Button, Card, EmptyState, Modal, PageHeader, StatCard } from '../components/ui'
import { BarCompare } from '../components/charts'
import { Stagger } from '../components/motion'
import { api } from '../lib/api'
import { fmtNum, fmtPct } from '../lib/format'
import { short } from '../lib/fmt'
import Gate from './Gate'
import { ClientsTable } from './shared'
import { useAction } from './useAction'

function TrainingView({ s }) {
  const { busy, run } = useAction()
  const [confirm, setConfirm] = useState(null)
  const m = s.metrics
  const train = async () => {
    setConfirm(null)
    await run('train', api.train, {
      title: 'Federated training complete',
      message: (r) => `${r.active_clients} clients aggregated · ε ${fmtNum(r.epsilon, 4)}`,
      failTitle: 'Training failed',
    })
  }
  const reset = async () => {
    setConfirm(null)
    await run('session', api.newSession, { title: 'New session started', message: 'Audit history was preserved.', failTitle: 'Could not start a new session' })
  }
  const bars = s.contributions.map((c) => ({ name: c.domain, value: s.trained ? c.clipped_norm : 0, highlight: c.active }))
  return (
    <div className="stack">
      <PageHeader
        eyebrow="Step 1"
        icon={Network}
        title="Federated training"
        lead="Each client's update is L2-clipped, then aggregated with Gaussian noise. Raw records never leave a client."
        actions={
          <>
            <Button variant="secondary" icon={RotateCcw} disabled={busy != null} onClick={() => setConfirm('session')}>
              New session
            </Button>
            <Button icon={Play} loading={busy === 'train'} disabled={busy != null} onClick={() => (s.trained ? setConfirm('train') : train())}>
              {s.trained ? 'Retrain model' : 'Train federated model'}
            </Button>
          </>
        }
      />

      <Stagger className="grid-kpi">
        <Stagger.Item><StatCard label="Active clients" tone="lavender" icon={Users} display={m ? String(m.active_clients) : '–'} foot={m ? `of ${s.contributions.length}` : 'Not trained yet'} /></Stagger.Item>
        <Stagger.Item><StatCard label="DP epsilon" tone="mint" icon={ShieldCheck} display={m ? fmtNum(m.epsilon, 4) : '–'} foot={m ? `δ = ${m.delta}` : 'Not trained yet'} /></Stagger.Item>
        <Stagger.Item><StatCard label="Perplexity" tone="peach" icon={Gauge} display={m ? fmtNum(m.perplexity, 2) : '–'} foot="Lower is better" /></Stagger.Item>
        <Stagger.Item><StatCard label="Next-char accuracy" tone="sky" icon={Target} display={m ? fmtPct(m.next_character_accuracy) : '–'} foot={m ? `Utility ${fmtNum(m.utility_score, 3)}` : 'Not trained yet'} /></Stagger.Item>
      </Stagger>

      {!s.trained && (
        <EmptyState
          icon={Network}
          title="The global model has not been trained"
          message="Run federated training to aggregate the five clients' clipped updates into one noisy global model."
          action={
            <Button icon={Play} loading={busy === 'train'} onClick={train}>
              Train federated model
            </Button>
          }
        />
      )}

      <div className="grid-2">
        <Card title="Clients" subtitle="Tracked update per federated client">
          <ClientsTable contributions={s.contributions} trained={s.trained} />
        </Card>
        <Card title="Clipped update norm" subtitle="Bounded by the clip norm before aggregation">
          <BarCompare data={bars} height={280} name="Clipped L2" valueFormat={(v) => fmtNum(v, 1)} label="Clipped update norm per client" />
        </Card>
      </div>

      {m && (
        <Card hover={false} title="Global model fingerprint" subtitle="SHA-256 of the current parameter vector">
          <p className="mono small" style={{ wordBreak: 'break-all' }} title={m.model_hash}>
            {m.model_hash}
          </p>
          <p className="muted small" style={{ marginTop: 8 }}>
            Session {short(s.session_id, 8)}
          </p>
        </Card>
      )}

      <Modal
        open={confirm === 'train'}
        onClose={() => setConfirm(null)}
        title="Retrain the model?"
        description="Retraining rebuilds the global model from all five clients and clears the certificates issued in this session. The audit ledger keeps its history."
        footer={
          <>
            <Button variant="ghost" onClick={() => setConfirm(null)}>
              Cancel
            </Button>
            <Button onClick={train}>Retrain</Button>
          </>
        }
      />
      <Modal
        open={confirm === 'session'}
        onClose={() => setConfirm(null)}
        title="Start a new session?"
        description="This discards the current model and certificates and creates a fresh, untrained session. The audit ledger keeps its history."
        footer={
          <>
            <Button variant="ghost" onClick={() => setConfirm(null)}>
              Cancel
            </Button>
            <Button variant="danger" onClick={reset}>
              Start new session
            </Button>
          </>
        }
      />
    </div>
  )
}

export default function Training() {
  return <Gate>{(s) => <TrainingView s={s} />}</Gate>
}
