import { type ReactNode } from 'react'

export function PageHeader({
  title,
  description,
  action,
}: {
  title: string
  description?: string
  action?: ReactNode
}) {
  return (
    <div className="flex items-center justify-between h-16 px-8 border-b border-white/5 bg-[#05070c]/60 backdrop-blur-sm sticky top-0 z-10">
      <div>
        <h1 className="font-display text-lg font-semibold text-white">{title}</h1>
        {description && <p className="text-xs text-slate-500">{description}</p>}
      </div>
      {action}
    </div>
  )
}
