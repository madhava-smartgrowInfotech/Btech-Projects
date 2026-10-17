import { useMemo, useState } from 'react'
import { ArrowDown, ArrowUp, ArrowUpDown, ChevronLeft, ChevronRight } from 'lucide-react'
import { Button } from './Button'
import { EmptyState } from './Feedback'

/**
 * Sortable, paginated table. Below 640px it renders as stacked cards.
 * columns: [{key, label, render?(row), sortValue?(row), numeric?, sortable?=true}]
 */
export function Table({ columns, rows, rowKey = (r, i) => r.id ?? i, pageSize = 10, initialSort, onRowClick, empty, caption }) {
  const [sort, setSort] = useState(initialSort || null) // {key, dir}
  const [page, setPage] = useState(0)

  const sorted = useMemo(() => {
    if (!sort) return rows
    const col = columns.find((c) => c.key === sort.key)
    if (!col) return rows
    const val = col.sortValue || ((r) => r[col.key])
    return [...rows].sort((a, b) => {
      const x = val(a)
      const y = val(b)
      if (x === y) return 0
      if (x === null || x === undefined || x === '') return 1
      if (y === null || y === undefined || y === '') return -1
      const r = typeof x === 'number' && typeof y === 'number' ? x - y : String(x).localeCompare(String(y), undefined, { numeric: true })
      return sort.dir === 'asc' ? r : -r
    })
  }, [rows, sort, columns])

  const pages = Math.max(1, Math.ceil(sorted.length / pageSize))
  const current = Math.min(page, pages - 1)
  const visible = sorted.slice(current * pageSize, current * pageSize + pageSize)

  if (!rows.length) return empty || <EmptyState title="Nothing here yet" />

  const toggle = (key) => {
    setPage(0)
    setSort((s) => (!s || s.key !== key ? { key, dir: 'asc' } : s.dir === 'asc' ? { key, dir: 'desc' } : null))
  }
  const cell = (c, r) => (c.render ? c.render(r) : r[c.key] ?? '—')
  const clickProps = (r) =>
    onRowClick
      ? {
          className: 'clickable',
          tabIndex: 0,
          onClick: () => onRowClick(r),
          onKeyDown: (e) => {
            if (e.key === 'Enter') onRowClick(r)
          },
        }
      : {}

  return (
    <div>
      <div className="table-wrap as-cards" data-lenis-prevent>
        <table className="table">
          {caption && <caption className="sr-only">{caption}</caption>}
          <thead>
            <tr>
              {columns.map((c) => {
                const active = sort?.key === c.key
                const Icon = !active ? ArrowUpDown : sort.dir === 'asc' ? ArrowUp : ArrowDown
                return (
                  <th
                    key={c.key}
                    scope="col"
                    className={c.numeric ? 'num' : undefined}
                    aria-sort={active ? (sort.dir === 'asc' ? 'ascending' : 'descending') : undefined}
                  >
                    {c.sortable === false ? (
                      c.label
                    ) : (
                      <button onClick={() => toggle(c.key)}>
                        {c.label}
                        <Icon size={13} aria-hidden="true" />
                      </button>
                    )}
                  </th>
                )
              })}
            </tr>
          </thead>
          <tbody>
            {visible.map((r, i) => (
              <tr key={rowKey(r, i)} {...clickProps(r)}>
                {columns.map((c) => (
                  <td key={c.key} className={c.numeric ? 'num' : undefined}>
                    {cell(c, r)}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="table-cards">
        {visible.map((r, i) => (
          <div key={rowKey(r, i)} {...clickProps(r)} className={`row-card ${onRowClick ? 'clickable' : ''}`} role={onRowClick ? 'button' : undefined}>
            <dl>
              {columns.map((c) => (
                <div key={c.key} style={{ display: 'contents' }}>
                  <dt>{c.label}</dt>
                  <dd>{cell(c, r)}</dd>
                </div>
              ))}
            </dl>
          </div>
        ))}
      </div>
      {pages > 1 && (
        <div className="table-foot">
          <span className="small mono">
            {current * pageSize + 1}–{Math.min(sorted.length, (current + 1) * pageSize)} of {sorted.length}
          </span>
          <div className="row">
            <Button size="sm" icon={ChevronLeft} disabled={current === 0} onClick={() => setPage(current - 1)} aria-label="Previous page">
              Prev
            </Button>
            <span className="small mono" aria-live="polite">
              {current + 1}/{pages}
            </span>
            <Button size="sm" iconRight={ChevronRight} disabled={current >= pages - 1} onClick={() => setPage(current + 1)} aria-label="Next page">
              Next
            </Button>
          </div>
        </div>
      )}
    </div>
  )
}
