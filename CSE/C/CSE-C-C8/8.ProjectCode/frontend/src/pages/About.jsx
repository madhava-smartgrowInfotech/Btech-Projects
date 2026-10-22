import { Link } from 'react-router-dom'
import { ScanSearch } from 'lucide-react'
import { Badge, Button, Card, CardHeader, Container, KeyValueList, PageHeader, Timeline } from '../components/ui'
import { Stagger } from '../components/motion'
import { useStats } from '../lib/stats'

const PIPELINE = [
  { title: 'PDF extraction', body: 'PyMuPDF reads page text locally; whitespace is normalised and page numbers are kept for evidence references.' },
  { title: 'Section & feature detection', body: 'Summary, introduction, related work, methodology, experiments, results, discussion, conclusion and references are detected; reference counts and keywords are derived.' },
  { title: 'Decision signal', body: 'A TF-IDF + logistic-regression model trained by scripts/train_model.py gives a historical accept / borderline / reject signal with real, measured metrics.' },
  { title: 'Local AI review', body: 'A lazily loaded Qwen instruction model runs analyse → critique → synthesise on CPU. If it cannot load, the app says so and keeps the deterministic review.' },
  { title: 'Literature grounding', body: 'Related works come from OpenAlex with strict timeouts and are ranked by similarity. Failure degrades gracefully.' },
  { title: 'Reviewer matching', body: 'Embeddings (or TF-IDF offline) plus keyword, method, availability and conflict checks produce an auditable 0-100 ranking.' },
]

const WEIGHTS = [
  ['0.55', 'Expertise similarity'],
  ['0.20', 'Keyword overlap'],
  ['0.15', 'Method overlap'],
  ['0.10', 'Availability'],
  ['−0.60', 'Conflict penalty'],
]

export default function About() {
  const { health, error } = useStats()
  return (
    <Container>
      <PageHeader
        crumbs={[{ label: 'Workspace', to: '/app' }, { label: 'About' }]}
        title="About PeerScope"
        description="AI-assisted research-paper evaluation and transparent reviewer recommendation - for decision support."
        actions={
          <Button as={Link} to="/app/analyze" variant="primary" icon={ScanSearch}>
            Analyze a paper
          </Button>
        }
      />
      <Stagger className="stack">
        <Card>
          <CardHeader title="Pipeline" subtitle="Everything runs on your machine except the OpenAlex lookup" />
          <div className="card-body">
            <Timeline items={PIPELINE.map((p, i) => ({ key: p.title, title: `${i + 1} · ${p.title}`, body: p.body }))} />
          </div>
        </Card>

        <Card>
          <CardHeader title="Auditable reviewer matching" subtitle="Default weights - configurable in app/config.py or via PEERSCOPE_W_* settings" />
          <div className="card-body stack" style={{ gap: 14 }}>
            <div className="formula">final = 0.55·expertise + 0.20·keyword + 0.15·method + 0.10·availability − conflict_penalty → scaled 0-100</div>
            <div className="formula-weights">
              {WEIGHTS.map(([w, l]) => (
                <div className="weight" key={l}>
                  <strong>{w}</strong>
                  <span>{l}</span>
                </div>
              ))}
            </div>
            <p className="faint">Every recommendation lists its own breakdown under “Audit details”. Rankings are computed live, never hard-coded.</p>
          </div>
        </Card>

        <div className="grid grid-2">
          <Card>
            <CardHeader title="Responsible use" />
            <div className="card-body">
              <ul className="bullets warn">
                <li>AI output can contain errors; scientific validity requires human expertise.</li>
                <li>Reviewer recommendations are decision-support suggestions, not assignments.</li>
                <li>Retrieved literature is supporting context, not proof of novelty.</li>
                <li>Verify important claims and conflicts of interest independently.</li>
                <li>Never use PeerScope as the sole basis for publication decisions.</li>
              </ul>
            </div>
          </Card>
          <Card>
            <CardHeader title="Privacy" />
            <div className="card-body stack" style={{ gap: 12 }}>
              <p className="muted">
                PDFs are processed locally. Only title and topic keywords are sent to the public OpenAlex API for literature context - no document upload, no paid APIs, no credentials. Analyses store results and metadata, not copies of the PDF.
              </p>
            </div>
          </Card>
        </div>

        <Card>
          <CardHeader title="System status" subtitle="Live from the backend" />
          <div className="card-body">
            {error ? (
              <Badge tone="danger" dot>
                Backend offline - {error.message}
              </Badge>
            ) : (
              <KeyValueList
                items={[
                  ['Backend', health ? `${health.product} · ${health.status}` : 'Checking…'],
                  ['Decision model', health ? (health.model_loaded ? 'Trained model loaded' : 'Not trained') : '…'],
                  ['Local AI review', health ? (health.llm_status === 'loaded' ? 'Loaded' : 'Loads on first analysis') : '…'],
                  ['Embeddings', health ? health.embedding_status : '…'],
                  ['Literature source', health ? health.literature_retrieval : '…'],
                  ['Reviewers in directory', health?.reviewer_count],
                ]}
              />
            )}
          </div>
        </Card>
      </Stagger>
    </Container>
  )
}
