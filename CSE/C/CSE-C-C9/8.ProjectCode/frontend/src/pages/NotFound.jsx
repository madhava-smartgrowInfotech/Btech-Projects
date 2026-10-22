import { Compass, Home } from 'lucide-react'
import { Button, Container, EmptyState } from '../components/ui'

export default function NotFound({ standalone }) {
  const body = (
    <EmptyState
      icon={Compass}
      tone="peach"
      title="Page not found"
      message="The page you requested was not found. It may have moved, or the address may be mistyped."
      action={
        <>
          <Button to="/app" icon={Home}>Go to the dashboard</Button>
          <Button to="/" variant="secondary">Landing page</Button>
        </>
      }
    />
  )
  return standalone ? (
    <main id="main" style={{ padding: '72px 0' }}>
      <Container>{body}</Container>
    </main>
  ) : (
    body
  )
}
