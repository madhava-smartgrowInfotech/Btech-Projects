import { forwardRef } from 'react'
import { Link } from 'react-router-dom'
import { Loader2 } from 'lucide-react'

/** Sticker button: hard offset shadow, presses down into it on click. */
export const Button = forwardRef(function Button(
  { variant = 'secondary', size, block, loading, icon: Icon, iconRight: IconRight, to, href, className = '', children, disabled, ...rest },
  ref,
) {
  const cls = ['btn', `btn-${variant}`, size && `btn-${size}`, block && 'btn-block', className].filter(Boolean).join(' ')
  const content = (
    <>
      {loading ? <Loader2 size={18} className="spin" aria-hidden="true" /> : Icon && <Icon size={18} aria-hidden="true" />}
      {children}
      {IconRight && !loading && <IconRight size={18} aria-hidden="true" />}
    </>
  )
  if (to) {
    return (
      <Link ref={ref} to={to} className={cls} {...rest}>
        {content}
      </Link>
    )
  }
  if (href) {
    return (
      <a ref={ref} href={href} className={cls} {...rest}>
        {content}
      </a>
    )
  }
  return (
    <button ref={ref} type="button" className={cls} disabled={disabled || loading} aria-busy={loading || undefined} {...rest}>
      {content}
    </button>
  )
})

export function IconButton({ icon: Icon, label, size = 'md', className = '', ...rest }) {
  return (
    <button type="button" className={`icon-btn ${size === 'sm' ? 'sm' : ''} ${className}`} aria-label={label} title={label} {...rest}>
      <Icon size={size === 'sm' ? 16 : 20} aria-hidden="true" />
    </button>
  )
}
