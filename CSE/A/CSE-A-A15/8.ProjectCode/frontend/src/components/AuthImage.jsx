import { useEffect, useState } from 'react'
import { AlertCircle } from 'lucide-react'
import { blobUrl } from '../api'
import { Skeleton } from './ui/feedback'

// <img> for endpoints that need the Authorization header. Skeleton while loading; says so if it fails.
export default function AuthImage({ path, alt, className = '' }) {
  const [src, setSrc] = useState(null)
  const [failed, setFailed] = useState(false)

  useEffect(() => {
    let url
    let live = true
    setSrc(null)
    setFailed(false)
    blobUrl(path)
      .then((u) => {
        url = u
        if (live) setSrc(u)
        else URL.revokeObjectURL(u)
      })
      .catch(() => live && setFailed(true))
    return () => {
      live = false
      if (url) URL.revokeObjectURL(url)
    }
  }, [path])

  if (failed) {
    return (
      <div role="alert" className="flex items-center gap-2 rounded-[6px] border border-alert/35 bg-alert/[0.07] p-4 text-sm text-alert">
        <AlertCircle size={16} aria-hidden="true" /> Could not load this image. Refresh the page or run the operation again.
      </div>
    )
  }
  if (!src) return <Skeleton className="h-48 w-full" />
  return <img src={src} alt={alt} className={className} />
}
