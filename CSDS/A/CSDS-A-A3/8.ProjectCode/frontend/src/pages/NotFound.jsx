import { useEffect } from 'react'
import { Link } from 'react-router-dom'
import { Compass, Home, ScanSearch } from 'lucide-react'
import { Button, Card, Container, EmptyState } from '../components/ui'

export default function NotFound({ standalone = false }) {
  useEffect(() => {
    document.title = 'Page not found · PhishGuard'
  }, [])
  return (
    <Container className={standalone ? 'notfound-standalone' : ''}>
      <Card>
        <EmptyState
          icon={Compass}
          title="This page does not exist"
          actions={
            <>
              <Button as={Link} to="/" icon={Home}>
                Landing page
              </Button>
              <Button as={Link} to="/app/check" variant="primary" icon={ScanSearch}>
                Check a URL
              </Button>
            </>
          }
        >
          The link may be mistyped or out of date. Pick a destination below.
        </EmptyState>
      </Card>
    </Container>
  )
}
