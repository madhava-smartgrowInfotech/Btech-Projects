import { lazy, Suspense, useCallback, useEffect, useState } from 'react'
import { Activity, Database, Gauge, Layers, Target, Timer } from 'lucide-react'
import { Card, Container, ErrorState, PageHeader, Skeleton, StatCard } from '../components/ui'
import { aboutApi } from '../lib/api'
import { useAuth } from '../lib/auth'

const BarBlocks = lazy(() => import('../components/ui/Charts').then((m) => ({ default: m.BarBlocks })))

const PIPELINE = [
  ['Symptoms', 'Free-text input, normalised'],
  ['HyDE expansion', 'Local hypothetical description'],
  ['Hybrid retrieval', 'FAISS semantic + BM25 lexical'],
  ['Fusion', '0.65 semantic + 0.35 lexical'],
  ['Rerank', 'Cross-encoder, top 5'],
  ['Grounded answer', 'Flan-T5 or evidence fallback'],
  ['Safety filter', 'Emergency rules + disclaimer'],
]

function Metrics() {
  const [state, setState] = useState({ loading: true, error: null, data: null })
  const load = useCallback(() => {
    setState({ loading: true, error: null, data: null })
    aboutApi
      .metrics()
      .then((data) => setState({ loading: false, error: null, data }))
      .catch((error) => setState({ loading: false, error, data: null }))
  }, [])
  useEffect(load, [load])

  if (state.loading) {
    return (
      <div className="grid grid-4" role="status" aria-label="Loading metrics">
        {[0, 1, 2, 3].map((i) => (
          <Skeleton key={i} height={130} />
        ))}
      </div>
    )
  }
  if (state.error) return <ErrorState title="Could not load evaluation metrics" error={state.error} onRetry={load} />

  const m = state.data
  const chart = [
    { metric: 'Top-1', value: Math.round(m.top1_accuracy * 100) },
    { metric: 'Top-3', value: Math.round(m.top3_accuracy * 100) },
    { metric: 'Precision', value: Math.round(m.macro_precision * 100) },
    { metric: 'Recall', value: Math.round(m.macro_recall * 100) },
    { metric: 'F1', value: Math.round(m.macro_f1 * 100) },
    { metric: 'MRR@3', value: Math.round(m.mrr_at_3 * 100) },
  ]
  return (
    <div className="stack" style={{ '--gap': '24px' }}>
      <div className="grid grid-4">
        <StatCard label="Top-1 accuracy" value={m.top1_accuracy * 100} decimals={Number.isInteger(m.top1_accuracy * 100) ? 0 : 1} icon={Target} hint={`${m.n_test} held-out queries`} />
        <StatCard label="Top-3 accuracy" value={m.top3_accuracy * 100} decimals={Number.isInteger(m.top3_accuracy * 100) ? 0 : 1} icon={Layers} hint="correct condition in top 3" />
        <StatCard label="Mean latency" value={m.mean_latency_ms} decimals={0} icon={Timer} hint="milliseconds per query" />
        <StatCard label="Knowledge base" value={m.kb_records} icon={Database} hint={`${m.kb_conditions} conditions · ${m.data_source}`} />
      </div>
      <Card title="Retrieval quality (%)">
        <Suspense fallback={<Skeleton height={280} />}>
          <BarBlocks data={chart} xKey="metric" yKey="value" name="Score (%)" height={280} />
        </Suspense>
      </Card>
      <p className="note">
        These numbers come from <code>scripts/evaluate.py</code>, which holds out one record per condition from a <strong>synthetic</strong> knowledge base
        ({m.kb_records} records). Because the held-out queries are drawn from the same synthetic data, scores are an upper bound for the pipeline wiring — not a
        measure of clinical accuracy. Embeddings: {m.embedding_mode}; reranker {m.reranker_available ? 'active' : 'unavailable'}; generator{' '}
        {m.generator_available ? 'active' : 'using evidence-based fallback'}.
      </p>
    </div>
  )
}

export default function About() {
  const { user } = useAuth()
  useEffect(() => {
    document.title = 'About - CareLens AI'
  }, [])
  const body = (
    <>
      <PageHeader
        eyebrow="About"
        title="How CareLens AI works"
        description="A local symptom-monitoring assistant that retrieves grounded medical information and states clearly what it cannot do."
      />
      <div className="stack" style={{ '--gap': '40px' }}>
        <section aria-labelledby="pipe-h" className="stack">
          <h2 id="pipe-h" className="display-sm">
            The pipeline
          </h2>
          <ol className="pipeline" aria-label="Retrieval pipeline">
            {PIPELINE.map(([t, d]) => (
              <li key={t}>
                <strong>{t}</strong>
                <span>{d}</span>
              </li>
            ))}
          </ol>
        </section>

        <section aria-labelledby="met-h" className="stack">
          <h2 id="met-h" className="display-sm">
            <Activity size={22} aria-hidden="true" style={{ display: 'inline', verticalAlign: '-3px', marginRight: 8 }} />
            Measured performance
          </h2>
          <Metrics />
        </section>

        <div className="grid grid-2">
          <Card title="What it does">
            <ul className="prose-list">
              <li>Accepts symptom descriptions in everyday language.</li>
              <li>Finds the most relevant knowledge records with hybrid retrieval and neural reranking.</li>
              <li>Writes a cautious, grounded summary with evidence and a match-relevance indicator.</li>
              <li>Escalates emergency wording (chest pain, stroke signs, self-harm and more) with urgent-care advice.</li>
            </ul>
          </Card>
          <Card title="What it is not" tone="coral">
            <p>
              <strong>CareLens AI is not a diagnostic device and does not replace a doctor.</strong> It provides preliminary information only, never medication
              instructions. Similarity is not medical probability. In an emergency, seek immediate professional care.
            </p>
          </Card>
          <Card title="Privacy">
            <p>
              Accounts and consultations are stored locally in SQLite on this machine, isolated per user, and can be deleted at any time. No symptom data is sent to
              paid external APIs and there are no analytics trackers.
            </p>
          </Card>
          <Card title="Technology">
            <p>
              FastAPI · SQLite · Sentence Transformers · FAISS · BM25 · Cross-Encoder reranking · local Flan-T5 generation with an evidence-based fallback ·
              React + Vite front end.
            </p>
          </Card>
        </div>
      </div>
    </>
  )
  return user ? body : <Container style={{ paddingTop: 36, paddingBottom: 80 }}>{body}</Container>
}
