import { Compass } from 'lucide-react'
import { Button, Container, EmptyState } from '../components/ui'

export default function NotFound() {
  return (
    <Container style={{ padding: '64px 16px' }}>
      <EmptyState
        icon={Compass}
        title="Wrong turn"
        action={
          <Button variant="primary" to="/">
            Back to the start
          </Button>
        }
      >
        That page does not exist. Check the address, or head back and pick a screen from the menu.
      </EmptyState>
    </Container>
  )
}
