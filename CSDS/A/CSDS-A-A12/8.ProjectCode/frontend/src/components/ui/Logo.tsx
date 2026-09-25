interface LogoProps {
  className?: string
  showWordmark?: boolean
}

export function Logo({ className = '', showWordmark = true }: LogoProps) {
  return (
    <div className={`flex items-center gap-2.5 ${className}`}>
      <svg width="30" height="30" viewBox="0 0 30 30" fill="none" xmlns="http://www.w3.org/2000/svg">
        <defs>
          <linearGradient id="seediq-grad" x1="0" y1="0" x2="30" y2="30" gradientUnits="userSpaceOnUse">
            <stop stopColor="#6ee7b7" />
            <stop offset="1" stopColor="#059669" />
          </linearGradient>
        </defs>
        <path
          d="M15 2C9 2 4 7.5 4 14.5C4 21 8.8 26.5 15 28C21.2 26.5 26 21 26 14.5C26 7.5 21 2 15 2Z"
          fill="url(#seediq-grad)"
          fillOpacity="0.18"
          stroke="url(#seediq-grad)"
          strokeWidth="1.4"
        />
        <path
          d="M15 24V13"
          stroke="#34d399"
          strokeWidth="1.6"
          strokeLinecap="round"
        />
        <path
          d="M15 13C15 13 15.5 8.5 20 8C20 12.5 15 13 15 13Z"
          fill="#fbbf24"
          fillOpacity="0.85"
        />
        <path
          d="M15 16C15 16 14.5 12.5 10.5 12C10.5 15.5 15 16 15 16Z"
          fill="#6ee7b7"
        />
      </svg>
      {showWordmark && (
        <span className="font-display text-lg font-bold tracking-tight text-[var(--color-text)]">
          Seed<span className="text-gradient">IQ</span>
        </span>
      )}
    </div>
  )
}
