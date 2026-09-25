import { Link } from 'react-router-dom'
import { Button } from '@/components/ui/button'

export default function NotFound() {
  return (
    <div className="container flex min-h-[70vh] flex-col items-center justify-center py-24 text-center">
      <p className="font-mono text-[12px] uppercase tracking-[0.24em] text-amber-300/80">404</p>
      <h1 className="mt-5 text-[38px] font-medium leading-tight tracking-tighter text-ink-100 sm:text-[52px]">
        This page moved on
      </h1>
      <p className="mt-4 max-w-md text-[15px] leading-relaxed text-ink-400">
        The link you followed does not point anywhere in the catalog. The collection is still
        where you left it.
      </p>
      <div className="mt-8 flex flex-wrap justify-center gap-3">
        <Button asChild>
          <Link to="/">Back home</Link>
        </Button>
        <Button asChild variant="outline">
          <Link to="/shop">Browse the collection</Link>
        </Button>
      </div>
    </div>
  )
}
