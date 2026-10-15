import { Card, CardHeader, PageHeader } from '../components/ui'

const EXTENSIONS = [
  ['AI Career Recommendation', 'cosine-similarity skill matching against target career roles.'],
  ['Peer Mentorship', 'similarity-based mentor-student matching.'],
  ['Learn & Earn Marketplace', 'monetizing and sharing knowledge resources with a simulated in-app economy.'],
  ['AI Mock Interviews', 'role-specific question generation and local NLP-based answer scoring.'],
  ['Coding Practice', 'sandboxed code execution and skill tracking.'],
  ['Gamification', 'XP, levels, badges and leaderboards to drive engagement.'],
  ['Student Analytics', 'dashboards spanning learning, interviews, coding and marketplace activity.'],
]

const FLOW = [
  ['Student Data'],
  ['Profile Analysis'],
  ['Skill Assessment'],
  ['Knowledge-State Tracking', 'base'],
  ['Knowledge Graph', 'base'],
  ['Weak Skill Detection', 'base'],
  ['Career Goal Analysis', 'ext'],
  ['Recommendation Engine', 'ext'],
  ['Personalized Learning Roadmap'],
  ['Resources + Mentors + Projects', 'ext'],
  ['Progress Tracking'],
  ['Continuous Recommendation Update'],
]

export default function Research() {
  return (
    <>
      <PageHeader title="Research & innovation" description="What was adopted from the base paper, and what this project proposes on top of it." />
      <div className="stack">
        <Card pad>
          <span className="eyebrow">Base paper</span>
          <h2 style={{ fontSize: 22, margin: '14px 0 6px' }}>
            Enhancing Efficient Personalized Learning and Educational Management in Universities Using Graph Neural Networks in Intelligent Tutoring Systems
          </h2>
          <p className="muted">
            IEEE Access, 2026 · DOI: <a href="https://doi.org/10.1109/ACCESS.2026.3662800" target="_blank" rel="noreferrer">10.1109/ACCESS.2026.3662800</a>
          </p>
        </Card>

        <div className="grid grid-2">
          <Card>
            <CardHeader title="Base paper contribution" />
            <div className="card-body">
              <ul className="bullets" style={{ marginTop: 0 }}>
                <li>Represents a student's curriculum and knowledge as a <strong>directed graph</strong>, where topics are nodes and prerequisite relationships are edges.</li>
                <li>Tracks a <strong>per-topic knowledge state / proficiency</strong> for each student.</li>
                <li>Uses the graph structure (via a Graph Neural Network in the original paper) to reason about which prerequisite topics are weak and what should be learned next, enabling <strong>personalized tutoring paths</strong>.</li>
              </ul>
              <p className="muted mt">
                <strong>Adopted in this project:</strong> the directed prerequisite graph, per-topic proficiency tracking and weak-prerequisite detection are implemented with
                NetworkX (<code>graph/knowledge_graph.py</code>). Rather than a trained GNN, this prototype uses transparent graph traversal and weighted scoring as a
                dependency-free local substitute that captures the same underlying idea, and can be swapped for a trained GNN later without changing the rest of the
                application (<code>ai/recommendation_engine.py</code>).
              </p>
            </div>
          </Card>
          <Card>
            <CardHeader title="Proposed system extension" subtitle="The base paper's idea grown into a complete student ecosystem" />
            <div className="card-body">
              <ul className="bullets" style={{ marginTop: 0 }}>
                {EXTENSIONS.map(([t, d]) => (
                  <li key={t}>
                    <strong>{t}</strong>: {d}
                  </li>
                ))}
              </ul>
            </div>
          </Card>
        </div>

        <Card>
          <CardHeader
            title="System architecture"
            subtitle="Green steps come from the base paper; blue steps are the proposed extension"
          />
          <div className="card-body">
            <ol className="flow" style={{ listStyle: 'none', margin: 0, padding: 0 }}>
              {FLOW.map(([label, kind], i) => (
                <li key={label} style={{ display: 'contents' }}>
                  <div className={kind || ''}>
                    {label}
                    {kind === 'base' && <span className="faint"> · base paper concept</span>}
                    {kind === 'ext' && <span className="faint"> · proposed extension</span>}
                  </div>
                  {i < FLOW.length - 1 && <span aria-hidden="true">↓</span>}
                </li>
              ))}
            </ol>
          </div>
        </Card>

        <p className="faint">
          This page is intended for project review, viva and research presentation, and clearly separates what was adopted from the base paper from what was newly proposed.
        </p>
      </div>
    </>
  )
}
