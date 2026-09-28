import { Link } from 'react-router-dom'
import { Hand } from 'lucide-react'

export default function Logo({ to = '/app' }) {
  return (
    <Link to={to} className="flex items-center gap-2 font-semibold text-slate-900">
      <span className="w-8 h-8 rounded-lg bg-indigo-600 text-white grid place-items-center"><Hand size={18} /></span>
      SignBridge
    </Link>
  )
}
