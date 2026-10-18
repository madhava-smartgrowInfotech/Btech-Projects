import { Compass } from 'lucide-react'
import { Button, EmptyState } from '../components/ui'

export default function NotFound({ standalone }) {
  const body = (
    <EmptyState
      icon={Compass}
      tone="sky"
      title="That page does not exist"
      message="The link may be old or mistyped. Head back to the dashboard or the landing page."
      action={
        <>
          <Button to="/app">Open dashboard</Button>
          <Button variant="secondary" to="/">
            Landing page
          </Button>
        </>
      }
    />
  )
  return standalone ? (
    <main className="container" style={{ paddingTop: 72 }}>
      {body}
    </main>
  ) : (
    body
  )
}
