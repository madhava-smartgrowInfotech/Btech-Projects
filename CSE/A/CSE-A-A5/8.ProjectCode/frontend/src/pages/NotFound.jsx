import { Compass } from 'lucide-react'
import { Link } from 'react-router-dom'
import { EmptyState } from '../components/ui/feedback'

export default function NotFound({ standalone = false }) {
  const body = (
    <EmptyState icon={Compass} title="404 - route not found" body="That page does not exist in CipherGuard Shield."
      action={(
        <Link to="/app" className="inline-flex h-9 items-center rounded-[6px] bg-ok px-3.5 text-sm font-medium text-on-ok hover:brightness-110">Back to live scoring</Link>
      )} />
  )
  return standalone ? <main className="grid min-h-screen place-items-center p-6">{body}</main> : body
}
