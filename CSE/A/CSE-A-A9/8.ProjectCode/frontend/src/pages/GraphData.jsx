import { Database, Layers, Network, Radar, Share2, Users } from 'lucide-react'
import { api } from '../lib/api'
import { useAsync } from '../lib/hooks'
import { fmtInt, fmtNum, fmtPct } from '../lib/format'
import { Badge, Card, PageHeader, StatCard, Table } from '../components/ui'
import { BarCompare, GroupedBars } from '../components/charts'
import { Callout, Load } from '../components/app'
import { Stagger } from '../components/motion'
import { useChartTheme } from '../lib/palette'

const GROUP_TONE = { 'Profile metadata': 'lavender', 'Posting behaviour': 'sky', 'Temporal pattern': 'peach', 'Interaction frequency': 'mint' }

export default function GraphData() {
  const state = useAsync(() => api.graph(), [])
  const t = useChartTheme()
  return (
    <div className="stack" style={{ '--gap': '24px' }}>
      <PageHeader
        eyebrow="Graph & features"
        icon={Network}
        title="How the graph is built"
        lead="Accounts are nodes, interactions are edges. This is the graph the models read, which parts are real data, and the 23 features each account carries."
      />
      <Load state={state} title="Could not load the graph summary">
        {(g) => {
          const split = g.split
          return (
            <>
              <Stagger className="grid-kpi">
                <Stagger.Item>
                  <StatCard label="Accounts (nodes)" value={g.nodes} format={fmtInt} icon={Users} tone="sky" foot={`${fmtInt(g.real_nodes)} real topology · ${fmtInt(g.injected_nodes)} injected`} />
                </Stagger.Item>
                <Stagger.Item>
                  <StatCard label="Interactions (edges)" value={g.edges} format={fmtInt} icon={Share2} tone="lavender" foot={`${fmtInt(g.real_edges)} real · ${fmtInt(g.injected_edges)} injected`} />
                </Stagger.Item>
                <Stagger.Item>
                  <StatCard label="Fake accounts" value={g.fake_accounts} format={fmtInt} icon={Radar} tone="rose" foot={`${fmtPct(g.fake_share, 1)} - a heavily imbalanced set`} />
                </Stagger.Item>
                <Stagger.Item>
                  <StatCard label="Features per account" value={g.n_features} format={fmtInt} icon={Layers} tone="mint" foot={`avg ${fmtNum(g.avg_degree, 1)} ties per account`} />
                </Stagger.Item>
              </Stagger>

              <Callout tone="info" title="Graph schema">
                <ul className="note-list">
                  <li>
                    <b>Node</b> = one account, with {g.n_features} numeric features in four groups and a label (fake or genuine) used only for training and evaluation.
                  </li>
                  <li>
                    <b>Edge</b> = an undirected tie between two accounts (follow, like or comment). Each edge is marked <Badge tone="neutral">real</Badge> or <Badge tone="rose">injected</Badge>.
                  </li>
                  <li>
                    <b>Split</b> = stratified {split.train} train · {split.val} validation · {split.test} test accounts, the same for every model.
                  </li>
                </ul>
              </Callout>

              <div className="grid-2">
                <Card title="Real and injected parts" subtitle="Injected botnets give cluster detection a known answer to be measured against.">
                  <BarCompare
                    height={230}
                    horizontal
                    yWidth={170}
                    valueFormat={fmtInt}
                    label="Real versus injected nodes and edges"
                    data={[
                      { name: 'Nodes - real topology', value: g.real_nodes, color: t.sky },
                      { name: 'Nodes - injected bots', value: g.injected_nodes, color: t.rose },
                      { name: 'Edges - real', value: g.real_edges, color: t.mint },
                      { name: 'Edges - injected', value: g.injected_edges, color: t.peach },
                    ]}
                  />
                  <p className="small muted" style={{ marginTop: 10 }}>
                    {g.botnets_injected} botnets of {g.meta.botnet_sizes.join(', ')} accounts plus {g.meta.n_lone_bots} lone spammers. {g.meta.camouflaged_bots} bots have a genuine-looking profile on purpose, and {g.meta.suspicious_genuine} genuine accounts look suspicious, so the profile alone is never enough.
                  </p>
                </Card>
                <Card title="Ties per account" subtitle="Fake accounts have few ties compared with well-connected genuine ones.">
                  <GroupedBars
                    height={260}
                    data={g.degree_histogram.map((b) => ({ x: b.bin, genuine: b.genuine, fake: b.fake }))}
                    series={[
                      { key: 'genuine', name: 'Genuine', color: t.mint },
                      { key: 'fake', name: 'Fake', color: t.rose },
                    ]}
                    valueFormat={fmtInt}
                    label="Number of accounts by degree, genuine versus fake"
                  />
                </Card>
              </div>

              <Card title="Where the data comes from" subtitle="Three public datasets plus a seeded generator. Nothing here is scraped from a live platform." actions={<Database size={20} aria-hidden="true" />}>
                <div className="provenance">
                  {g.datasets.map((d) => (
                    <div className="src" key={d.name}>
                      <b>
                        {d.name} <Badge tone={d.real ? 'mint' : 'peach'}>{d.real ? 'real data' : 'synthetic, seeded'}</Badge> <Badge tone="neutral">{d.licence}</Badge>
                      </b>
                      <span className="small muted">
                        {d.role} · {d.used_for}
                      </span>
                    </div>
                  ))}
                </div>
              </Card>

              <Card title="Node features" subtitle="Average value for genuine and fake accounts (standardised units are used for training).">
                <Table
                  caption="Node features"
                  rowKey={(r) => r.name}
                  pageSize={12}
                  searchKeys={['label', 'group']}
                  searchPlaceholder="Search features"
                  cardTitle={(r) => r.label}
                  columns={[
                    { key: 'label', label: 'Feature', wrap: true },
                    { key: 'group', label: 'Group', render: (r) => <Badge tone={GROUP_TONE[r.group] || 'neutral'}>{r.group}</Badge> },
                    { key: 'mean_genuine', label: 'Mean · genuine', numeric: true, render: (r) => fmtNum(r.mean_genuine, 2) },
                    { key: 'mean_fake', label: 'Mean · fake', numeric: true, render: (r) => fmtNum(r.mean_fake, 2) },
                    {
                      key: 'gap',
                      label: 'Gap (in std devs)',
                      numeric: true,
                      sortValue: (r) => Math.abs(r.mean_fake - r.mean_genuine) / (r.std || 1),
                      render: (r) => fmtNum((r.mean_fake - r.mean_genuine) / (r.std || 1), 2),
                    },
                  ]}
                  rows={g.features}
                  initialSort={{ key: 'gap', dir: 'desc' }}
                />
              </Card>
            </>
          )
        }}
      </Load>
    </div>
  )
}
