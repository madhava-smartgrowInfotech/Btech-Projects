import { useState } from 'react'
import { AlertTriangle, BookOpen, Download, FileJson, FileText, Info, ShieldAlert, Sparkles, Users } from 'lucide-react'
import { Badge, Button, Card, CardHeader, KeyValueList, ProgressBar, StatCard, Table, Tabs, EmptyState, useToast } from './ui'
import { download, exportPath } from '../lib/api'
import { num1, scoreTone } from '../lib/format'
import { Stagger } from './motion'

const TABS = [
  { value: 'overview', label: 'Overview', icon: FileText },
  { value: 'review', label: 'Review', icon: Sparkles },
  { value: 'literature', label: 'Literature', icon: BookOpen },
  { value: 'reviewers', label: 'Reviewers', icon: Users },
  { value: 'audit', label: 'Audit & export', icon: ShieldAlert },
]

const LABEL_TONE = { accept: 'safe', borderline: 'warn', reject: 'danger' }

function List({ items, tone, empty }) {
  if (!items?.length) return <p className="faint">{empty}</p>
  return (
    <ul className={`bullets ${tone || ''}`}>
      {items.map((t, i) => (
        <li key={i}>{t}</li>
      ))}
    </ul>
  )
}

// The AI synthesis is model-written markdown-ish text: render headings, bullets and paragraphs without trusting HTML.
function Prose({ text }) {
  const blocks = []
  let list = null
  for (const raw of String(text || '').split(/\r?\n/)) {
    const line = raw.trim()
    if (!line) {
      list = null
      continue
    }
    const h = line.match(/^#{1,6}\s+(.*)$/)
    const b = line.match(/^[-*•]\s+(.*)$/) || line.match(/^\d+[.)]\s+(.*)$/)
    if (h) {
      list = null
      blocks.push({ t: 'h', v: h[1].replace(/\*\*/g, '') })
    } else if (b) {
      if (!list) {
        list = { t: 'ul', v: [] }
        blocks.push(list)
      }
      list.v.push(b[1].replace(/\*\*/g, ''))
    } else {
      list = null
      blocks.push({ t: 'p', v: line.replace(/\*\*/g, '') })
    }
  }
  return (
    <div className="md">
      {blocks.map((b, i) =>
        b.t === 'h' ? (
          <h4 key={i}>{b.v}</h4>
        ) : b.t === 'ul' ? (
          <ul key={i}>
            {b.v.map((x, j) => (
              <li key={j}>{x}</li>
            ))}
          </ul>
        ) : (
          <p key={i}>{b.v}</p>
        ),
      )}
    </div>
  )
}

function Overview({ r }) {
  const f = r.features || {}
  const ml = r.ml_decision_signal || {}
  const rev = r.review || {}
  const paper = r.paper || {}
  const probs = Object.entries(ml.probabilities || {})
  // the backend can return a label without class probabilities; don't draw a fake 0% / 100% bar for that
  const calibrated = ml.status === 'ok' && ml.confidence > 0 && probs.length > 1
  return (
    <div className="stack">
      <Card>
        <CardHeader title="Paper overview" subtitle={paper.title || r.filename} actions={<Badge>{paper.page_count} pages</Badge>} />
        <div className="card-body stack" style={{ gap: 14 }}>
          <p className="muted">{paper.paper_summary || 'No summary could be extracted from this PDF.'}</p>
          <KeyValueList
            items={[
              ['File', r.filename],
              ['Words', f.word_count?.toLocaleString()],
              ['References detected', f.reference_count],
              ['Sections detected', (f.detected_sections || []).join(', ') || 'none'],
              ['Sections not detected', (f.missing_sections || []).join(', ') || 'none'],
              ['Keywords', (f.keywords || []).join(', ') || '-'],
            ]}
          />
          {paper.pages_preview?.length > 0 && (
            <details className="audit">
              <summary>Extracted text preview (first {paper.pages_preview.length} pages)</summary>
              <div className="audit-body">
                {paper.pages_preview.map((p) => (
                  <p key={p.page} className="faint pre-wrap">
                    <strong>p.{p.page}</strong> - {(p.text || '').slice(0, 500)}…
                  </p>
                ))}
              </div>
            </details>
          )}
        </div>
      </Card>

      <Card>
        <CardHeader title="Preliminary assessment" subtitle="One input among many - not a judgment of scientific correctness" />
        <div className="card-body stack" style={{ gap: 16 }}>
          <p>{r.overall_assessment}</p>
          <div className="grid grid-3">
            <div className="stack" style={{ gap: 8 }}>
              <span className="faint">Historical decision signal</span>
              <div>
                <Badge tone={ml.status === 'ok' ? LABEL_TONE[ml.label] || 'info' : 'warn'} dot>
                  {ml.status !== 'ok' ? 'Unavailable' : calibrated ? `${ml.label} · ${(ml.confidence * 100).toFixed(0)}% confidence` : ml.label}
                </Badge>
              </div>
              {calibrated && probs.map(([k, v]) => (
                <ProgressBar key={k} label={k} valueLabel={`${(v * 100).toFixed(1)}%`} value={v} max={1} />
              ))}
              <p className="faint">{ml.note}</p>
            </div>
            <div className="stack" style={{ gap: 8 }}>
              <span className="faint">Structural score</span>
              <strong style={{ font: '800 34px/1 var(--font-display)' }}>{num1(f.overall_structural, 1)}<span className="faint"> / 100</span></strong>
              <ProgressBar label="Structure completeness" valueLabel={num1(f.structure_completeness, 1)} value={f.structure_completeness || 0} max={100} />
              <ProgressBar label="Evidence coverage" valueLabel={num1(f.evidence_coverage, 1)} value={f.evidence_coverage || 0} max={100} />
              <ProgressBar label="Method clarity" valueLabel={num1(f.method_clarity_signal, 1)} value={f.method_clarity_signal || 0} max={100} />
              <ProgressBar label="Presentation" valueLabel={num1(f.presentation_signal, 1)} value={f.presentation_signal || 0} max={100} />
            </div>
            <div className="stack" style={{ gap: 8 }}>
              <span className="faint">Local AI review</span>
              <div>
                <Badge tone={rev.llm_status === 'ok' ? 'safe' : 'warn'} dot>
                  {rev.llm_status === 'ok' ? `Generated by ${rev.llm_model || 'local model'}` : 'Unavailable'}
                </Badge>
              </div>
              <p className="faint">{rev.llm_note || (rev.llm_status === 'ok' ? 'Three-step pipeline: analyze, critique, synthesize.' : 'The deterministic analysis below is still complete; no AI text was fabricated.')}</p>
            </div>
          </div>
          {r.warning && (
            <div className="note warn" role="status">
              <AlertTriangle size={18} aria-hidden="true" />
              <span>{r.warning}</span>
            </div>
          )}
        </div>
      </Card>
    </div>
  )
}

function Review({ r }) {
  const rev = r.review || {}
  const q = r.review_quality || {}
  const cov = Object.entries(rev.coverage || {})
  const assess = [
    ['Methodology', rev.methodology_assessment],
    ['Evidence', rev.evidence_assessment],
    ['Clarity', rev.clarity_assessment],
    ['Reproducibility', rev.reproducibility_assessment],
    ['Novelty', rev.novelty_considerations],
  ].filter(([, v]) => v)
  return (
    <div className="stack">
      <div className="grid grid-2">
        <Card>
          <CardHeader title={`Strengths (${rev.strengths?.length || 0})`} />
          <div className="card-body">
            <List items={rev.strengths} empty="No strengths were detected from the extracted text." />
          </div>
        </Card>
        <Card>
          <CardHeader title={`Major concerns (${rev.major_concerns?.length || 0})`} />
          <div className="card-body">
            <List items={rev.major_concerns} tone="danger" empty="No major concerns were raised." />
          </div>
        </Card>
        <Card>
          <CardHeader title={`Minor concerns (${rev.minor_concerns?.length || 0})`} />
          <div className="card-body">
            <List items={rev.minor_concerns} tone="warn" empty="No minor concerns were raised." />
          </div>
        </Card>
        <Card>
          <CardHeader title={`Actionable recommendations (${rev.recommendations?.length || 0})`} />
          <div className="card-body">
            <List items={rev.recommendations} tone="info" empty="No recommendations were generated." />
          </div>
        </Card>
      </div>

      {assess.length > 0 && (
        <Card>
          <CardHeader title="Dimension notes" subtitle="Deterministic notes derived from the extracted text" />
          <div className="card-body">
            <KeyValueList items={assess} />
          </div>
        </Card>
      )}

      <Card>
        <CardHeader title="Review coverage" subtitle="Derived from generated content and detected evidence" />
        <div className="card-body stack" style={{ gap: 14 }}>
          {cov.length ? (
            <div className="bar-list">
              {cov.map(([k, v]) => (
                <ProgressBar key={k} label={k} valueLabel={`${v}%`} value={v} max={100} />
              ))}
            </div>
          ) : (
            <p className="faint">No coverage data for this analysis.</p>
          )}
          <p className="faint">
            Counted: {q.num_strengths} strengths, {q.num_major} major and {q.num_minor} minor concerns, {q.num_recommendations} recommendations, {q.num_evidence_refs} evidence references.
          </p>
        </div>
      </Card>

      {rev.ai_synthesis ? (
        <Card>
          <CardHeader title="AI synthesis" subtitle={`Local model${rev.llm_model ? ` · ${rev.llm_model}` : ''} - can contain errors`} />
          <div className="card-body">
            <Prose text={rev.ai_synthesis} />
          </div>
        </Card>
      ) : (
        <div className="note warn">
          <Info size={18} aria-hidden="true" />
          <span>No AI synthesis for this analysis{rev.llm_status && rev.llm_status !== 'ok' ? ` (status: ${rev.llm_status})` : ''}. The sections above come from the deterministic checks.</span>
        </div>
      )}

      {rev.evidence_references?.length > 0 && (
        <Card>
          <CardHeader title="Evidence references" subtitle="Page-anchored excerpts the review relied on" />
          <div className="card-body">
            <ul className="bullets info">
              {rev.evidence_references.map((t, i) => (
                <li key={i} className="pre-wrap">
                  {String(t).slice(0, 320)}
                </li>
              ))}
            </ul>
          </div>
        </Card>
      )}
    </div>
  )
}

function Literature({ r }) {
  const lit = r.literature || {}
  if (lit.literature_retrieval_status !== 'ok') {
    return (
      <div className="note warn" role="status">
        <AlertTriangle size={18} aria-hidden="true" />
        <span>
          Related-literature retrieval was unavailable{lit.error ? ` (${lit.error})` : ''}. The analysis continued with local content only. This usually means no internet access to OpenAlex.
        </span>
      </div>
    )
  }
  const cols = [
    {
      key: 'title',
      label: 'Title',
      render: (w) => (
        <div>
          {w.url ? (
            <a href={w.url} target="_blank" rel="noreferrer">
              {w.title}
            </a>
          ) : (
            w.title
          )}
          {w.authors?.length > 0 && <div className="faint">{w.authors.slice(0, 3).join(', ')}{w.authors.length > 3 ? ' et al.' : ''}</div>}
        </div>
      ),
      sortValue: (w) => w.title,
    },
    { key: 'year', label: 'Year', num: true, render: (w) => w.year ?? '-' },
    { key: 'source', label: 'Source', hideSm: true, render: (w) => w.source || '-' },
    { key: 'relevance', label: 'Relevance', num: true, render: (w) => num1(w.relevance, 3) },
  ]
  return (
    <Card>
      <CardHeader title="Related literature" subtitle={`${lit.source || 'OpenAlex'} · query: “${lit.query || ''}” - supporting context, not proof of novelty`} />
      <Table columns={cols} rows={lit.works || []} rowKey={(w) => w.url || w.doi || w.title} pageSize={8} initialSort={{ key: 'relevance', dir: 'desc' }} caption="Related literature" empty={<EmptyState title="No related works returned" />} />
    </Card>
  )
}

function ReviewerCard({ v }) {
  const b = v.breakdown || {}
  const w = b.weights || {}
  const rows = [
    ['Expertise similarity (cosine)', b.expertise_similarity, w.expertise_similarity],
    ['Topic / keyword overlap', b.keyword_score, w.keyword_score],
    ['Method overlap', b.method_score, w.method_score],
    ['Availability', b.availability_score, w.availability_score],
  ]
  const av = v.availability || {}
  return (
    <Card className="rev-card" as="article" aria-label={`Rank ${v.rank}: ${v.display_name}`}>
      <div className="rev-head">
        <div style={{ minWidth: 0 }}>
          <div className="rev-rank">RANK {v.rank}</div>
          <div className="rev-name">{v.display_name}</div>
          <div className="faint">{v.affiliation || 'No affiliation listed'}</div>
        </div>
        <div className="rev-score">
          <strong>{num1(v.score, 1)}</strong>
          <span>match score / 100</span>
          <div style={{ marginTop: 6 }}>
            <Badge tone={scoreTone(v.score)} dot>
              {v.match_strength}
            </Badge>
          </div>
        </div>
      </div>
      <ProgressBar label="Overall match" value={v.score} max={100} valueLabel={`${num1(v.score, 1)}`} />
      {v.expertise && <p className="muted">{v.expertise}</p>}
      <div className="tag-row" aria-label="Matching terms">
        {(v.matching_topics || []).map((t) => (
          <Badge key={`t-${t}`} tone="info">
            {t}
          </Badge>
        ))}
        {(v.matching_methods || []).map((t) => (
          <Badge key={`m-${t}`}>{t}</Badge>
        ))}
        {!v.matching_topics?.length && !v.matching_methods?.length && <span className="faint">No overlapping terms found.</span>}
      </div>
      <div className="rev-meta">
        <ProgressBar label="Current workload" value={av.current_load || 0} max={av.maximum_load || 1} valueLabel={`${av.current_load}/${av.maximum_load}`} />
        <div>
          <span className="faint">Conflict check</span>
          <div style={{ marginTop: 6 }}>
            {v.conflict?.conflicted ? (
              <Badge tone="danger" dot>
                Conflict: {v.conflict.reason || 'flagged'}
              </Badge>
            ) : (
              <Badge tone="safe" dot>
                None detected
              </Badge>
            )}
          </div>
        </div>
      </div>
      <details className="audit">
        <summary>Audit details - score breakdown</summary>
        <div className="audit-body">
          <div className="table-wrap">
            <table className="table">
              <thead>
                <tr>
                  <th scope="col">Signal</th>
                  <th scope="col" className="num">
                    Value (0-1)
                  </th>
                  <th scope="col" className="num">
                    Weight
                  </th>
                </tr>
              </thead>
              <tbody>
                {rows.map(([k, val, wt]) => (
                  <tr key={k}>
                    <td>{k}</td>
                    <td className="num">{num1(val, 3)}</td>
                    <td className="num">{wt ?? '-'}</td>
                  </tr>
                ))}
                <tr>
                  <td>Conflict penalty</td>
                  <td className="num">{num1(b.conflict_penalty, 3)}</td>
                  <td className="num">−{w.conflict_penalty ?? '-'}</td>
                </tr>
                <tr>
                  <td>
                    <strong>Final score (0-100)</strong>
                  </td>
                  <td className="num" colSpan={2}>
                    <strong>{num1(v.score, 1)}</strong>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
          {v.explanation && <p className="faint">{v.explanation}</p>}
        </div>
      </details>
    </Card>
  )
}

function Reviewers({ r }) {
  const list = r.reviewers || []
  if (!list.length) {
    return (
      <EmptyState icon={Users} title="No reviewers matched the current filters">
        {r.reviewer_pool_size ?? 0} reviewers are in the directory. Loosen the minimum score, clear the topic/method filters, or include inactive reviewers and analyze again.
      </EmptyState>
    )
  }
  return (
    <div className="stack">
      <p className="faint">
        Top {list.length} of {r.reviewer_pool_size} reviewers in the directory. Recommendations are suggestions - verify conflicts of interest independently.
      </p>
      <Stagger className="stack">
        {list.map((v) => (
          <ReviewerCard key={v.reviewer_id ?? v.rank} v={v} />
        ))}
      </Stagger>
    </div>
  )
}

function Audit({ r, id }) {
  const toast = useToast()
  const [busy, setBusy] = useState('')
  const w = r.reviewers?.[0]?.breakdown?.weights
  const get = async (format) => {
    setBusy(format)
    try {
      await download(exportPath(id, format), `peerscope_analysis_${id}.${format}`)
      toast({ title: `${format.toUpperCase()} exported`, message: `Analysis #${id} downloaded.` })
    } catch (e) {
      toast({ title: `Could not export ${format.toUpperCase()}`, message: e.message, tone: 'error' })
    } finally {
      setBusy('')
    }
  }
  return (
    <div className="stack">
      <Card>
        <CardHeader title="Audit details" subtitle="Everything needed to reproduce this ranking" />
        <div className="card-body stack" style={{ gap: 14 }}>
          <div className="formula">final = {w ? `${w.expertise_similarity}·expertise + ${w.keyword_score}·keyword + ${w.method_score}·method + ${w.availability_score}·availability − ${w.conflict_penalty}·conflict` : '0.55·expertise + 0.20·keyword + 0.15·method + 0.10·availability − conflict penalty'}  → scaled 0-100</div>
          <KeyValueList
            items={[
              ['Analysis ID', id ?? 'not saved'],
              ['Created', r.created_at ? new Date(r.created_at).toLocaleString() : '-'],
              ['Reviewer pool size', r.reviewer_pool_size],
              ['Review source', r.review?.source],
              ['Literature status', r.literature?.literature_retrieval_status],
              ['Decision model status', r.ml_decision_signal?.status],
            ]}
          />
        </div>
      </Card>
      <Card>
        <CardHeader title="Export" subtitle="Download the complete analysis" />
        <div className="card-body row">
          {id ? (
            <>
              <Button icon={FileJson} loading={busy === 'json'} onClick={() => get('json')}>
                Export JSON
              </Button>
              <Button icon={Download} loading={busy === 'pdf'} onClick={() => get('pdf')}>
                Export PDF
              </Button>
            </>
          ) : (
            <p className="faint">This result has no saved analysis ID, so it cannot be exported.</p>
          )}
        </div>
      </Card>
      <div className="note">
        <Info size={18} aria-hidden="true" />
        <span>{r.disclaimer}</span>
      </div>
      {r.responsible_use && <p className="faint">{r.responsible_use}</p>}
    </div>
  )
}

export default function AnalysisResult({ result, id }) {
  const [tab, setTab] = useState('overview')
  const r = result
  const rev = r.review || {}
  return (
    <div>
      <div className="grid grid-4">
        <StatCard label="Structural score" value={r.features?.overall_structural ?? '-'} format={(v) => v.toFixed(1)} icon={FileText} />
        <StatCard label="Concerns raised" value={r.concern_count ?? 0} icon={AlertTriangle} tone="warn" delta={`${rev.major_concerns?.length || 0} major`} />
        <StatCard label="Recommendations" value={r.recommendation_count ?? 0} icon={Sparkles} tone="info" />
        <StatCard label="Top reviewer" value={r.top_reviewer || 'None matched'} icon={Users} delta={r.reviewers?.[0] ? `score ${num1(r.reviewers[0].score, 1)}` : undefined} />
      </div>
      <div className="result-tabs">
        <Tabs tabs={TABS} value={tab} onChange={setTab} label="Analysis sections" />
      </div>
      <div role="tabpanel" aria-label={TABS.find((t) => t.value === tab)?.label}>
        {tab === 'overview' && <Overview r={r} />}
        {tab === 'review' && <Review r={r} />}
        {tab === 'literature' && <Literature r={r} />}
        {tab === 'reviewers' && <Reviewers r={r} />}
        {tab === 'audit' && <Audit r={r} id={id ?? r.analysis_id} />}
      </div>
    </div>
  )
}
