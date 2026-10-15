import { useEffect, useState } from 'react'
import { BookOpen, CircleHelp, Cloud, Cpu, Info, Layers, MapPin, Network, Plane, Radar, Rocket, Route, Smartphone, TriangleAlert, Video, Waves } from 'lucide-react'
import { Badge, Card, PageHeader, Tabs, Timeline } from '../components/ui'
import { SlideUp } from '../components/motion'
import { ARCHITECTURE, BASE_PAPER_POINTS, BASE_PAPER_TEXT, FUTURE_SCOPE, NOT_IMPLEMENTED, VIVA, WHY_YOLOV8 } from '../content'

const ICONS = { Video, Plane, Waves, Route, Smartphone, Cloud, Cpu, MapPin, Layers, Radar }
const TONES = ['lavender', 'mint', 'peach', 'sky', 'rose', 'butter']
const TABS = [
  { id: 'architecture', label: 'Architecture', icon: Network },
  { id: 'paper', label: 'Base paper', icon: BookOpen },
  { id: 'future', label: 'Future scope', icon: Rocket },
  { id: 'viva', label: 'Viva Q&A', icon: CircleHelp },
]

export default function About() {
  const [tab, setTab] = useState('architecture')
  useEffect(() => {
    document.title = 'About · PlastiScan'
  }, [])

  return (
    <div>
      <PageHeader
        eyebrow="About"
        icon={Info}
        title="About this project"
        lead="Architecture, the connection to the base paper, future scope and quick answers for the viva."
      />
      <Tabs tabs={TABS} value={tab} onChange={setTab} label="About sections" name="about" />

      <div className="tab-panel" role="tabpanel" aria-label={TABS.find((t) => t.id === tab).label}>
        {tab === 'architecture' && (
          <SlideUp key="a">
            <Card title="System architecture" subtitle="From the uploaded image to the stored report" hover={false}>
              <Timeline
                items={ARCHITECTURE.map((s, i) => ({ ...s, id: s.title, tone: TONES[i % TONES.length] }))}
              />
            </Card>
          </SlideUp>
        )}

        {tab === 'paper' && (
          <SlideUp key="p" className="stack">
            <Card title="Base paper connection" hover={false}>
              <p style={{ color: 'var(--text-2)' }}>{BASE_PAPER_TEXT}</p>
              <ul className="list-plain" style={{ marginTop: 14 }}>
                {BASE_PAPER_POINTS.map((p) => (
                  <li key={p}>{p}</li>
                ))}
              </ul>
              <div className="notice warn" style={{ marginTop: 18 }}>
                <TriangleAlert size={20} aria-hidden="true" />
                <p>{NOT_IMPLEMENTED}</p>
              </div>
            </Card>
            <Card title="Why YOLOv8 (Ultralytics) instead of YOLOv7?" hover={false}>
              <p style={{ color: 'var(--text-2)' }}>{WHY_YOLOV8}</p>
            </Card>
          </SlideUp>
        )}

        {tab === 'future' && (
          <SlideUp key="f">
            <Card title="Future scope" subtitle="Ideas listed in the project report - none of these are implemented yet" hover={false} actions={<Badge tone="neutral">Not implemented</Badge>}>
              <ul className="chip-grid" style={{ listStyle: 'none', margin: 0, padding: 0 }}>
                {FUTURE_SCOPE.map((f, i) => {
                  const Icon = ICONS[f.icon]
                  return (
                    <li key={f.label} className="chip-card">
                      <span className="ico" style={{ background: `var(--${TONES[i % TONES.length]})` }}>
                        <Icon size={20} aria-hidden="true" />
                      </span>
                      <span>{f.label}</span>
                    </li>
                  )
                })}
              </ul>
            </Card>
          </SlideUp>
        )}

        {tab === 'viva' && (
          <SlideUp key="v">
            <Card title="Quick reference for the viva" hover={false}>
              <div className="faq">
                {VIVA.map((v) => (
                  <details key={v.q}>
                    <summary>{v.q}</summary>
                    <p>{v.a}</p>
                  </details>
                ))}
              </div>
            </Card>
          </SlideUp>
        )}
      </div>
    </div>
  )
}
