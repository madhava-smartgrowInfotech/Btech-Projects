import { useEffect } from 'react'
import { Link } from 'react-router-dom'
import { Compass, Home } from 'lucide-react'
import { Button, Card, EmptyState } from '../components/ui'

export default function NotFound({ standalone = false }) {
  useEffect(() => {
    document.title = 'Page not found · BioSight'
  }, [])
  const body = (
    <Card>
      <EmptyState
        icon={Compass}
        title="This page does not exist"
        actions={
          <>
            <Button as={Link} to="/app/mri" variant="primary">
              Open the workspace
            </Button>
            <Button as={Link} to="/" icon={Home}>
              Landing page
            </Button>
          </>
        }
      >
        The link may be mistyped or out of date.
      </EmptyState>
    </Card>
  )
  return standalone ? (
    <main className="auth-wrap">
      <div className="auth-card">{body}</div>
    </main>
  ) : (
    <div className="container">{body}</div>
  )
}
