import { useEffect, useState } from 'react'
import api, { errorMessage } from '../api.js'
import { Skeleton } from './ui/Feedback.jsx'

/** <img> that loads through the API (so the JWT is sent) and shows a placeholder while loading or on failure. */
export default function AuthImage({ src, alt, className = '', style }) {
  const [url, setUrl] = useState(null)
  const [failed, setFailed] = useState('')

  useEffect(() => {
    let objectUrl
    let cancelled = false
    setUrl(null)
    setFailed('')
    api
      .get(src, { responseType: 'blob' })
      .then((r) => {
        if (cancelled) return
        objectUrl = URL.createObjectURL(r.data)
        setUrl(objectUrl)
      })
      .catch(async (e) => {
        if (!cancelled) setFailed(await errorMessage(e))
      })
    return () => {
      cancelled = true
      if (objectUrl) URL.revokeObjectURL(objectUrl)
    }
  }, [src])

  if (failed) {
    return (
      <div className={`${className} image-fallback`} role="img" aria-label={`${alt} unavailable`} style={style}>
        Image unavailable
      </div>
    )
  }
  if (!url) return <Skeleton height="100%" style={{ aspectRatio: '1 / 1', ...style }} />
  return <img src={url} alt={alt} className={className} style={style} />
}
