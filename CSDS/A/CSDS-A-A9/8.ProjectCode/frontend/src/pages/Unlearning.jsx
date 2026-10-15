import { useEffect, useState } from 'react'
import { Eraser, Network, ShieldCheck } from 'lucide-react'
import { Button, Card, EmptyState, Modal, PageHeader, Select } from '../components/ui'
import { ChartLegend, GroupedBars } from '../components/charts'
import { FadeIn } from '../components/motion'
import { api } from '../lib/api'
import { fmtNum } from '../lib/format'
import Gate from './Gate'
import { CertificateView, statusBadge } from './shared'
import { useAction } from './useAction'

function UnlearnView({ s }) {
  const { busy, run } = useAction()
  const [target, setTarget] = useState('')
  const [confirm, setConfirm] = useState(false)
  const [formError, setFormError] = useState(null)
  const active = s.active_clients
  const canRun = s.trained && active.length > 1

  useEffect(() => {
    if (!active.some((c) => c.client_id === target)) setTarget(active[0]?.client_id || '')
  }, [active, target])

  const chosen = active.find((c) => c.client_id === target)
  const ask = () => {
    if (!target) {
      setFormError('Choose a client to remove.')
      return
    }
    setFormError(null)
    setConfirm(true)
  }
  const execute = async () => {
    setConfirm(false)
    await run('unlearn', () => api.unlearn(target), {
      title: 'Client removed and certified',
      message: (c) => `${c.client_name} · ${c.status === 'CERTIFIED' ? 'certified' : 'review required'}`,
      failTitle: 'Unlearning failed',
    })
  }

  const cert = s.latest_certificate
  const quality = cert
    ? [
        { x: 'Membership AUC', Before: cert.membership_auc_before, After: cert.membership_auc_after },
        { x: 'Next-char accuracy', Before: cert.accuracy_before, After: cert.accuracy_after },
      ]
    : []
  const ppl = cert ? [{ x: 'Perplexity', Before: cert.perplexity_before, After: cert.perplexity_after }] : []
  const seriesHex = [
    { key: 'Before', name: 'Before', color: '#C7B9FF' },
    { key: 'After', name: 'After', color: '#A7E8C8' },
  ]

  return (
    <div className="stack">
      <PageHeader
        eyebrow="Step 2"
        icon={Eraser}
        title="Certified unlearning"
        lead="Remove an active client's tracked update, renormalise over the remaining clients, and verify against a clean recomputation."
      />

      <Card hover={false} title="Right-to-be-forgotten request" subtitle="Pick the client whose contribution must be erased">
        {!s.trained ? (
          <EmptyState icon={Network} title="Train the model first" message="Unlearning removes a client from a trained global model." action={<Button to="/app/training">Go to training</Button>} compact />
        ) : active.length <= 1 ? (
          <EmptyState icon={ShieldCheck} title="Only one client remains" message="At least one client must stay in the model. Start a new session on the training page to run another request." action={<Button to="/app/training">Go to training</Button>} compact />
        ) : (
          <div className="row" style={{ alignItems: 'flex-end', flexWrap: 'wrap', '--gap': '14px' }}>
            <div style={{ flex: '1 1 260px', minWidth: 0 }}>
              <Select
                label="Client to remove"
                value={target}
                onChange={(e) => setTarget(e.target.value)}
                options={active.map((c) => ({ value: c.client_id, label: `${c.display_name} — ${c.domain}` }))}
                error={formError}
                hint={`${active.length} active clients`}
              />
            </div>
            <Button icon={Eraser} loading={busy === 'unlearn'} disabled={!canRun || busy != null} onClick={ask}>
              Execute &amp; certify
            </Button>
          </div>
        )}
      </Card>

      {cert ? (
        <FadeIn>
          <div className="grid-2">
            <Card hover={false} title="Verification certificate" actions={statusBadge(cert.status)}>
              <CertificateView cert={cert} />
            </Card>
            <div className="stack">
              <Card hover={false} title="Before vs after" subtitle="Leakage and quality of the retained model">
                <ChartLegend items={[{ label: 'Before', color: '#C7B9FF' }, { label: 'After', color: '#A7E8C8' }]} />
                <GroupedBars data={quality} series={seriesHex} height={230} valueFormat={(v) => fmtNum(v, 3)} label="Membership AUC and accuracy before and after unlearning" />
              </Card>
              <Card hover={false} title="Perplexity" subtitle="Lower is better">
                <ChartLegend items={[{ label: 'Before', color: '#C7B9FF' }, { label: 'After', color: '#A7E8C8' }]} />
                <GroupedBars data={ppl} series={seriesHex} height={200} valueFormat={(v) => fmtNum(v, 2)} label="Perplexity before and after unlearning" />
              </Card>
            </div>
          </div>
        </FadeIn>
      ) : (
        <EmptyState
          icon={ShieldCheck}
          title="No certificate yet"
          message="A verification certificate with the residual-influence check, membership-inference AUC and retained utility appears here after an unlearning request."
        />
      )}

      <Modal
        open={confirm}
        onClose={() => setConfirm(false)}
        title="Remove this client?"
        description={chosen ? `${chosen.display_name} (${chosen.domain}) will be erased from the global model. This cannot be undone in this session.` : ''}
        footer={
          <>
            <Button variant="ghost" onClick={() => setConfirm(false)}>
              Cancel
            </Button>
            <Button variant="danger" icon={Eraser} onClick={execute}>
              Remove &amp; certify
            </Button>
          </>
        }
      />
    </div>
  )
}

export default function Unlearning() {
  return <Gate>{(s) => <UnlearnView s={s} />}</Gate>
}
