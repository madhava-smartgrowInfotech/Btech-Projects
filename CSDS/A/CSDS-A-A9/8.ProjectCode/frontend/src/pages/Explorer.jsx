import { useState } from 'react'
import { Network, Sparkles, Wand2 } from 'lucide-react'
import { Badge, Button, Card, EmptyState, Input, PageHeader } from '../components/ui'
import { api } from '../lib/api'
import { short } from '../lib/fmt'
import Gate from './Gate'
import { useAction } from './useAction'

function ExplorerView({ s }) {
  const { busy, run } = useAction()
  const [seed, setSeed] = useState('privacy')
  const [samples, setSamples] = useState([])
  const generate = async (e) => {
    e?.preventDefault()
    const out = await run('generate', () => api.generate(seed), { title: 'Sample generated', failTitle: 'Generation failed' })
    if (out) {
      setSamples((xs) => [
        { id: Date.now(), seed, text: out.text, clients: s.metrics?.active_clients, hash: s.metrics?.model_hash },
        ...xs,
      ].slice(0, 8))
    }
  }
  return (
    <div className="stack">
      <PageHeader
        eyebrow="Step 3"
        icon={Sparkles}
        title="Model explorer"
        lead="Sample the character language model before and after an unlearning request to see what it can still say."
      />

      <div className="grid-2">
        <Card hover={false} title="Generate text" subtitle="Seed the model and let it continue">
          {!s.trained ? (
            <EmptyState icon={Network} title="Train the global model first" message="Generation needs a trained model." action={<Button to="/app/training">Go to training</Button>} compact />
          ) : (
            <form className="stack" onSubmit={generate}>
              <Input label="Seed text" value={seed} onChange={(e) => setSeed(e.target.value)} hint="Letters, spaces and basic punctuation are used." maxLength={60} />
              <div>
                <Button type="submit" icon={Wand2} loading={busy === 'generate'} disabled={busy != null}>
                  Generate sample
                </Button>
              </div>
            </form>
          )}
        </Card>
        <Card hover={false} title="Method notes">
          <p className="muted">
            Every client update is L2-clipped. Gaussian noise provides the displayed one-shot (ε, δ) release bound. Unlearning subtracts the tracked parameter update, renormalises over the retained clients,
            compares with a clean retained-only recomputation, evaluates a loss-based membership attack, and records the result in the audit ledger.
          </p>
        </Card>
      </div>

      <Card hover={false} title="Samples" subtitle="Newest first. Each is tagged with the model state that produced it.">
        {samples.length === 0 ? (
          <EmptyState
            icon={Sparkles}
            title="No samples yet"
            message={s.trained ? 'Generate a sample to see the model output. Generate again after unlearning to compare.' : 'Train the model, then generate your first sample.'}
            compact
          />
        ) : (
          <ul className="stack" style={{ listStyle: 'none', padding: 0, margin: 0 }} aria-live="polite">
            {samples.map((x) => (
              <li key={x.id} style={{ background: 'var(--surface-2)', borderRadius: 18, padding: '14px 16px' }}>
                <div className="row" style={{ '--gap': '8px', flexWrap: 'wrap', marginBottom: 8 }}>
                  <Badge tone="lavender">seed “{x.seed}”</Badge>
                  <Badge tone="mint">{x.clients} active clients</Badge>
                  <span className="mono tiny muted" title={x.hash}>
                    model {short(x.hash, 10)}
                  </span>
                </div>
                <p className="mono" style={{ wordBreak: 'break-word' }}>
                  {x.text}
                </p>
              </li>
            ))}
          </ul>
        )}
      </Card>
    </div>
  )
}

export default function Explorer() {
  return <Gate kpis={0} blocks={2}>{(s) => <ExplorerView s={s} />}</Gate>
}
