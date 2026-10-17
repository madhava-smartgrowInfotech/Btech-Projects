import { Compass } from 'lucide-react'
import { Button, Container, EmptyState } from '../components/ui'

export default function NotFound() {
  return (
    <Container style={{ padding: '64px 16px' }}>
      <EmptyState icon={Compass} title="Page not found" action={<Button variant="primary" to="/monitor">Go to the live monitor</Button>}>
        That address does not exist in ResQAI.
      </EmptyState>
    </Container>
  )
}
