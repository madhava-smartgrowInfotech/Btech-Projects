import { Compass } from 'lucide-react'
import { Button, Container, EmptyState } from '../components/ui'
import { useDocumentTitle } from '../lib/hooks'

export default function NotFound() {
  useDocumentTitle('Page not found')
  return (
    <Container style={{ padding: '64px 16px' }}>
      <EmptyState
        icon={Compass}
        title="404 · Nothing at this address"
        action={
          <Button variant="primary" to="/">
            Back to the home page
          </Button>
        }
      >
        The page you opened does not exist. Check the link, or head back and start from the home page.
      </EmptyState>
    </Container>
  )
}
