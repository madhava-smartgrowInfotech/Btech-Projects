import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { ArrowRight, ArrowUpRight, Quote, Sparkles } from 'lucide-react'
import { HeroScene } from '@/components/three/HeroScene'
import { TextReveal } from '@/components/bits/TextReveal'
import { GradientText } from '@/components/bits/GradientText'
import { MagneticButton } from '@/components/bits/MagneticButton'
import { Reveal } from '@/components/bits/Reveal'
import { ProductArt } from '@/components/bits/ProductArt'
import { AnimatedNumber } from '@/components/bits/AnimatedNumber'
import { SpotlightCard } from '@/components/bits/SpotlightCard'
import { RecommendationRail } from '@/components/product/RecommendationRail'
import { ProductCard } from '@/components/product/ProductCard'
import { Rail } from '@/components/common/Rail'
import { SectionHeading } from '@/components/common/SectionHeading'
import { RailSkeleton } from '@/components/common/Skeletons'
import { EmptyState, ErrorState } from '@/components/common/States'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { useCategories, useProductRail } from '@/hooks/useQueries'
import { useReveal } from '@/hooks/useReveal'
import { useTracking } from '@/hooks/useTracking'
import { useSession } from '@/store/session'
import { EASE_EXPO, formatCompact } from '@/lib/utils'

const HERO_STATS = [
  { label: 'Signals processed daily', value: 2.4, suffix: 'M', decimals: 1 },
  { label: 'Agents in the ensemble', value: 4, suffix: '', decimals: 0 },
  { label: 'Median rank latency', value: 38, suffix: 'ms', decimals: 0 },
]

const TESTIMONIALS = [
  {
    quote:
      'The second I switched to the warmer palette, the whole shop reorganised around it. It felt like the store already knew.',
    name: 'Mireille Kahn',
    role: 'Interior architect, Antwerp',
  },
  {
    quote:
      'I bought the desk lamp, and every suggestion afterwards made sense. Nothing random, nothing loud.',
    name: 'Daniel Osei',
    role: 'Product designer, Lisbon',
  },
  {
    quote:
      'Three orders in and it has never once shown me something I would not consider. That is rare.',
    name: 'Sofia Lindqvist',
    role: 'Studio owner, Stockholm',
  },
  {
    quote:
      'Beautiful objects, and the fit is uncanny. I stopped scrolling past the recommendations.',
    name: 'Arjun Mehta',
    role: 'Composer, Berlin',
  },
]

function Hero() {
  const persona = useSession((s) => s.persona)

  return (
    <section className="relative overflow-hidden">
      <div className="pointer-events-none absolute inset-0">
        <HeroScene className="absolute inset-0 h-full w-full" />
        <div className="absolute inset-0 bg-[radial-gradient(70%_60%_at_50%_40%,transparent,rgba(7,8,10,0.55)_72%,rgba(7,8,10,0.96))]" />
      </div>

      <div className="container relative flex min-h-[86vh] flex-col justify-center py-24">
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, ease: EASE_EXPO }}
          className="mb-8"
        >
          <Badge variant="accent" className="px-3 py-1.5">
            <Sparkles className="h-3 w-3" />
            Autumn release — the Quiet Materials collection
          </Badge>
        </motion.div>

        <TextReveal
          as="h1"
          immediate
          delay={0.15}
          text="Objects worth keeping,"
          className="max-w-[16ch] text-[13vw] font-medium leading-[0.95] tracking-tightest text-ink-100 sm:text-[9vw] lg:text-[84px]"
        />
        <TextReveal
          as="h1"
          immediate
          delay={0.3}
          text="found without the noise."
          className="max-w-[18ch] text-[13vw] font-medium leading-[0.95] tracking-tightest text-ink-400 sm:text-[9vw] lg:text-[84px]"
        />

        <motion.p
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.9, delay: 0.6, ease: EASE_EXPO }}
          className="mt-8 max-w-xl text-[16px] leading-relaxed text-ink-400"
        >
          A small range of lighting, audio and workspace pieces — surfaced by an ensemble of
          agents that reads what you linger on, not what someone paid to promote.
        </motion.p>

        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.9, delay: 0.72, ease: EASE_EXPO }}
          className="mt-10 flex flex-wrap items-center gap-3"
        >
          <MagneticButton>
            <Button asChild size="lg">
              <Link to="/shop">
                Browse the collection
                <ArrowRight className="h-4 w-4" />
              </Link>
            </Button>
          </MagneticButton>
          <Button asChild variant="outline" size="lg">
            <Link to="/intelligence">
              See how it decides
              <ArrowUpRight className="h-4 w-4" />
            </Link>
          </Button>
        </motion.div>

        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 1, delay: 0.95, ease: EASE_EXPO }}
          className="mt-16 grid max-w-2xl grid-cols-3 gap-6 border-t border-white/[0.07] pt-8"
        >
          {HERO_STATS.map((stat) => (
            <div key={stat.label}>
              <p className="text-[24px] font-medium tracking-tight text-ink-100 sm:text-[30px]">
                <AnimatedNumber
                  value={stat.value}
                  decimals={stat.decimals}
                  suffix={stat.suffix}
                  startOnView
                />
              </p>
              <p className="mt-1.5 text-[11.5px] leading-snug text-ink-500">{stat.label}</p>
            </div>
          ))}
        </motion.div>

        {persona && (
          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 1, delay: 1.1 }}
            className="mt-8 inline-flex items-center gap-2 text-[12px] text-ink-500"
          >
            <span className="h-1.5 w-1.5 rounded-full bg-amber-400" />
            Personalising for <span className="text-ink-300">{persona.name}</span> ·{' '}
            {persona.segment}
          </motion.p>
        )}
      </div>
    </section>
  )
}

function CategoryRail() {
  const { data, isLoading, isError, error, refetch } = useCategories()
  const containerRef = useReveal<HTMLDivElement>({ selector: '[data-reveal]', stagger: 0.09 })

  return (
    <section className="container py-16 sm:py-20">
      <SectionHeading
        eyebrow="The range"
        title="Four rooms, one material language"
        description="Every piece shares the same palette of anodised aluminium, oiled ash and recycled wool — so anything you add still belongs."
        action={
          <Button asChild variant="ghost" size="sm">
            <Link to="/shop">
              All products
              <ArrowRight className="h-3.5 w-3.5" />
            </Link>
          </Button>
        }
      />

      <div ref={containerRef} className="mt-10">
        {isLoading && (
          <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
            {Array.from({ length: 4 }).map((_, i) => (
              <Skeleton key={i} className="aspect-[4/3] w-full rounded-2xl" />
            ))}
          </div>
        )}

        {isError && <ErrorState error={error} onRetry={() => void refetch()} />}

        {data && data.length === 0 && (
          <EmptyState title="Catalog is being prepared" description="Categories will appear here." />
        )}

        {data && data.length > 0 && (
          <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
            {data.slice(0, 8).map((category) => (
              <Link key={String(category.id)} to={`/shop/${category.slug}`} data-reveal>
                <SpotlightCard className="h-full">
                  <div className="relative">
                    <ProductArt
                      seed={category.slug}
                      name={category.name}
                      className="aspect-[4/3] w-full"
                    />
                    <div className="absolute inset-0 bg-gradient-to-t from-ink-950/85 via-ink-950/10 to-transparent" />
                    <div className="absolute inset-x-0 bottom-0 flex items-end justify-between gap-3 p-4">
                      <div>
                        <p className="text-[15px] font-medium tracking-tight text-ink-100">
                          {category.name}
                        </p>
                        <p className="mt-0.5 text-[11.5px] text-ink-400">
                          {formatCompact(category.product_count)} pieces
                        </p>
                      </div>
                      <ArrowUpRight className="h-4 w-4 shrink-0 text-ink-400 transition-transform duration-500 ease-expo group-hover/spot:-translate-y-0.5 group-hover/spot:translate-x-0.5" />
                    </div>
                  </div>
                </SpotlightCard>
              </Link>
            ))}
          </div>
        )}
      </div>
    </section>
  )
}

function TrendingRail() {
  const { items, isLoading, isError, error, refetch } = useProductRail({
    sort: 'trending',
    limit: 8,
  })
  const { track } = useTracking()

  return (
    <section className="container py-16 sm:py-20">
      <SectionHeading
        eyebrow="Moving fast"
        title="What the catalog is gravitating toward"
        description="Ranked by the trending agent on a rolling seven-day window of views, adds and completed orders."
      />
      <div className="mt-10">
        {isLoading && <RailSkeleton count={4} />}
        {isError && <ErrorState error={error} onRetry={() => void refetch()} />}
        {!isLoading && !isError && items.length === 0 && (
          <EmptyState title="Nothing trending yet" description="Check back once orders start landing." />
        )}
        {items.length > 0 && (
          <Rail>
            {items.map((product) => (
              <ProductCard
                key={String(product.id)}
                product={product}
                onOpen={() => track({ type: 'click', product })}
              />
            ))}
          </Rail>
        )}
      </div>
    </section>
  )
}

function IntelligenceBand() {
  return (
    <section className="container py-16 sm:py-20">
      <Reveal>
        <div className="noise relative overflow-hidden rounded-4xl border border-white/[0.08] bg-gradient-to-br from-ink-875 via-ink-900 to-ink-950 p-8 sm:p-14">
          <div
            aria-hidden
            className="pointer-events-none absolute -right-24 -top-24 h-[420px] w-[420px] rounded-full bg-[radial-gradient(circle,rgba(229,165,75,0.18),transparent_65%)] blur-2xl"
          />
          <div className="relative max-w-2xl">
            <p className="eyebrow">Under the storefront</p>
            <h2 className="mt-4 text-[30px] font-medium leading-[1.08] tracking-tighter text-ink-100 sm:text-[42px]">
              Every recommendation can{' '}
              <GradientText>explain itself</GradientText>.
            </h2>
            <p className="mt-5 text-[15px] leading-relaxed text-ink-400">
              Four agents propose, a weighted orchestrator decides, and the outcome of every
              click feeds straight back into the weights. The console shows the whole loop —
              simulation lab, learning history and live traffic.
            </p>
            <div className="mt-8 flex flex-wrap gap-3">
              <Button asChild>
                <Link to="/intelligence">
                  Open the console
                  <ArrowUpRight className="h-4 w-4" />
                </Link>
              </Button>
              <Button asChild variant="ghost">
                <Link to="/shop">Keep browsing</Link>
              </Button>
            </div>
          </div>
        </div>
      </Reveal>
    </section>
  )
}

function Testimonials() {
  const ref = useReveal<HTMLDivElement>({ stagger: 0.08 })
  return (
    <section className="container py-16 sm:py-20">
      <SectionHeading eyebrow="In the wild" title="What people say after a few orders" />
      <div ref={ref} className="mt-10 grid gap-5 md:grid-cols-2 xl:grid-cols-4">
        {TESTIMONIALS.map((item) => (
          <figure
            key={item.name}
            data-reveal
            className="panel flex h-full flex-col justify-between p-6"
          >
            <Quote className="h-4 w-4 text-amber-400/70" />
            <blockquote className="mt-4 flex-1 text-[14px] leading-relaxed text-ink-200">
              {item.quote}
            </blockquote>
            <figcaption className="mt-6 border-t border-white/[0.06] pt-4">
              <p className="text-[13px] font-medium text-ink-100">{item.name}</p>
              <p className="mt-0.5 text-[11.5px] text-ink-500">{item.role}</p>
            </figcaption>
          </figure>
        ))}
      </div>
    </section>
  )
}

export default function Home() {
  return (
    <>
      <Hero />
      <CategoryRail />
      <RecommendationRail
        context="home"
        surface="home-rail"
        eyebrow="Recommended for you"
        title="Chosen for how you shop"
        description="Switch the shopper profile in the header and this rail re-ranks against a different behavioural history — same catalog, different ordering."
        showStrategy
        limit={8}
      />
      <TrendingRail />
      <IntelligenceBand />
      <Testimonials />
    </>
  )
}
