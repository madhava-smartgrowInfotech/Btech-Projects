import { Link } from 'react-router-dom'
import { Compass } from 'lucide-react'
import { EmptyState } from '../components/ui'

export default function NotFound() {
  return (
    <main id="main" className="container" style={{ paddingTop: 96 }}>
      <EmptyState
        icon={Compass}
        title="Page not found"
        actions={
          <>
            <Link to="/" className="btn">
              Home
            </Link>
            <Link to="/app" className="btn btn-primary">
              Open my vault
            </Link>
          </>
        }
      >
        That address does not exist. Check the link or head back to your vault.
      </EmptyState>
    </main>
  )
}
