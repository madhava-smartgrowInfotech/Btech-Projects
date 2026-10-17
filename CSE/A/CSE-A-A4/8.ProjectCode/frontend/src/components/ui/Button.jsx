import { forwardRef } from 'react'
import { motion } from 'framer-motion'
import { Link } from 'react-router-dom'
import { press } from '../../lib/motion'

const MotionLink = motion.create(Link)

/** variant: primary | secondary | ghost | danger | mint ; size: sm | md | lg */
export const Button = forwardRef(function Button(
  { variant = 'primary', size = 'md', loading = false, icon: Icon, iconRight: IconRight, block, to, className = '', children, disabled, ...rest },
  ref,
) {
  const cls = ['btn', variant !== 'primary' && variant, size !== 'md' && size, block && 'block', className].filter(Boolean).join(' ')
  const inner = (
    <>
      {loading ? <span className="spinner" aria-hidden="true" /> : Icon && <Icon size={size === 'sm' ? 16 : 18} aria-hidden="true" />}
      {children}
      {IconRight && !loading && <IconRight size={size === 'sm' ? 16 : 18} aria-hidden="true" />}
    </>
  )
  const anim = disabled || loading ? {} : press
  if (to) {
    return (
      <MotionLink ref={ref} to={to} className={cls} {...anim} {...rest}>
        {inner}
      </MotionLink>
    )
  }
  return (
    <motion.button
      ref={ref}
      type="button"
      className={cls}
      disabled={disabled || loading}
      aria-busy={loading || undefined}
      {...anim}
      {...rest}
    >
      {inner}
    </motion.button>
  )
})

export const IconButton = forwardRef(function IconButton({ icon: Icon, label, plain, size = 20, className = '', ...rest }, ref) {
  return (
    <motion.button
      ref={ref}
      type="button"
      className={`icon-btn ${plain ? 'plain' : ''} ${className}`}
      aria-label={label}
      title={label}
      whileHover={{ scale: 1.08 }}
      whileTap={{ scale: 0.9 }}
      transition={press.transition}
      {...rest}
    >
      <Icon size={size} aria-hidden="true" />
    </motion.button>
  )
})
