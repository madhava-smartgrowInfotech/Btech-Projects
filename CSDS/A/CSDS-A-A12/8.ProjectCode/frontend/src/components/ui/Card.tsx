import type { HTMLAttributes, ReactNode } from 'react'

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  children: ReactNode
  glow?: boolean
  padding?: string
}

export function Card({ children, glow = false, padding = 'p-6', className = '', ...rest }: CardProps) {
  return (
    <div
      className={`glass rounded-2xl ${padding} ${glow ? 'glow-card' : ''} ${className}`}
      {...rest}
    >
      {children}
    </div>
  )
}
