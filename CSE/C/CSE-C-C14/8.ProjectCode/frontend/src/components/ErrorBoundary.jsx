import { Component } from 'react'
import { ErrorState } from './ui'

/** Last line of defence: a render crash shows a recoverable error instead of a blank page. */
export default class ErrorBoundary extends Component {
  state = { error: null }

  static getDerivedStateFromError(error) {
    return { error }
  }

  componentDidCatch(error, info) {
    console.error('UI crashed:', error, info?.componentStack)
  }

  render() {
    if (!this.state.error) return this.props.children
    return (
      <div className="container" style={{ paddingTop: 48 }}>
        <ErrorState
          title="This screen hit a problem"
          error={this.state.error.message}
          hint="Reload the page. If it keeps happening, check the browser console and the API terminal."
          onRetry={() => window.location.reload()}
        />
      </div>
    )
  }
}
