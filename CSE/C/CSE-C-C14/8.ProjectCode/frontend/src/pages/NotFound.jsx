import { Compass } from 'lucide-react'
import { useDocTitle } from '../lib/hooks'
import { Button, EmptyState } from '../components/ui'

export default function NotFound() {
  useDocTitle('Page not found · VeriVision AI')
  return (
    <div className="container" style={{ minHeight: '100vh', display: 'grid', placeItems: 'center' }}>
      <EmptyState
        icon={Compass}
        tone="sky"
        title="We couldn't find that page"
        message="The address may be mistyped or the page may have moved. You can head back to the analyzer or the landing page."
        action={
          <>
            <Button to="/app">Open the analyzer</Button>
            <Button to="/" variant="secondary">Landing page</Button>
          </>
        }
      />
    </div>
  )
}
