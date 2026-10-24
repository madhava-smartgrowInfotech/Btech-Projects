import { Compass } from 'lucide-react'
import { Brand, Button, EmptyState } from '../components/ui'

export default function NotFound({ standalone }) {
  const card = (
    <EmptyState
      icon={Compass}
      tone="peach"
      title="That page does not exist"
      message="The link may be old or mistyped."
      action={
        <>
          <Button to={standalone ? '/' : '/app'}>{standalone ? 'Go to the landing page' : 'Back to the overview'}</Button>
          {standalone && <Button to="/login" variant="secondary">Sign in</Button>}
        </>
      }
    />
  )
  if (!standalone) return card
  return (
    <div className="container" style={{ paddingTop: 48, display: 'grid', gap: 32 }}>
      <Brand />
      {card}
    </div>
  )
}
