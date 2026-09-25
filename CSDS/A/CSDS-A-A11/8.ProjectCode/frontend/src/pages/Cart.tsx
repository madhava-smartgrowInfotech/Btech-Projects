import { useState } from 'react'
import { Link } from 'react-router-dom'
import { AnimatePresence, motion } from 'framer-motion'
import { ArrowRight, Check, Minus, Plus, ShoppingBag, Trash2 } from 'lucide-react'
import { ProductArt } from '@/components/bits/ProductArt'
import { RecommendationRail } from '@/components/product/RecommendationRail'
import { AnimatedNumber } from '@/components/bits/AnimatedNumber'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { toast } from '@/components/ui/toast'
import { EmptyState } from '@/components/common/States'
import { cartSubtotal, useCart } from '@/store/cart'
import { useTracking } from '@/hooks/useTracking'
import { EASE_EXPO, formatPrice } from '@/lib/utils'

const SHIPPING_THRESHOLD = 150

export default function Cart() {
  const lines = useCart((s) => s.lines)
  const setQty = useCart((s) => s.setQty)
  const remove = useCart((s) => s.remove)
  const clear = useCart((s) => s.clear)
  const { track, signal } = useTracking()
  const [placed, setPlaced] = useState(false)

  const subtotal = cartSubtotal(lines)
  const shipping = subtotal >= SHIPPING_THRESHOLD || subtotal === 0 ? 0 : 12
  const total = subtotal + shipping
  const currency = lines[0]?.currency ?? 'USD'

  const checkout = async () => {
    if (lines.length === 0) return

    // One purchase event per line; recommended lines additionally reinforce the loop.
    await Promise.all(
      lines.map((line) =>
        line.recId
          ? signal({
              action: 'purchase',
              recId: line.recId,
              product: {
                id: line.productId,
                slug: line.slug,
                name: line.name,
                category: line.category ?? '',
                price: line.price,
                currency: line.currency,
              },
              surface: 'cart-checkout',
              value: line.price * line.qty,
            })
          : Promise.resolve(
              track({
                type: 'purchase',
                productId: line.productId,
                value: line.price * line.qty,
              }),
            ),
      ),
    )

    setPlaced(true)
    clear()
    toast({
      title: 'Order confirmed',
      description: 'Purchase signals were sent to the learning loop.',
      tone: 'success',
    })
  }

  if (placed) {
    return (
      <div className="container flex min-h-[60vh] flex-col items-center justify-center py-24 text-center">
        <motion.span
          initial={{ scale: 0.7, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ duration: 0.6, ease: EASE_EXPO }}
          className="grid h-14 w-14 place-items-center rounded-full border border-teal-400/30 bg-teal-400/10 text-teal-400"
        >
          <Check className="h-6 w-6" />
        </motion.span>
        <h1 className="mt-6 text-[32px] font-medium tracking-tighter text-ink-100">
          Order confirmed
        </h1>
        <p className="mt-3 max-w-md text-[14.5px] leading-relaxed text-ink-400">
          A confirmation is on its way. Every purchased recommendation just reinforced the agent
          weights — you can watch the shift in the learning panel.
        </p>
        <div className="mt-8 flex flex-wrap justify-center gap-3">
          <Button asChild>
            <Link to="/shop">Keep browsing</Link>
          </Button>
          <Button asChild variant="outline">
            <Link to="/intelligence">See the learning panel</Link>
          </Button>
        </div>
      </div>
    )
  }

  return (
    <>
      <div className="container pt-14">
        <h1 className="text-[34px] font-medium leading-tight tracking-tighter text-ink-100 sm:text-[42px]">
          Your bag
        </h1>
        <p className="mt-2 text-[14px] text-ink-400">
          {lines.length === 0
            ? 'Nothing here yet.'
            : `${lines.length} ${lines.length === 1 ? 'line' : 'lines'} · ${formatPrice(subtotal, currency)}`}
        </p>

        {lines.length === 0 ? (
          <div className="mt-10">
            <EmptyState
              title="Your bag is empty"
              description="Add a piece and the complementary rail below will fill with items the agents think finish the set."
              icon={<ShoppingBag className="h-4 w-4" />}
              action={
                <Button asChild size="sm">
                  <Link to="/shop">
                    Browse the collection
                    <ArrowRight className="h-3.5 w-3.5" />
                  </Link>
                </Button>
              }
            />
          </div>
        ) : (
          <div className="mt-10 grid gap-10 lg:grid-cols-[1fr_360px]">
            <ul className="divide-y divide-white/[0.06] border-y border-white/[0.06]">
              <AnimatePresence initial={false}>
                {lines.map((line) => (
                  <motion.li
                    key={line.productId}
                    layout
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                    exit={{ opacity: 0, height: 0 }}
                    transition={{ duration: 0.4, ease: EASE_EXPO }}
                    className="overflow-hidden"
                  >
                    <div className="flex gap-4 py-5">
                      <Link to={`/product/${line.slug}`} className="shrink-0">
                        <ProductArt
                          seed={line.imageSeed ?? line.slug}
                          name={line.name}
                          className="h-24 w-20 rounded-xl sm:h-28 sm:w-24"
                        />
                      </Link>

                      <div className="flex min-w-0 flex-1 flex-col justify-between">
                        <div className="flex items-start justify-between gap-4">
                          <div className="min-w-0">
                            <Link
                              to={`/product/${line.slug}`}
                              className="block truncate text-[15px] font-medium tracking-tight text-ink-100 hover:text-amber-200"
                            >
                              {line.name}
                            </Link>
                            <p className="mt-1 text-[12px] capitalize text-ink-500">
                              {line.colorway ?? line.category}
                            </p>
                            {line.recId && (
                              <Badge variant="accent" className="mt-2">
                                From your recommendations
                              </Badge>
                            )}
                          </div>
                          <p className="shrink-0 text-[15px] font-medium text-ink-100">
                            {formatPrice(line.price * line.qty, line.currency)}
                          </p>
                        </div>

                        <div className="mt-4 flex items-center justify-between gap-4">
                          <div className="flex h-9 items-center rounded-full border border-white/[0.09]">
                            <button
                              onClick={() => setQty(line.productId, line.qty - 1)}
                              className="grid h-9 w-9 place-items-center rounded-l-full text-ink-400 hover:text-ink-100"
                              aria-label="Decrease quantity"
                            >
                              <Minus className="h-3 w-3" />
                            </button>
                            <span className="num w-7 text-center text-[13px] text-ink-100">
                              {line.qty}
                            </span>
                            <button
                              onClick={() => setQty(line.productId, line.qty + 1)}
                              className="grid h-9 w-9 place-items-center rounded-r-full text-ink-400 hover:text-ink-100"
                              aria-label="Increase quantity"
                            >
                              <Plus className="h-3 w-3" />
                            </button>
                          </div>

                          <button
                            onClick={() => remove(line.productId)}
                            className="inline-flex items-center gap-1.5 text-[12px] text-ink-500 transition-colors hover:text-rose-400"
                          >
                            <Trash2 className="h-3.5 w-3.5" />
                            Remove
                          </button>
                        </div>
                      </div>
                    </div>
                  </motion.li>
                ))}
              </AnimatePresence>
            </ul>

            <aside className="h-fit lg:sticky lg:top-[92px]">
              <div className="panel p-6">
                <p className="eyebrow">Summary</p>

                <dl className="mt-5 space-y-3 text-[13.5px]">
                  <div className="flex justify-between">
                    <dt className="text-ink-400">Subtotal</dt>
                    <dd className="text-ink-100">
                      <AnimatedNumber value={subtotal} decimals={2} prefix="$" />
                    </dd>
                  </div>
                  <div className="flex justify-between">
                    <dt className="text-ink-400">Shipping</dt>
                    <dd className="text-ink-100">
                      {shipping === 0 ? 'Free' : formatPrice(shipping, currency)}
                    </dd>
                  </div>
                  {subtotal < SHIPPING_THRESHOLD && (
                    <p className="text-[11.5px] leading-relaxed text-amber-300/80">
                      {formatPrice(SHIPPING_THRESHOLD - subtotal, currency)} more for free
                      delivery.
                    </p>
                  )}
                </dl>

                <div className="mt-5 flex items-baseline justify-between border-t border-white/[0.07] pt-5">
                  <span className="text-[13px] text-ink-400">Total</span>
                  <span className="text-[22px] font-medium tracking-tight text-ink-100">
                    <AnimatedNumber value={total} decimals={2} prefix="$" />
                  </span>
                </div>

                <Button className="mt-6 w-full" size="lg" onClick={() => void checkout()}>
                  Complete order
                  <ArrowRight className="h-4 w-4" />
                </Button>

                <p className="mt-4 text-center text-[11px] leading-relaxed text-ink-600">
                  Completing an order sends purchase signals for every recommended line, closing
                  the learning loop.
                </p>
              </div>
            </aside>
          </div>
        )}
      </div>

      <RecommendationRail
        context="cart"
        surface="cart-complementary"
        eyebrow="Completes the set"
        title="Frequently finished with"
        description="Complementary pieces scored against what is already in your bag."
        emptyHint="Add something to your bag and complementary picks will appear here."
        limit={8}
      />
    </>
  )
}
