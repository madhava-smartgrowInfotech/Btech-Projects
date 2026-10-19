import { useSearchParams } from 'react-router-dom'
import { ArrowDownRight, ArrowUpRight } from 'lucide-react'
import { Badge, Tabs } from '../ui'
import { companyOf } from '../../lib/market'

export function TrendBadge({ trend }) {
  if (!trend) return <Badge tone="neutral">No trend</Badge>
  return trend === 'up' ? (
    <Badge tone="mint" icon={ArrowUpRight}>
      Trend up
    </Badge>
  ) : (
    <Badge tone="rose" icon={ArrowDownRight}>
      Trend down
    </Badge>
  )
}

const MODE = { live: ['sky', 'Live Yahoo data'], csv: ['lavender', 'Bundled CSV data'], synthetic: ['peach', 'Synthetic data'] }
export function ModeBadge({ mode }) {
  const [tone, text] = MODE[mode] || ['neutral', mode || 'Unknown']
  return <Badge tone={tone}>{text}</Badge>
}

/** Ticker selection kept in the URL (?t=TSLA) so a view can be shared and survives a refresh. */
export function useTicker(tickers) {
  const [params, setParams] = useSearchParams()
  const first = tickers?.[0] || 'TSLA'
  const asked = (params.get('t') || '').toUpperCase()
  const ticker = tickers?.length ? (tickers.includes(asked) ? asked : first) : asked || first
  const set = (t) =>
    setParams(
      (p) => {
        const n = new URLSearchParams(p)
        n.set('t', t)
        return n
      },
      { replace: true },
    )
  return [ticker, set, params, setParams]
}

export function TickerTabs({ tickers, value, onChange }) {
  return (
    <div className="stack" style={{ '--gap': '6px' }}>
      <Tabs
        name="ticker"
        label="Ticker"
        value={value}
        onChange={onChange}
        tabs={tickers.map((t) => ({ id: t, label: t }))}
      />
      <span className="small muted">{companyOf(value)}</span>
    </div>
  )
}
