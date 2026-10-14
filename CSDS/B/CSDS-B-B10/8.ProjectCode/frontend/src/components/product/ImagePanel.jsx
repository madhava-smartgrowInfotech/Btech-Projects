import { Skeleton } from '../ui/feedback'

// One image with a caption. `src` is a data URL from the API; without it a skeleton shows.
export default function ImagePanel({ src, caption, className = '' }) {
  return (
    <figure className={`min-w-0 ${className}`}>
      <div className="grid aspect-square place-items-center overflow-hidden rounded-[6px] border border-line bg-panel-2">
        {src
          ? <img src={src} alt={caption} className="h-full w-full object-contain" />
          : <Skeleton className="h-full w-full" />}
      </div>
      <figcaption className="mt-1.5 font-mono text-[10px] uppercase tracking-[0.12em] text-dim">{caption}</figcaption>
    </figure>
  )
}
