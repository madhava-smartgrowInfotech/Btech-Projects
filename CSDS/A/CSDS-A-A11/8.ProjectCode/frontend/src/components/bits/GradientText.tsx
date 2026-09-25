import type { ReactNode } from 'react'
import { cn } from '@/lib/utils'

/** Slow-drifting metallic sheen across a headline fragment. */
export function GradientText({
  children,
  className,
}: {
  children: ReactNode
  className?: string
}) {
  return (
    <span
      className={cn(
        'bg-[linear-gradient(100deg,#F3D194_0%,#E5A54B_22%,#FBF3E2_46%,#E5A54B_68%,#F3D194_100%)] bg-[length:250%_100%] bg-clip-text text-transparent',
        'animate-[shine_7s_linear_infinite]',
        className,
      )}
      style={{ WebkitBackgroundClip: 'text' }}
    >
      {children}
      <style>{`@keyframes shine{0%{background-position:0% 50%}100%{background-position:250% 50%}}`}</style>
    </span>
  )
}
