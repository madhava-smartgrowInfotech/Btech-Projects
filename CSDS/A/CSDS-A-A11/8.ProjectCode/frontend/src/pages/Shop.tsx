import { useEffect, useMemo, useState, type FormEvent } from 'react'
import { Link, useParams, useSearchParams } from 'react-router-dom'
import { AnimatePresence, motion } from 'framer-motion'
import { ChevronLeft, ChevronRight, Search, SlidersHorizontal, X } from 'lucide-react'
import { ProductCard } from '@/components/product/ProductCard'
import { GridSkeleton } from '@/components/common/Skeletons'
import { EmptyState, ErrorState } from '@/components/common/States'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input, Select } from '@/components/ui/input'
import { Skeleton } from '@/components/ui/skeleton'
import { useCategories, useProducts } from '@/hooks/useQueries'
import { useTracking } from '@/hooks/useTracking'
import { useReveal } from '@/hooks/useReveal'
import { EASE_EXPO, cn, titleCase } from '@/lib/utils'

const SORTS = [
  { value: 'relevance', label: 'Most relevant' },
  { value: 'newest', label: 'Newest' },
  { value: 'price_asc', label: 'Price: low to high' },
  { value: 'price_desc', label: 'Price: high to low' },
  { value: 'rating', label: 'Top rated' },
  { value: 'trending', label: 'Trending' },
]

const PAGE_SIZE = 12

export default function Shop() {
  const { category: routeCategory } = useParams<{ category?: string }>()
  const [params, setParams] = useSearchParams()
  const { track } = useTracking()

  const q = params.get('q') ?? ''
  const sort = params.get('sort') ?? 'relevance'
  const page = Number(params.get('page') ?? '1') || 1
  const category = routeCategory ?? params.get('category') ?? ''

  const [searchDraft, setSearchDraft] = useState(q)
  useEffect(() => setSearchDraft(q), [q])

  const { data: categories } = useCategories()
  const query = useProducts({
    category: category || undefined,
    q: q || undefined,
    sort,
    page,
    page_size: PAGE_SIZE,
  })

  const items = query.data?.items ?? []
  const total = query.data?.total ?? 0
  const pageCount = Math.max(1, Math.ceil(total / (query.data?.page_size ?? PAGE_SIZE)))
  const gridRef = useReveal<HTMLDivElement>({ stagger: 0.045, y: 18, enabled: items.length > 0 })

  const heading = useMemo(() => {
    if (q) return `Results for “${q}”`
    if (category) {
      const match = categories?.find((c) => c.slug === category)
      return match?.name ?? titleCase(category)
    }
    return 'The full collection'
  }, [categories, category, q])

  const update = (next: Record<string, string | undefined>) => {
    const merged = new URLSearchParams(params)
    Object.entries(next).forEach(([key, value]) => {
      if (!value) merged.delete(key)
      else merged.set(key, value)
    })
    if (!('page' in next)) merged.delete('page')
    setParams(merged, { replace: true })
  }

  const submitSearch = (event: FormEvent) => {
    event.preventDefault()
    const value = searchDraft.trim()
    if (value) track({ type: 'search', query: value })
    update({ q: value || undefined })
  }

  return (
    <div className="container pb-24 pt-14">
      {/* heading */}
      <div className="flex flex-col gap-5 border-b border-white/[0.07] pb-8">
        <nav className="flex items-center gap-2 text-[12px] text-ink-500">
          <Link to="/" className="transition-colors hover:text-ink-300">
            Home
          </Link>
          <span>/</span>
          <Link to="/shop" className="transition-colors hover:text-ink-300">
            Shop
          </Link>
          {category && (
            <>
              <span>/</span>
              <span className="text-ink-300">{titleCase(category)}</span>
            </>
          )}
        </nav>

        <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <h1 className="text-[34px] font-medium leading-[1.08] tracking-tighter text-ink-100 sm:text-[44px]">
              {heading}
            </h1>
            <div className="mt-2 text-[14px] text-ink-400">
              {query.isLoading ? (
                <Skeleton className="h-3.5 w-32" />
              ) : (
                <span>
                  {total} {total === 1 ? 'piece' : 'pieces'}
                  {category ? ` in ${titleCase(category)}` : ''}
                </span>
              )}
            </div>
          </div>

          <form onSubmit={submitSearch} className="relative w-full sm:w-[320px]">
            <Search className="pointer-events-none absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-ink-500" />
            <Input
              value={searchDraft}
              onChange={(e) => setSearchDraft(e.target.value)}
              placeholder="Search the catalog"
              className="pl-11 pr-10"
              aria-label="Search the catalog"
            />
            {searchDraft && (
              <button
                type="button"
                onClick={() => {
                  setSearchDraft('')
                  update({ q: undefined })
                }}
                className="absolute right-3.5 top-1/2 -translate-y-1/2 rounded-full p-1 text-ink-500 hover:text-ink-200"
                aria-label="Clear search"
              >
                <X className="h-3.5 w-3.5" />
              </button>
            )}
          </form>
        </div>
      </div>

      {/* filters */}
      <div className="sticky top-[68px] z-30 -mx-5 mb-10 mt-6 flex flex-col gap-4 bg-ink-950/85 px-5 py-4 backdrop-blur-xl lg:flex-row lg:items-center lg:justify-between">
        <div className="no-scrollbar flex items-center gap-2 overflow-x-auto">
          <Link to="/shop">
            <Badge
              variant={!category ? 'accent' : 'outline'}
              className="cursor-pointer whitespace-nowrap px-3 py-1.5 text-[12px] transition-colors hover:border-white/25"
            >
              All
            </Badge>
          </Link>
          {(categories ?? []).map((c) => (
            <Link key={String(c.id)} to={`/shop/${c.slug}`}>
              <Badge
                variant={category === c.slug ? 'accent' : 'outline'}
                className="cursor-pointer whitespace-nowrap px-3 py-1.5 text-[12px] transition-colors hover:border-white/25"
              >
                {c.name}
              </Badge>
            </Link>
          ))}
          {!categories && (
            <div className="flex gap-2">
              {Array.from({ length: 4 }).map((_, i) => (
                <Skeleton key={i} className="h-7 w-20 rounded-full" />
              ))}
            </div>
          )}
        </div>

        <div className="flex items-center gap-3">
          <SlidersHorizontal className="h-3.5 w-3.5 shrink-0 text-ink-500" />
          <Select
            value={sort}
            onChange={(e) => update({ sort: e.target.value })}
            aria-label="Sort products"
            className="h-10 w-[190px] text-[13px]"
          >
            {SORTS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </Select>
        </div>
      </div>

      {/* grid */}
      <AnimatePresence mode="wait">
        {query.isLoading ? (
          <motion.div key="loading" exit={{ opacity: 0 }}>
            <GridSkeleton count={8} />
          </motion.div>
        ) : query.isError ? (
          <motion.div key="error" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
            <ErrorState error={query.error} onRetry={() => void query.refetch()} />
          </motion.div>
        ) : items.length === 0 ? (
          <motion.div key="empty" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
            <EmptyState
              title="Nothing matches those filters"
              description="Try a broader search term or clear the category filter."
              action={
                <Button asChild variant="secondary" size="sm">
                  <Link to="/shop">Reset filters</Link>
                </Button>
              }
            />
          </motion.div>
        ) : (
          <motion.div
            key={`${category}-${q}-${sort}-${page}`}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.45, ease: EASE_EXPO }}
          >
            <div
              ref={gridRef}
              className={cn(
                'grid grid-cols-2 gap-5 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4',
                query.isFetching && 'opacity-70 transition-opacity',
              )}
            >
              {items.map((product) => (
                <div key={String(product.id)} data-reveal>
                  <ProductCard
                    product={product}
                    onOpen={() => track({ type: 'click', product })}
                  />
                </div>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* pagination */}
      {pageCount > 1 && !query.isError && (
        <div className="mt-14 flex items-center justify-center gap-2">
          <Button
            variant="secondary"
            size="sm"
            disabled={page <= 1}
            onClick={() => update({ page: String(page - 1) })}
          >
            <ChevronLeft className="h-3.5 w-3.5" />
            Previous
          </Button>

          <div className="mx-2 flex items-center gap-1">
            {Array.from({ length: pageCount })
              .slice(0, 7)
              .map((_, i) => {
                const target = i + 1
                return (
                  <button
                    key={target}
                    onClick={() => update({ page: String(target) })}
                    className={cn(
                      'h-9 w-9 rounded-full text-[13px] transition-colors duration-300 ease-expo',
                      target === page
                        ? 'bg-white/[0.09] text-ink-100'
                        : 'text-ink-500 hover:bg-white/[0.05] hover:text-ink-200',
                    )}
                  >
                    {target}
                  </button>
                )
              })}
            {pageCount > 7 && <span className="px-1 text-ink-600">…</span>}
          </div>

          <Button
            variant="secondary"
            size="sm"
            disabled={page >= pageCount}
            onClick={() => update({ page: String(page + 1) })}
          >
            Next
            <ChevronRight className="h-3.5 w-3.5" />
          </Button>
        </div>
      )}
    </div>
  )
}
