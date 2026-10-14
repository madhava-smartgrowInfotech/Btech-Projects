import { useMemo, useState } from 'react'
import { ArrowDown, ArrowUp, ChevronLeft, ChevronRight, ChevronsUpDown, Inbox } from 'lucide-react'
import { Button } from './Button'
import { SearchField } from './Form'
import { EmptyState } from './Feedback'

/**
 * columns: [{key, label, numeric, render(row), sortValue(row), sortable=true, wrap}]
 * Sortable, searchable (searchKeys), paginated (pageSize), with an empty state and mobile cards.
 */
export function Table({
  columns,
  rows = [],
  rowKey = (r, i) => i,
  pageSize = 10,
  searchKeys,
  searchPlaceholder = 'Search',
  initialSort,
  highlight,
  caption,
  tools,
  empty,
  cards = true,
  cardTitle,
  tall,
}) {
  const [q, setQ] = useState('')
  const [sort, setSort] = useState(initialSort || null)
  const [page, setPage] = useState(0)

  const filtered = useMemo(() => {
    if (!q || !searchKeys) return rows
    const s = q.toLowerCase()
    return rows.filter((r) => searchKeys.some((k) => String(typeof k === 'function' ? k(r) : r[k] ?? '').toLowerCase().includes(s)))
  }, [rows, q, searchKeys])

  const sorted = useMemo(() => {
    if (!sort) return filtered
    const col = columns.find((c) => c.key === sort.key)
    if (!col) return filtered
    const val = col.sortValue || ((r) => r[col.key])
    return [...filtered].sort((a, b) => {
      const x = val(a)
      const y = val(b)
      const cmp = typeof x === 'number' && typeof y === 'number' ? x - y : String(x).localeCompare(String(y), undefined, { numeric: true })
      return sort.dir === 'asc' ? cmp : -cmp
    })
  }, [filtered, sort, columns])

  const pages = pageSize ? Math.max(1, Math.ceil(sorted.length / pageSize)) : 1
  const cur = Math.min(page, pages - 1)
  const visible = pageSize ? sorted.slice(cur * pageSize, cur * pageSize + pageSize) : sorted

  const toggle = (key) => {
    setPage(0)
    setSort((s) => (s?.key === key ? (s.dir === 'desc' ? { key, dir: 'asc' } : null) : { key, dir: 'desc' }))
  }

  return (
    <div className={cards ? 'has-cards' : ''}>
      {(searchKeys || tools) && (
        <div className="table-tools">
          {searchKeys && (
            <SearchField
              value={q}
              onChange={(v) => {
                setQ(v)
                setPage(0)
              }}
              placeholder={searchPlaceholder}
            />
          )}
          {tools}
        </div>
      )}
      {sorted.length === 0 ? (
        empty || (
          <EmptyState
            icon={Inbox}
            title={q ? 'No matches' : 'Nothing here yet'}
            message={q ? `Nothing matches “${q}”.` : 'There are no rows to show.'}
            action={q ? <Button variant="secondary" onClick={() => setQ('')}>Clear search</Button> : null}
            compact
          />
        )
      ) : (
        <>
          <div className={`table-scroll ${tall ? 'tall' : ''}`} tabIndex={0} role="region" aria-label={caption || 'Table'}>
            <table className="tbl">
              {caption && <caption className="sr-only">{caption}</caption>}
              <thead>
                <tr>
                  {columns.map((c) => {
                    const active = sort?.key === c.key
                    const Icon = active ? (sort.dir === 'asc' ? ArrowUp : ArrowDown) : ChevronsUpDown
                    return (
                      <th
                        key={c.key}
                        className={c.numeric ? 'n' : ''}
                        aria-sort={active ? (sort.dir === 'asc' ? 'ascending' : 'descending') : undefined}
                        scope="col"
                      >
                        {c.sortable === false ? (
                          c.label
                        ) : (
                          <button type="button" className="sort-btn" onClick={() => toggle(c.key)}>
                            {c.label}
                            <Icon size={13} aria-hidden="true" style={{ opacity: active ? 1 : 0.45 }} />
                          </button>
                        )}
                      </th>
                    )
                  })}
                </tr>
              </thead>
              <tbody>
                {visible.map((r, i) => (
                  <tr key={rowKey(r, i)} className={highlight?.(r) ? 'highlight' : ''}>
                    {columns.map((c) => (
                      <td key={c.key} className={`${c.numeric ? 'n' : ''} ${c.wrap ? 'wrap' : ''}`}>
                        {c.render ? c.render(r) : r[c.key]}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {cards && (
            <div className="table-cards">
              {visible.map((r, i) => (
                <div key={rowKey(r, i)} className={`tcard ${highlight?.(r) ? 'highlight' : ''}`}>
                  <div className="tcard-title">{cardTitle ? cardTitle(r) : columns[0].render ? columns[0].render(r) : r[columns[0].key]}</div>
                  <dl className="kv">
                    {columns.slice(1).map((c) => (
                      <div key={c.key} style={{ display: 'contents' }}>
                        <dt>{c.label}</dt>
                        <dd>{c.render ? c.render(r) : r[c.key]}</dd>
                      </div>
                    ))}
                  </dl>
                </div>
              ))}
            </div>
          )}
          {pageSize > 0 && pages > 1 && (
            <div className="pager">
              <span className="num">
                {cur * pageSize + 1}–{Math.min(sorted.length, (cur + 1) * pageSize)} of {sorted.length}
              </span>
              <div className="row" style={{ '--gap': '8px' }}>
                <Button variant="secondary" size="sm" icon={ChevronLeft} disabled={cur === 0} onClick={() => setPage(cur - 1)} aria-label="Previous page">
                  Prev
                </Button>
                <span className="num">
                  Page {cur + 1} / {pages}
                </span>
                <Button variant="secondary" size="sm" iconRight={ChevronRight} disabled={cur >= pages - 1} onClick={() => setPage(cur + 1)} aria-label="Next page">
                  Next
                </Button>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  )
}
