import { Compass, Home, LayoutDashboard } from 'lucide-react'
import { Button, EmptyState } from '../components/ui'

export default function NotFound({ standalone }) {
  const body = (
    <EmptyState
      icon={Compass}
      title="This page wandered off"
      message="The address does not match any screen in HubOptima."
      action={
        <>
          <Button to="/app" icon={LayoutDashboard}>
            Open the dashboard
          </Button>
          <Button to="/" variant="secondary" icon={Home}>
            Landing page
          </Button>
        </>
      }
    />
  )
  if (!standalone) return body
  return (
    <main className="container" style={{ paddingTop: '12vh' }}>
      {body}
    </main>
  )
}
