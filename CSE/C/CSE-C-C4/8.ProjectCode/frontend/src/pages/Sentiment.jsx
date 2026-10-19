import { useMemo, useState } from 'react'
import { Gauge, Info, MessageSquareText, Newspaper, RefreshCw, SearchX, Sparkles } from 'lucide-react'
import { Badge, Button, Card, EmptyState, ErrorState, PageHeader, ProgressBar, Segmented, SearchField, Skeleton, StatCard } from '../components/ui'
import { LineCompare } from '../components/charts'
import { TickerTabs, useTicker } from '../components/app/parts'
import { api } from '../lib/api'
import { useAsync, useRefresh } from '../lib/hooks'
import { companyOf, tone, toneLabel } from '../lib/market'
import { dateLabel, fmtNum, fmtInt } from '../lib/format'
import { useChartTheme } from '../lib/palette'

const TONES = [
  { value: 'all', label: 'All' },
  { value: 'Positive', label: 'Positive' },
  { value: 'Neutral', label: 'Neutral' },
  { value: 'Negative', label: 'Negative' },
]

/** The first call loads FinBERT (and downloads it on a cold cache), so tell the user why it is slow. */
function SentimentLoading({ ticker }) {
  return (
    <div className="stack" role="status" aria-label="Loading sentiment">
      <div className="note">
        <Info size={18} aria-hidden="true" />
        <span>
          Scoring {ticker} headlines with FinBERT. The first request after starting the API loads the language model, which can take a minute.
        </span>
      </div>
      <ProgressBar indeterminate label="Scoring headlines" />
      <div className="grid-kpi">
        {[0, 1, 2, 3].map((i) => (
          <div key={i} className="card">
            <Skeleton width="55%" height={14} />
            <Skeleton width="70%" height={30} style={{ marginTop: 14 }} />
          </div>
        ))}
      </div>
      <div className="card">
        <Skeleton height={260} radius={18} />
      </div>
    </div>
  )
}

export default function Sentiment() {
  const list = useAsync((signal) => api.tickers({ signal }), [])
  const names = useMemo(() => list.data?.tickers.map((x) => x.ticker) || [], [list.data])
  const [ticker, setTicker] = useTicker(names)
  const t = useChartTheme()
  const [q, setQ] = useState('')
  const [toneFilter, setToneFilter] = useState('all')

  const view = useAsync((signal) => (names.length ? api.sentiment(ticker, { signal }) : null), [ticker, names.length])
  const refresh = useRefresh(view, `${ticker} sentiment refreshed`)
  const d = view.data

  const daily = useMemo(() => (d?.daily || []).map((x) => ({ x: x.date, score: x.score })), [d])
  const avg = daily.length ? daily.reduce((a, b) => a + b.score, 0) / daily.length : null
  const latest = daily.length ? daily[daily.length - 1].score : null
  const headlines = useMemo(
    () =>
      (d?.headlines || [])
        .map((h) => ({ ...h, label: toneLabel(h.sentiment_score) }))
        .filter((h) => (toneFilter === 'all' || h.label === toneFilter) && (!q || h.headline.toLowerCase().includes(q.toLowerCase()))),
    [d, q, toneFilter],
  )
  const clear = () => {
    setQ('')
    setToneFilter('all')
  }

  return (
    <div className="stack" style={{ '--gap': '22px' }}>
      <PageHeader
        eyebrow="News sentiment"
        icon={MessageSquareText}
        title={`${ticker} news mood`}
        lead="Headline tone scored by FinBERT, aligned to trading days. It is the extra input channel of the sentiment tier."
        actions={
          <Button variant="secondary" icon={RefreshCw} loading={view.loading && !!d} onClick={refresh}>
            Refresh
          </Button>
        }
      />

      {list.error && <ErrorState title="Could not load the ticker list" error={list.error} onRetry={list.reload} />}

      {names.length > 0 && (
        <>
          <div className="toolbar">
            <TickerTabs tickers={names} value={ticker} onChange={setTicker} />
          </div>

          {view.loading && !d && <SentimentLoading ticker={ticker} />}
          {view.error && <ErrorState title={`Could not load ${ticker} sentiment`} error={view.error} onRetry={view.reload} />}

          {d && (
            <div className="stack" style={{ '--gap': '22px', opacity: view.loading ? 0.6 : 1, transition: 'opacity .2s' }} aria-busy={view.loading}>
              <div className="grid-kpi">
                <StatCard
                  label="News source"
                  display={d.meta.source === 'newsapi' ? 'NewsAPI (live)' : 'Built-in fallback'}
                  icon={Newspaper}
                  tone={d.meta.source === 'newsapi' ? 'mint' : 'peach'}
                  foot={`scorer: ${d.meta.scorer}`}
                />
                <StatCard label="Headlines scored" value={d.meta.n_headlines} format={fmtInt} icon={Sparkles} tone="lavender" foot={companyOf(ticker)} />
                <StatCard label="30-day average score" display={avg == null ? '–' : fmtNum(avg, 3)} icon={Gauge} tone="sky" foot="-1 negative, +1 positive" />
                <StatCard
                  label="Latest day"
                  display={latest == null ? '–' : fmtNum(latest, 3)}
                  icon={MessageSquareText}
                  tone={latest > 0.15 ? 'mint' : latest < -0.15 ? 'rose' : 'peach'}
                  foot={latest == null ? undefined : toneLabel(latest)}
                />
              </div>

              {d.meta.note && (
                <div className="note warn" role="note">
                  <Info size={18} aria-hidden="true" />
                  <span>{d.meta.note}</span>
                </div>
              )}

              <Card title="Daily sentiment" subtitle="Average headline score per trading day, last 30 days.">
                {daily.length === 0 ? (
                  <EmptyState compact icon={SearchX} title="No daily scores" message="The API returned no sentiment days for this ticker." />
                ) : (
                  <LineCompare
                    data={daily}
                    dots={false}
                    domain={[-1, 1]}
                    xFormat={(v, ...r) => dateLabel(v)}
                    valueFormat={(v) => fmtNum(v, 3)}
                    yFormat={(v) => fmtNum(v, 1)}
                    series={[{ key: 'score', name: 'Sentiment', color: t.mint }]}
                    label={`${ticker} daily news sentiment over the last 30 trading days`}
                  />
                )}
              </Card>

              <Card title="Recent headlines" subtitle={`${d.headlines.length} headlines with their FinBERT tone.`}>
                <div className="table-tools">
                  <SearchField value={q} onChange={setQ} placeholder="Search headlines" label="Search headlines" />
                  <Segmented name="tone" label="Tone" value={toneFilter} onChange={setToneFilter} options={TONES} />
                </div>
                {d.headlines.length === 0 ? (
                  <EmptyState compact icon={Newspaper} title="No headlines" message="This ticker has no scored headlines yet." />
                ) : headlines.length === 0 ? (
                  <EmptyState
                    compact
                    icon={SearchX}
                    title="No matching headlines"
                    message="Nothing fits the current search and tone filter."
                    action={<Button variant="secondary" onClick={clear}>Clear filters</Button>}
                  />
                ) : (
                  <ul className="headline-list">
                    {headlines.map((h, i) => (
                      <li key={`${h.headline}-${i}`} className="headline">
                        <p>{h.headline}</p>
                        <div className="score">
                          <Badge tone={tone(h.sentiment_score)}>{h.label}</Badge>
                          <span className="small muted num">score {fmtNum(h.sentiment_score, 3)}</span>
                        </div>
                      </li>
                    ))}
                  </ul>
                )}
              </Card>
            </div>
          )}
        </>
      )}
    </div>
  )
}
