import { useEffect, useState } from 'react'
import { fetchAuthedImage } from '@/lib/api'

export function useAuthedImage(url: string | null): string | null {
  const [blobUrl, setBlobUrl] = useState<string | null>(null)

  useEffect(() => {
    if (!url) {
      setBlobUrl(null)
      return
    }
    let objectUrl: string | null = null
    let cancelled = false

    fetchAuthedImage(url).then((u) => {
      if (cancelled) {
        URL.revokeObjectURL(u)
        return
      }
      objectUrl = u
      setBlobUrl(u)
    })

    return () => {
      cancelled = true
      if (objectUrl) URL.revokeObjectURL(objectUrl)
    }
  }, [url])

  return blobUrl
}
