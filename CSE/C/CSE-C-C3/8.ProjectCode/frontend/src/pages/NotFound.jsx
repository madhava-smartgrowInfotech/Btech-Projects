import { Link } from 'react-router-dom'
import { Compass, Home } from 'lucide-react'
import { Button, EmptyState } from '../components/ui'

export default function NotFound() {
  return (
    <main id="main" style={{ minHeight: '100vh', display: 'grid', placeItems: 'center', padding: 24 }}>
      <EmptyState
        icon={Compass}
        title="That page does not exist"
        actions={
          <Button as={Link} to="/" variant="primary" icon={Home}>
            Back to ParkSure
          </Button>
        }
      >
        The link may be old or mistyped.
      </EmptyState>
    </main>
  )
}
