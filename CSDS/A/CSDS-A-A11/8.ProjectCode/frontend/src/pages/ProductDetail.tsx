import { useEffect, useMemo, useState } from 'react'
import { Link, useParams, useSearchParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { motion } from 'framer-motion'
import { Check, Minus, Plus, ShieldCheck, Star, Truck, Undo2 } from 'lucide-react'
import { ProductArt } from '@/components/bits/ProductArt'
import { MagneticButton } from '@/components/bits/MagneticButton'
import { Reveal } from '@/components/bits/Reveal'
import { RecommendationRail } from '@/components/product/RecommendationRail'
import { ReviewList } from '@/components/product/ReviewList'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { toast } from '@/components/ui/toast'
import { Tooltip } from '@/components/ui/tooltip'
import { ErrorState } from '@/components/common/States'
import { api, queryKeys } from '@/lib/api'
import { useProduct } from '@/hooks/useQueries'
import { useTracking } from '@/hooks/useTracking'
import { useCart } from '@/store/cart'
import { EASE_EXPO, cn, formatPrice } from '@/lib/utils'
import type { Product } from '@/lib/types'

const GUARANTEES = [
  { icon: Truck, label: 'Carbon-neutral delivery', detail: '2–4 working days' },
  { icon: Undo2, label: '60-day returns', detail: 'No questions asked' },
  { icon: ShieldCheck, label: '10-year warranty', detail: 'Repairs, not replacements' },
]

function useResolvedProduct(slug?: string) {
  const direct = useProduct(slug)

  // Some catalogs key detail lookups by id — if the slug lookup misses, resolve
  // it through a search and retry with the matched record's id.
  const fallbackNeeded = direct.isError && Boolean(slug)
  const lookup = useQuery({
    queryKey: ['product-by-slug', slug],
    queryFn: () => api.products({ q: slug, page: 1, page_size: 24 }),
    enabled: fallbackNeeded,
  })

  const matched = useMemo(() => {
    if (!fallbackNeeded || !lookup.data) return undefined
    return (
      lookup.data.items.find((p) => p.slug === slug) ?? lookup.data.items[0] ?? undefined
    )
  }, [fallbackNeeded, lookup.data, slug])

  const byId = useQuery({
    queryKey: queryKeys.product(matched?.id ?? ''),
    queryFn: () => api.product(matched!.id),
    enabled: Boolean(matched?.id),
  })

  const product: Product | undefined = direct.data ?? byId.data ?? matched
  const isLoading = direct.isLoading || (fallbackNeeded && (lookup.isLoading || byId.isLoading))
  const isError = Boolean(direct.isError && !product && !lookup.isLoading && !byId.isLoading)

  return {
    product,
    isLoading,
    isError,
    error: direct.error,
    refetch: () => {
      void direct.refetch()
      if (fallbackNeeded) void lookup.refetch()
    },
  }
}

function Gallery({ product }: { product: Product }) {
  const [active, setActive] = useState(0)
  const seeds = useMemo(
    () => [0, 1, 2, 3].map((i) => `${product.image_seed ?? product.slug}-${i}`),
    [product.image_seed, product.slug],
  )

  return (
    <div className="grid gap-4 sm:grid-cols-[84px_1fr]">
      <div className="order-2 flex gap-3 sm:order-1 sm:flex-col">
        {seeds.map((seed, i) => (
          <button
            key={seed}
            onClick={() => setActive(i)}
            className={cn(
              'overflow-hidden rounded-xl border transition-all duration-400 ease-expo',
              active === i
                ? 'border-amber-400/60 opacity-100'
                : 'border-white/[0.07] opacity-55 hover:opacity-90',
            )}
            aria-label={`View angle ${i + 1}`}
          >
            <ProductArt seed={seed} name={product.name} className="h-[72px] w-[72px]" />
          </button>
        ))}
      </div>

      <motion.div
        key={active}
        initial={{ opacity: 0, scale: 1.015 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.6, ease: EASE_EXPO }}
        className="order-1 overflow-hidden rounded-3xl border border-white/[0.07] sm:order-2"
      >
        <ProductArt
          detail
          seed={seeds[active]}
          name={product.name}
          className="aspect-[4/5] w-full sm:aspect-[5/5]"
        />
      </motion.div>
    </div>
  )
}

function RateWidget({ product }: { product: Product }) {
  const { track } = useTracking()
  const [value, setValue] = useState(0)
  const [hover, setHover] = useState(0)
  const [sent, setSent] = useState(false)

  return (
    <div className="panel flex flex-wrap items-center justify-between gap-4 p-5">
      <div>
        <p className="text-[13px] font-medium text-ink-100">
          {sent ? 'Thanks — noted' : 'Own this piece?'}
        </p>
        <p className="mt-1 text-[12px] text-ink-500">
          {sent
            ? 'Your rating feeds the ranking signals for this item.'
            : 'Rate it and the agents factor it into future ranking.'}
        </p>
      </div>
      <div className="flex items-center gap-1" onMouseLeave={() => setHover(0)}>
        {[1, 2, 3, 4, 5].map((star) => (
          <button
            key={star}
            onMouseEnter={() => setHover(star)}
            onClick={() => {
              setValue(star)
              setSent(true)
              track({ type: 'rating', product, value: star })
              toast({ title: `Rated ${star} / 5`, tone: 'success' })
            }}
            aria-label={`Rate ${star} out of 5`}
            className="p-1"
          >
            <Star
              className={cn(
                'h-5 w-5 transition-all duration-300 ease-expo',
                (hover || value) >= star
                  ? 'scale-110 fill-amber-400 text-amber-400'
                  : 'text-ink-600',
              )}
            />
          </button>
        ))}
      </div>
    </div>
  )
}

export default function ProductDetail() {
  const { slug } = useParams<{ slug: string }>()
  const [params] = useSearchParams()
  const recId = params.get('rec') ?? undefined
  const { product, isLoading, isError, error, refetch } = useResolvedProduct(slug)
  const { track, signal } = useTracking()
  const add = useCart((s) => s.add)
  const [qty, setQty] = useState(1)
  const [added, setAdded] = useState(false)

  // Product view is the primary implicit signal the agents learn from.
  useEffect(() => {
    if (!product) return
    track({ type: 'view', product, recId })
    setQty(1)
    setAdded(false)
  }, [product, recId, track])

  if (isLoading) {
    return (
      <div className="container grid gap-12 py-14 lg:grid-cols-2">
        <Skeleton className="aspect-[4/5] w-full rounded-3xl" />
        <div className="space-y-5">
          <Skeleton className="h-3 w-24" />
          <Skeleton className="h-10 w-3/4" />
          <Skeleton className="h-4 w-1/3" />
          <Skeleton className="h-24 w-full rounded-xl" />
          <Skeleton className="h-12 w-52 rounded-full" />
        </div>
      </div>
    )
  }

  if (isError || !product) {
    return (
      <div className="container py-24">
        <ErrorState
          error={error}
          onRetry={refetch}
          title="This piece could not be loaded"
          className="mx-auto max-w-xl"
        />
        <div className="mt-6 text-center">
          <Button asChild variant="secondary" size="sm">
            <Link to="/shop">Back to the collection</Link>
          </Button>
        </div>
      </div>
    )
  }

  const outOfStock = typeof product.stock === 'number' && product.stock <= 0
  const discounted =
    typeof product.compare_at_price === 'number' && product.compare_at_price > product.price

  const handleAdd = () => {
    add(product, { qty, recId })
    setAdded(true)
    window.setTimeout(() => setAdded(false), 2200)
    void signal({
      action: 'add_to_cart',
      recId,
      product,
      surface: 'product-detail',
      value: product.price * qty,
    })
    toast({
      title: `${product.name} added`,
      description: `${qty} × ${formatPrice(product.price, product.currency)} — in your bag.`,
      tone: 'success',
    })
  }

  return (
    <>
      <div className="container pt-14">
        <nav className="flex items-center gap-2 text-[12px] text-ink-500">
          <Link to="/" className="hover:text-ink-300">
            Home
          </Link>
          <span>/</span>
          <Link to="/shop" className="hover:text-ink-300">
            Shop
          </Link>
          <span>/</span>
          <Link to={`/shop/${product.category}`} className="capitalize hover:text-ink-300">
            {product.category}
          </Link>
        </nav>

        <div className="mt-8 grid gap-12 lg:grid-cols-[minmax(0,1fr)_minmax(0,480px)] lg:gap-16">
          <Gallery product={product} />

          <div>
            <div className="flex flex-wrap items-center gap-2">
              <Badge variant="outline" className="capitalize">
                {product.category}
              </Badge>
              {product.subcategory && (
                <Badge variant="outline" className="capitalize">
                  {product.subcategory}
                </Badge>
              )}
              {recId && (
                <Badge variant="accent">Recommended for your profile</Badge>
              )}
            </div>

            <h1 className="mt-5 text-[34px] font-medium leading-[1.06] tracking-tighter text-ink-100 sm:text-[42px]">
              {product.name}
            </h1>

            <div className="mt-4 flex flex-wrap items-center gap-4">
              <p className="text-[24px] font-medium text-ink-100">
                {formatPrice(product.price, product.currency)}
              </p>
              {discounted && (
                <p className="text-[15px] text-ink-600 line-through">
                  {formatPrice(product.compare_at_price ?? 0, product.currency)}
                </p>
              )}
              {typeof product.rating === 'number' && (
                <span className="inline-flex items-center gap-1.5 text-[13px] text-ink-400">
                  <Star className="h-3.5 w-3.5 fill-amber-400 text-amber-400" />
                  {product.rating.toFixed(1)}
                  {product.review_count ? <span>· {product.review_count} reviews</span> : null}
                </span>
              )}
            </div>

            <p className="mt-6 text-[15px] leading-relaxed text-ink-400">
              {product.description ?? product.short_description}
            </p>

            {product.colorway && (
              <div className="mt-8">
                <p className="eyebrow mb-3">Colourway</p>
                <span className="inline-flex items-center gap-2.5 rounded-full border border-white/[0.09] bg-white/[0.03] px-3 py-2 text-[13px] text-ink-200">
                  <span
                    className="h-4 w-4 rounded-full border border-white/20"
                    style={{
                      background: `linear-gradient(135deg, hsl(${(product.colorway.length * 27) % 360} 40% 60%), hsl(${(product.colorway.length * 27 + 60) % 360} 35% 30%))`,
                    }}
                  />
                  {product.colorway}
                </span>
              </div>
            )}

            {/* quantity + add */}
            <div className="mt-8 flex flex-wrap items-center gap-3">
              <div className="flex h-12 items-center rounded-full border border-white/[0.09] bg-white/[0.02]">
                <button
                  onClick={() => setQty((q) => Math.max(1, q - 1))}
                  className="grid h-12 w-12 place-items-center rounded-l-full text-ink-400 transition-colors hover:text-ink-100"
                  aria-label="Decrease quantity"
                >
                  <Minus className="h-3.5 w-3.5" />
                </button>
                <span className="num w-8 text-center text-[14px] text-ink-100">{qty}</span>
                <button
                  onClick={() => setQty((q) => Math.min(9, q + 1))}
                  className="grid h-12 w-12 place-items-center rounded-r-full text-ink-400 transition-colors hover:text-ink-100"
                  aria-label="Increase quantity"
                >
                  <Plus className="h-3.5 w-3.5" />
                </button>
              </div>

              <MagneticButton strength={0.22}>
                <Button size="lg" onClick={handleAdd} disabled={outOfStock} className="min-w-[200px]">
                  {added ? (
                    <>
                      <Check className="h-4 w-4" />
                      Added to bag
                    </>
                  ) : outOfStock ? (
                    'Out of stock'
                  ) : (
                    `Add to bag · ${formatPrice(product.price * qty, product.currency)}`
                  )}
                </Button>
              </MagneticButton>
            </div>

            {typeof product.stock === 'number' && product.stock > 0 && product.stock <= 8 && (
              <p className="mt-3 text-[12px] text-amber-300/85">
                Only {product.stock} left in this colourway.
              </p>
            )}

            {/* guarantees */}
            <div className="mt-10 grid gap-3 sm:grid-cols-3">
              {GUARANTEES.map((item) => (
                <div key={item.label} className="panel-inset p-3.5">
                  <item.icon className="h-4 w-4 text-ink-400" />
                  <p className="mt-2.5 text-[12.5px] font-medium text-ink-200">{item.label}</p>
                  <p className="mt-0.5 text-[11px] text-ink-500">{item.detail}</p>
                </div>
              ))}
            </div>

            {/* attributes */}
            {product.attributes && Object.keys(product.attributes).length > 0 && (
              <div className="mt-10">
                <p className="eyebrow mb-4">Specification</p>
                <dl className="divide-y divide-white/[0.06] border-y border-white/[0.06]">
                  {Object.entries(product.attributes).map(([key, value]) => (
                    <div key={key} className="flex items-center justify-between gap-6 py-3">
                      <dt className="text-[13px] capitalize text-ink-500">
                        {key.replace(/_/g, ' ')}
                      </dt>
                      <dd className="text-right text-[13px] text-ink-200">{String(value)}</dd>
                    </div>
                  ))}
                </dl>
              </div>
            )}

            {product.tags && product.tags.length > 0 && (
              <div className="mt-8 flex flex-wrap gap-2">
                {product.tags.map((tag) => (
                  <Tooltip key={tag} content="Tags feed the content-similarity agent">
                    <Badge variant="default">{tag}</Badge>
                  </Tooltip>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      <RecommendationRail
        context="product"
        productId={product.id}
        surface="product-similar"
        eyebrow="Similar because"
        title="Pairs with what you're looking at"
        description="Each card carries the reasoning that put it here — open “Why this?” to see the agent contributions behind the score."
        showStrategy
        limit={8}
      />

      <section className="container py-16 sm:py-20">
        <Reveal>
          <div className="grid gap-10 lg:grid-cols-[320px_1fr]">
            <div>
              <p className="eyebrow">Reviews</p>
              <h2 className="mt-3 text-[28px] font-medium leading-[1.1] tracking-tighter text-ink-100">
                How it holds up
              </h2>
              <p className="mt-3 text-[14px] leading-relaxed text-ink-400">
                Verified owners only. Ratings and reviews are behavioural signals — they change
                what the agents surface next.
              </p>
              <div className="mt-6">
                <RateWidget product={product} />
              </div>
            </div>
            <ReviewList productId={product.id} />
          </div>
        </Reveal>
      </section>
    </>
  )
}
