import { ArrowDown, ArrowUp, ChevronLeft, ChevronRight, ChevronsUpDown } from 'lucide-react'
import { useMemo, useState } from 'react'
import { Skeleton } from './feedback'

/**
 * columns: [{ key, label, align, sortable, sortValue(row), render(row), className, headClass }]
 * Sorting: controlled when `onSort` is given (server-side), otherwise client-side via sortValue.
 * Paging: controlled when `onPage` is given (page, total, pageSize), otherwise client-side when `pageSize` is set.
 * `cards(row)` renders each row as a card below 640px instead of a scrolling table.
 */
export default function Table({
  columns, rows, rowKey, sort, onSort, initialSort, page, pageSize, total, onPage, loading = false,
  empty, cards, caption, dense = false, footer,
}) {
  const [localSort, setLocalSort] = useState(initialSort || null)
  const [localPage, setLocalPage] = useState(0)
  const activeSort = onSort ? sort : localSort

  const sorted = useMemo(() => {
    if (onSort || !localSort || !rows) return rows || []
    const col = columns.find((c) => c.key === localSort.key)
    if (!col) return rows
    const get = col.sortValue || ((r) => r[col.key])
    const dir = localSort.dir === 'asc' ? 1 : -1
    return [...rows].sort((a, b) => {
      const x = get(a), y = get(b)
      return (x > y ? 1 : x < y ? -1 : 0) * dir
    })
  }, [rows, localSort, columns, onSort])

  const serverPaged = !!onPage
  const pg = serverPaged ? page : localPage
  const size = pageSize || sorted.length || 1
  const count = serverPaged ? total : sorted.length
  const visible = serverPaged || !pageSize ? sorted : sorted.slice(pg * size, pg * size + size)
  const pages = Math.max(1, Math.ceil(count / size))
  const goto = (p) => (serverPaged ? onPage(p) : setLocalPage(p))

  function toggle(col) {
    if (!col.sortable) return
    if (onSort) return onSort(col.key)
    setLocalPage(0)
    setLocalSort((s) => (s?.key === col.key ? { key: col.key, dir: s.dir === 'asc' ? 'desc' : 'asc' } : { key: col.key, dir: col.defaultDir || 'desc' }))
  }

  const pad = dense ? 'py-1.5' : 'py-2.5'
  const align = (a) => (a === 'right' ? 'text-right' : a === 'center' ? 'text-center' : 'text-left')
  const showSkeleton = loading && !rows

  return (
    <div className="min-w-0">
      {showSkeleton ? (
        <div className="space-y-2 py-1">{Array.from({ length: 6 }, (_, i) => <Skeleton key={i} className="h-9 w-full" />)}</div>
      ) : visible.length === 0 ? (
        empty
      ) : (
        <>
          <div className={`${cards ? 'hidden sm:block' : ''} -mx-4 overflow-x-auto px-4 ${loading ? 'opacity-50 transition-opacity' : ''}`}>
            <table className="w-full border-collapse text-sm">
              {caption && <caption className="sr-only">{caption}</caption>}
              <thead>
                <tr className="border-b border-line-strong">
                  {columns.map((c) => {
                    const on = activeSort?.key === c.key
                    const Icon = on ? (activeSort.dir === 'asc' ? ArrowUp : ArrowDown) : ChevronsUpDown
                    return (
                      <th key={c.key} scope="col" aria-sort={on ? (activeSort.dir === 'asc' ? 'ascending' : 'descending') : undefined}
                        className={`whitespace-nowrap py-2 pr-3 font-mono text-[10px] font-medium uppercase tracking-[0.12em] text-dim last:pr-0 ${align(c.align)} ${c.headClass || ''}`}>
                        {c.sortable ? (
                          <button type="button" onClick={() => toggle(c)} className={`inline-flex items-center gap-1 uppercase hover:text-fg ${on ? 'text-ok' : ''}`}>
                            {c.label}<Icon size={11} aria-hidden="true" />
                          </button>
                        ) : c.label}
                      </th>
                    )
                  })}
                </tr>
              </thead>
              <tbody>
                {visible.map((r, i) => (
                  <tr key={rowKey ? rowKey(r) : i} className="border-b border-line transition-colors hover:bg-ok/[0.035]">
                    {columns.map((c) => (
                      <td key={c.key} className={`${pad} pr-3 align-middle last:pr-0 ${align(c.align)} ${c.className || ''}`}>
                        {c.render ? c.render(r) : r[c.key]}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {cards && <ul className={`space-y-2 sm:hidden ${loading ? 'opacity-50' : ''}`}>{visible.map((r, i) => <li key={rowKey ? rowKey(r) : i}>{cards(r)}</li>)}</ul>}
        </>
      )}
      {(footer || (pageSize && count > size)) && !showSkeleton && (
        <div className="mt-3 flex flex-wrap items-center justify-between gap-2 font-mono text-xs text-muted">
          <span>{footer ?? `${count.toLocaleString('en-US')} rows`}</span>
          {pages > 1 && (
            <nav className="flex items-center gap-2" aria-label="Pagination">
              <button type="button" disabled={pg === 0} onClick={() => goto(pg - 1)} aria-label="Previous page"
                className="rounded border border-line-strong p-1 hover:border-ok/60 hover:text-ok disabled:opacity-30"><ChevronLeft size={15} /></button>
              <span className="tabular-nums">{String(pg + 1).padStart(2, '0')} / {String(pages).padStart(2, '0')}</span>
              <button type="button" disabled={pg + 1 >= pages} onClick={() => goto(pg + 1)} aria-label="Next page"
                className="rounded border border-line-strong p-1 hover:border-ok/60 hover:text-ok disabled:opacity-30"><ChevronRight size={15} /></button>
            </nav>
          )}
        </div>
      )}
    </div>
  )
}
