import { useEffect, useState } from 'react'
import { useReducedMotion } from '../../lib/reduced'

// Types `text` out character by character. The full text reserves the space (no layout shift)
// and is what assistive tech reads; reduced motion shows it at once.
export default function Typewriter({ text, as: Tag = 'span', speed = 28, delay = 0, caret = true, keepCaret = false, className = '' }) {
  const reduced = useReducedMotion()
  const [n, setN] = useState(reduced ? text.length : 0)
  useEffect(() => {
    if (reduced) {
      setN(text.length)
      return
    }
    setN(0)
    let i = 0
    let timer
    const tick = () => {
      i += 1
      setN(i)
      if (i < text.length) timer = setTimeout(tick, speed)
    }
    timer = setTimeout(tick, delay)
    return () => clearTimeout(timer)
  }, [text, speed, delay, reduced])
  const typing = n < text.length
  return (
    <Tag className={className} aria-label={text}>
      <span className="grid" aria-hidden="true">
        <span className="invisible col-start-1 row-start-1">{text}{caret && <span className="tw-caret" />}</span>
        <span className="col-start-1 row-start-1">
          {text.slice(0, n)}
          {caret && (typing || keepCaret) && !reduced && <span className="tw-caret" />}
        </span>
      </span>
    </Tag>
  )
}
