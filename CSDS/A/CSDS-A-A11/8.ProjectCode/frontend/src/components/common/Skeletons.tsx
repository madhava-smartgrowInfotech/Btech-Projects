import { Skeleton } from '@/components/ui/skeleton'
import { cn } from '@/lib/utils'

export function ProductCardSkeleton({ className }: { className?: string }) {
  return (
    <div className={cn('space-y-3', className)}>
      <Skeleton className="aspect-[4/5] w-full rounded-2xl" />
      <Skeleton className="h-3.5 w-2/3" />
      <Skeleton className="h-3 w-1/3" />
    </div>
  )
}

export function RailSkeleton({ count = 4 }: { count?: number }) {
  return (
    <div className="grid grid-cols-2 gap-5 md:grid-cols-3 lg:grid-cols-4">
      {Array.from({ length: count }).map((_, i) => (
        <ProductCardSkeleton key={i} />
      ))}
    </div>
  )
}

export function GridSkeleton({ count = 8 }: { count?: number }) {
  return (
    <div className="grid grid-cols-2 gap-5 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
      {Array.from({ length: count }).map((_, i) => (
        <ProductCardSkeleton key={i} />
      ))}
    </div>
  )
}

export function MetricSkeleton() {
  return (
    <div className="panel space-y-3 p-5">
      <Skeleton className="h-2.5 w-20" />
      <Skeleton className="h-8 w-28" />
      <Skeleton className="h-2.5 w-16" />
    </div>
  )
}

export function ChartSkeleton({ className }: { className?: string }) {
  return <Skeleton className={cn('h-[260px] w-full rounded-xl', className)} />
}

export function LineSkeleton({ className }: { className?: string }) {
  return <Skeleton className={cn('h-3 w-full', className)} />
}
