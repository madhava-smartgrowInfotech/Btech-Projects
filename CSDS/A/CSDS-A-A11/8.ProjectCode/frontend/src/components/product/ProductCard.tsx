import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Sparkles, Star } from 'lucide-react'
import { ProductArt } from '@/components/bits/ProductArt'
import { SpotlightCard } from '@/components/bits/SpotlightCard'
import { Badge } from '@/components/ui/badge'
import { EASE_EXPO, cn, formatPrice } from '@/lib/utils'
import type { Product } from '@/lib/types'

type Props = {
  product: Product
  /** Present when the card came from a recommendation impression. */
  recId?: string
  reason?: string
  confidence?: number
  onOpen?: () => void
  onWhy?: () => void
  className?: string
  compact?: boolean
}

export function ProductCard({
  product,
  recId,
  reason,
  confidence,
  onOpen,
  onWhy,
  className,
  compact = false,
}: Props) {
  const discounted =
    typeof product.compare_at_price === 'number' && product.compare_at_price > product.price

  return (
    <motion.article
      whileHover={{ y: -4 }}
      transition={{ duration: 0.5, ease: EASE_EXPO }}
      className={cn('group relative', className)}
    >
      <SpotlightCard className="h-full">
        <Link
          to={recId ? `/product/${product.slug}?rec=${encodeURIComponent(recId)}` : `/product/${product.slug}`}
          onClick={onOpen}
          className="block focus-visible:outline-none"
        >
          <div className="relative overflow-hidden">
            <ProductArt
              seed={product.image_seed ?? product.slug}
              name={product.name}
              className={cn(
                'w-full transition-transform duration-[900ms] ease-expo group-hover:scale-[1.04]',
                compact ? 'aspect-[5/4]' : 'aspect-[4/5]',
              )}
            />
            <div className="pointer-events-none absolute inset-x-0 top-0 flex items-start justify-between p-3">
              {discounted ? (
                <Badge variant="accent">
                  −
                  {Math.round(
                    (1 - product.price / (product.compare_at_price as number)) * 100,
                  )}
                  %
                </Badge>
              ) : (
                <span />
              )}
              {typeof product.stock === 'number' && product.stock <= 5 && product.stock > 0 && (
                <Badge variant="warning">Low stock</Badge>
              )}
            </div>
            {recId && (
              <div className="pointer-events-none absolute inset-x-0 bottom-0 bg-gradient-to-t from-ink-950/85 to-transparent p-3 pt-10">
                <span className="inline-flex items-center gap-1.5 rounded-full border border-amber-400/25 bg-ink-950/70 px-2.5 py-1 text-[10.5px] font-medium text-amber-200 backdrop-blur-sm">
                  <Sparkles className="h-3 w-3" />
                  Picked for you
                  {typeof confidence === 'number' && (
                    <span className="text-amber-300/70">
                      {Math.round((confidence <= 1 ? confidence * 100 : confidence))}%
                    </span>
                  )}
                </span>
              </div>
            )}
          </div>

          <div className="space-y-1.5 p-4">
            <div className="flex items-start justify-between gap-3">
              <h3 className="text-[14.5px] font-medium leading-snug tracking-tight text-ink-100">
                {product.name}
              </h3>
              <div className="shrink-0 text-right">
                <p className="text-[14px] font-medium text-ink-100">
                  {formatPrice(product.price, product.currency)}
                </p>
                {discounted && (
                  <p className="text-[11.5px] text-ink-600 line-through">
                    {formatPrice(product.compare_at_price ?? 0, product.currency)}
                  </p>
                )}
              </div>
            </div>

            <div className="flex items-center gap-2 text-[12px] text-ink-500">
              <span className="capitalize">{product.colorway ?? product.category}</span>
              {typeof product.rating === 'number' && (
                <>
                  <span className="h-0.5 w-0.5 rounded-full bg-ink-600" />
                  <span className="inline-flex items-center gap-1">
                    <Star className="h-3 w-3 fill-amber-400/80 text-amber-400/80" />
                    {product.rating.toFixed(1)}
                    {product.review_count ? (
                      <span className="text-ink-600">({product.review_count})</span>
                    ) : null}
                  </span>
                </>
              )}
            </div>

            {reason && (
              <p className="line-clamp-2 pt-1 text-[12px] leading-relaxed text-ink-400">{reason}</p>
            )}
          </div>
        </Link>

        {recId && onWhy && (
          <div className="px-4 pb-4">
            <button
              type="button"
              onClick={(e) => {
                e.preventDefault()
                e.stopPropagation()
                onWhy()
              }}
              className="inline-flex items-center gap-1.5 rounded-full border border-white/[0.09] bg-white/[0.02] px-3 py-1.5 text-[11.5px] font-medium text-ink-300 transition-colors duration-300 ease-expo hover:border-amber-400/35 hover:text-amber-200"
            >
              <Sparkles className="h-3 w-3" />
              Why this?
            </button>
          </div>
        )}
      </SpotlightCard>
    </motion.article>
  )
}
