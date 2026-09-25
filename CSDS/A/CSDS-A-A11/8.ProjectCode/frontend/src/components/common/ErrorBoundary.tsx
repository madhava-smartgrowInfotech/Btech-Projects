import { Component, type ErrorInfo, type ReactNode } from 'react'
import { Button } from '@/components/ui/button'

type Props = { children: ReactNode }
type State = { error: Error | null }

/** Last line of defence — a render failure degrades to a recoverable panel, never a blank page. */
export class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null }

  static getDerivedStateFromError(error: Error): State {
    return { error }
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error('Nuvara render error', error, info.componentStack)
  }

  render() {
    if (!this.state.error) return this.props.children

    return (
      <div className="flex min-h-screen flex-col items-center justify-center gap-5 bg-ink-950 px-6 text-center">
        <p className="font-mono text-[11px] uppercase tracking-[0.24em] text-amber-300/80">
          Interface error
        </p>
        <h1 className="max-w-lg text-[26px] font-medium tracking-tighter text-ink-100">
          Something in this view stopped responding
        </h1>
        <p className="max-w-md text-[13.5px] leading-relaxed text-ink-400">
          {this.state.error.message}
        </p>
        <div className="flex gap-3">
          <Button onClick={() => this.setState({ error: null })}>Try again</Button>
          <Button variant="outline" onClick={() => window.location.assign('/')}>
            Back home
          </Button>
        </div>
      </div>
    )
  }
}
