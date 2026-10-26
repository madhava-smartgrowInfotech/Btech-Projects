import { Compass } from 'lucide-react'
import { Button, Container, EmptyState } from '../components/ui'

export default function NotFound() {
  return (
    <Container style={{ padding: '64px 16px 96px' }}>
      <EmptyState
        icon={Compass}
        title="Page not found"
        action={
          <div className="row">
            <Button variant="primary" to="/app">
              Open the dashboard
            </Button>
            <Button to="/">Go home</Button>
          </div>
        }
      >
        That address does not exist in TrendCast. Check the link, or start from the dashboard.
      </EmptyState>
    </Container>
  )
}
