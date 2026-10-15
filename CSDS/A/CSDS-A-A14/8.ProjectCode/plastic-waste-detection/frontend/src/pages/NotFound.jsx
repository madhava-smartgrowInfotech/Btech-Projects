import { useEffect } from 'react'
import { Compass } from 'lucide-react'
import { Button, Container, EmptyState } from '../components/ui'

export default function NotFound() {
  useEffect(() => {
    document.title = 'Page not found · PlastiScan'
  }, [])
  return (
    <Container style={{ paddingTop: 72, paddingBottom: 72 }}>
      <EmptyState
        icon={Compass}
        tone="sky"
        title="That page drifted away"
        message="The address you opened does not exist in PlastiScan."
        action={
          <>
            <Button to="/app/detect">Open detection</Button>
            <Button to="/" variant="secondary">
              Back to the landing page
            </Button>
          </>
        }
      />
    </Container>
  )
}
