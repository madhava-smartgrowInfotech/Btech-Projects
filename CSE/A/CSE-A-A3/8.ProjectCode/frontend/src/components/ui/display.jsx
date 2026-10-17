import { useId, useMemo, useState } from 'react'
import { ArrowDown, ArrowUp, ArrowUpDown, ChevronLeft, ChevronRight } from 'lucide-react'
import { CountUp } from '../motion'
import { Button } from './controls'
import { EmptyState, Skeleton } from './feedback'

const cx = (...c) => c.filter(Boolean).join(' ')

// Panel with a cursor-following spotlight.
export function Card({ as: As = 'div', spotlight = true, pad = false, className, children, onPointerMove, ...rest }) {
  const move = (e) => {
    const r = e.currentTarget.getBoundingClientRect()
    e.currentTarget.style.setProperty('--mx', `${e.clientX - r.left}px`)
    e.currentTarget.style.setProperty('--my', `${e.clientY - r.top}px`)
    onPointerMove?.(e)
  }
  return (
    <As className={cx('card', spotlight && 'spot', pad && 'card-pad', className)} onPointerMove={spotlight ? move : onPointerMove} {...rest}>
      {children}
    </As>
  )
}

export function CardHeader({ title, subtitle, actions, as: H = 'h2' }) {
  return (
    <div className="card-head">
      <div style={{ minWidth: 0 }}>
        <H>{title}</H>
        {subtitle && <p>{subtitle}</p>}
      </div>
      {actions && <div className="row">{actions}</div>}
    </div>
  )
}

export function Sparkline({ data, width = 96, height = 32, label }) {
  const id = useId().replace(/:/g, '')
  if (!data || data.length < 2) return null
  const max = Math.max(...data, 1)
  const min = Math.min(...data, 0)
  const span = max - min || 1
  const pts = data.map((v, i) => [(i / (data.length - 1)) * width, height - 3 - ((v - min) / span) * (height - 6)])
  const line = pts.map((p, i) => `${i ? 'L' : 'M'}${p[0].toFixed(1)},${p[1].toFixed(1)}`).join(' ')
  return (
    <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`} role="img" aria-label={label}>
      <defs>
        <linearGradient id={`sg${id}`} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="var(--accent)" stopOpacity="0.35" />
          <stop offset="1" stopColor="var(--accent)" stopOpacity="0" />
        </linearGradient>
      </defs>
      <path d={`${line} L${width},${height} L0,${height} Z`} fill={`url(#sg${id})`} />
      <path d={line} fill="none" stroke="var(--accent)" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}

export function StatCard({ label, value, format, icon: Icon, tone, delta, deltaTone, spark, sparkLabel, loading }) {
  return (
    <Card className="stat">
      <div className="stat-top">
        <span className="stat-label">{label}</span>
        {Icon && (
          <span className={cx('stat-icon', tone && `tone-${tone}`)}>
            <Icon size={16} aria-hidden="true" />
          </span>
        )}
      </div>
      <div className={cx('stat-value', typeof value === 'string' && 'is-text')}>
        {loading ? <Skeleton width={80} height={30} /> : typeof value === 'number' ? <CountUp value={value} format={format} /> : value ?? '-'}
      </div>
      <div className="stat-foot">
        {delta ? <span className={cx('delta', deltaTone)}>{delta}</span> : <span />}
        {spark && <Sparkline data={spark} label={sparkLabel || `${label} trend`} />}
      </div>
    </Card>
  )
}

export function Badge({ tone = 'neutral', dot = false, children, className }) {
  return (
    <span className={cx('badge', tone !== 'neutral' && `badge-${tone}`, className)}>
      {dot && <span className="dot" aria-hidden="true" />}
      {children}
    </span>
  )
}

export function KeyValueList({ items }) {
  return (
    <dl className="kv">
      {items.filter(Boolean).map(([k, v]) => (
        <div key={k} style={{ display: 'contents' }}>
          <dt>{k}</dt>
          <dd>{v}</dd>
        </div>
      ))}
    </dl>
  )
}

export function Timeline({ items }) {
  return (
    <ol className="timeline">
      {items.map((it, i) => (
        <li key={it.key ?? i}>
          <span className={cx('timeline-dot', it.tone && `tone-${it.tone}`)} aria-hidden="true" />
          <div className="timeline-title">{it.title}</div>
          {it.meta && <div className="timeline-meta">{it.meta}</div>}
          {it.body && <div className="timeline-body">{it.body}</div>}
        </li>
      ))}
    </ol>
  )
}

/**
 * Sortable, paginated table. Columns: { key, label, num, sortable, render(row), sortValue(row), hideSm }.
 * Below 640px rows collapse into cards when `cards` is true.
 */
export function Table({
  columns,
  rows,
  rowKey,
  pageSize = 10,
  initialSort,
  loading,
  empty,
  onRowClick,
  rowClassName,
  caption,
  cards = true,
}) {
  const [sort, setSort] = useState(initialSort || null)
  const [page, setPage] = useState(0)

  const sorted = useMemo(() => {
    if (!rows || !sort) return rows || []
    const col = columns.find((c) => c.key === sort.key)
    const val = col?.sortValue || ((r) => r[sort.key])
    return [...rows].sort((a, b) => {
      const x = val(a)
      const y = val(b)
      if (x === y) return 0
      if (x === null || x === undefined) return 1
      if (y === null || y === undefined) return -1
      return (x > y ? 1 : -1) * (sort.dir === 'asc' ? 1 : -1)
    })
  }, [rows, sort, columns])

  const pages = Math.max(1, Math.ceil(sorted.length / pageSize))
  const current = Math.min(page, pages - 1)
  const slice = sorted.slice(current * pageSize, current * pageSize + pageSize)

  const toggle = (key) => {
    setPage(0)
    setSort((s) => (s?.key === key ? { key, dir: s.dir === 'asc' ? 'desc' : 'asc' } : { key, dir: 'desc' }))
  }

  if (loading) {
    return (
      <div className="card-body" aria-busy="true" aria-label="Loading">
        {Array.from({ length: 5 }).map((_, i) => (
          <Skeleton key={i} height={22} style={{ margin: '12px 0' }} />
        ))}
      </div>
    )
  }
  if (!rows || rows.length === 0) return empty || <EmptyState title="Nothing here yet" />

  const clickable = (r) =>
    onRowClick
      ? {
          className: cx('clickable', rowClassName?.(r)),
          onClick: () => onRowClick(r),
          onKeyDown: (e) => {
            if (e.key === 'Enter' && e.target === e.currentTarget) onRowClick(r)
          },
          tabIndex: 0,
        }
      : { className: rowClassName?.(r) }

  return (
    <>
      <div className={cx('table-wrap', cards && 'as-cards')}>
        <table className="table">
          {caption && <caption className="sr-only">{caption}</caption>}
          <thead>
            <tr>
              {columns.map((c) => {
                const active = sort?.key === c.key
                const Icon = active ? (sort.dir === 'asc' ? ArrowUp : ArrowDown) : ArrowUpDown
                return (
                  <th
                    key={c.key}
                    className={cx(c.num && 'num', c.hideSm && 'hide-sm')}
                    aria-sort={active ? (sort.dir === 'asc' ? 'ascending' : 'descending') : undefined}
                    scope="col"
                  >
                    {c.sortable === false || !c.label ? (
                      c.label || <span className="sr-only">Actions</span>
                    ) : (
                      <button onClick={() => toggle(c.key)}>
                        {c.label}
                        <Icon size={12} aria-hidden="true" style={{ opacity: active ? 1 : 0.45 }} />
                      </button>
                    )}
                  </th>
                )
              })}
            </tr>
          </thead>
          <tbody>
            {slice.map((r) => (
              <tr key={rowKey(r)} {...clickable(r)}>
                {columns.map((c) => (
                  <td key={c.key} className={cx(c.num && 'num', c.className, c.hideSm && 'hide-sm')}>
                    {c.render ? c.render(r) : r[c.key]}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
        {cards && (
          <div className="table-cards">
            {slice.map((r) => (
              <div key={rowKey(r)} {...clickable(r)} className={cx('table-card', clickable(r).className)} role={onRowClick ? 'button' : undefined}>
                {columns.map((c) => (
                  <div key={c.key} className="table-card-row">
                    <span>{c.label}</span>
                    <span className={c.className === 'url-cell' ? 'mono break' : undefined}>{c.render ? c.render(r) : r[c.key]}</span>
                  </div>
                ))}
              </div>
            ))}
          </div>
        )}
      </div>
      {sorted.length > pageSize && (
        <div className="table-foot">
          <span>
            {current * pageSize + 1}-{Math.min(sorted.length, (current + 1) * pageSize)} of {sorted.length}
          </span>
          <div className="row">
            <Button size="sm" variant="ghost" icon={ChevronLeft} disabled={current === 0} onClick={() => setPage(current - 1)}>
              Prev
            </Button>
            <span>
              Page {current + 1} / {pages}
            </span>
            <Button size="sm" variant="ghost" iconRight={ChevronRight} disabled={current >= pages - 1} onClick={() => setPage(current + 1)}>
              Next
            </Button>
          </div>
        </div>
      )}
    </>
  )
}
