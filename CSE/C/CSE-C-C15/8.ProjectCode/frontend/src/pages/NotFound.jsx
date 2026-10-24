import { Compass } from 'lucide-react'
import { Link } from 'react-router-dom'
import { Button } from '../components/ui/controls'
import { EmptyState } from '../components/ui/feedback'

export default function NotFound({ standalone = false }) {
  const body = (
    <EmptyState icon={Compass} title="404 · no such screen" body="That address does not exist in the SentinelFlow console."
      action={<Link to={standalone ? '/' : '/app'}><Button>{standalone ? 'Back to home' : 'Back to overview'}</Button></Link>} />
  )
  return standalone ? <main className="grid min-h-screen place-items-center p-6">{body}</main> : <div className="panel">{body}</div>
}
