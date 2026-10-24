import { Link } from 'react-router-dom'
import { Compass } from 'lucide-react'
import { Button, EmptyState } from '../components/ui'

export default function NotFound({ standalone = false }) {
  return (
    <div className={`container not-found${standalone ? ' notfound-standalone' : ''}`}>
      <EmptyState
        icon={Compass}
        title="This page does not exist"
        actions={
          <>
            <Button as={Link} to="/app" variant="primary">
              Go to dashboard
            </Button>
            <Button as={Link} to="/">
              Landing page
            </Button>
          </>
        }
      >
        The address may be mistyped, or the report it pointed to was removed.
      </EmptyState>
    </div>
  )
}
