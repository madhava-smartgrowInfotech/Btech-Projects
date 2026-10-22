import { useEffect } from 'react'
import { Compass } from 'lucide-react'
import { Button, EmptyState } from '../components/ui'

export default function NotFound() {
  useEffect(() => {
    document.title = 'Page not found - CareLens AI'
  }, [])
  return (
    <div className="state-center">
      <EmptyState
        icon={Compass}
        title="404 - page not found"
        action={
          <Button variant="primary" to="/">
            Back to home
          </Button>
        }
      >
        That address does not exist in CareLens AI. Check the link, or head back to the start.
      </EmptyState>
    </div>
  )
}
