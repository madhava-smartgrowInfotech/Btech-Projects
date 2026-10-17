import { useEffect } from 'react'
import { Link } from 'react-router-dom'
import { Compass } from 'lucide-react'
import { Button, EmptyState } from '../components/ui'

export default function NotFound({ standalone = false }) {
  useEffect(() => {
    document.title = 'Page not found · Health Assistant'
  }, [])
  const state = (
    <EmptyState
      icon={Compass}
      title="Page not found"
      actions={
        <>
          <Button as={Link} to="/app" variant="primary">
            Go to overview
          </Button>
          <Button as={Link} to="/">
            Landing page
          </Button>
        </>
      }
    >
      That address does not match any screen. Check the link or head back to the app.
    </EmptyState>
  )
  return standalone ? <main className="standalone-state">{state}</main> : <div className="container">{state}</div>
}
