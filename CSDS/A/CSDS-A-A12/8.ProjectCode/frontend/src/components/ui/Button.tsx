import type { ButtonHTMLAttributes, ReactNode } from 'react'
import { motion } from 'framer-motion'

interface ButtonProps extends Omit<ButtonHTMLAttributes<HTMLButtonElement>, 'children'> {
  variant?: 'primary' | 'secondary' | 'ghost'
  size?: 'sm' | 'md' | 'lg'
  children: ReactNode
  icon?: ReactNode
}

const variants: Record<string, string> = {
  primary:
    'bg-gradient-to-r from-emerald-500 to-emerald-600 text-[#04120b] hover:brightness-110 shadow-[0_0_30px_-8px_rgba(16,185,129,0.6)]',
  secondary:
    'bg-[var(--color-surface-2)] text-[var(--color-text)] border border-[var(--color-border)] hover:border-emerald-500/50 hover:bg-[var(--color-surface)]',
  ghost: 'bg-transparent text-[var(--color-text-muted)] hover:text-[var(--color-text)]',
}

const sizes: Record<string, string> = {
  sm: 'px-3.5 py-1.5 text-sm',
  md: 'px-5 py-2.5 text-sm',
  lg: 'px-7 py-3.5 text-base',
}

export function Button({
  variant = 'primary',
  size = 'md',
  children,
  icon,
  className = '',
  ...rest
}: ButtonProps) {
  return (
    <motion.button
      whileHover={{ y: -2 }}
      whileTap={{ scale: 0.97 }}
      transition={{ type: 'spring', stiffness: 400, damping: 20 }}
      className={`inline-flex items-center justify-center gap-2 rounded-full font-semibold tracking-tight transition-colors duration-200 cursor-pointer disabled:opacity-50 disabled:pointer-events-none ${variants[variant]} ${sizes[size]} ${className}`}
      {...(rest as any)}
    >
      {children}
      {icon}
    </motion.button>
  )
}
