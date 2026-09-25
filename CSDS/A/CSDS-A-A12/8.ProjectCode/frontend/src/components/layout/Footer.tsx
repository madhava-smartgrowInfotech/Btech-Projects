import { Logo } from '../ui/Logo'

export function Footer() {
  return (
    <footer className="relative border-t border-[var(--color-border-soft)] mt-24">
      <div className="mx-auto max-w-6xl px-6 py-14 flex flex-col md:flex-row items-start md:items-center justify-between gap-8">
        <div>
          <Logo />
          <p className="text-sm text-[var(--color-text-muted)] mt-3 max-w-sm">
            Precision germination intelligence for seed labs, agronomists, and modern agriculture
            teams — from image to insight in seconds.
          </p>
        </div>
        <div className="flex gap-12 text-sm">
          <div className="flex flex-col gap-2">
            <span className="text-[var(--color-text-faint)] uppercase tracking-wider text-xs mb-1">Platform</span>
            <a href="/app" className="text-[var(--color-text-muted)] hover:text-[var(--color-text)] transition-colors">Workspace</a>
            <a href="/history" className="text-[var(--color-text-muted)] hover:text-[var(--color-text)] transition-colors">History</a>
            <a href="/insights" className="text-[var(--color-text-muted)] hover:text-[var(--color-text)] transition-colors">Insights</a>
          </div>
          <div className="flex flex-col gap-2">
            <span className="text-[var(--color-text-faint)] uppercase tracking-wider text-xs mb-1">Engine</span>
            <span className="text-[var(--color-text-muted)]">JEPA Vision Encoder</span>
            <span className="text-[var(--color-text-muted)]">Environmental Fusion</span>
            <span className="text-[var(--color-text-muted)]">Explainable Advisory</span>
          </div>
        </div>
      </div>
      <div className="border-t border-[var(--color-border-soft)] py-5 text-center text-xs text-[var(--color-text-faint)]">
        © {new Date().getFullYear()} SeedIQ. Precision germination analytics.
      </div>
    </footer>
  )
}
