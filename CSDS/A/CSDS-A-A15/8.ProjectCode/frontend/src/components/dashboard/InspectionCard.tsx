import { motion } from 'framer-motion'
import { Link } from 'react-router-dom'
import { SeverityBadge } from '@/components/dashboard/SeverityBadge'
import { useAuthedImage } from '@/hooks/useAuthedImage'
import type { InspectionOut } from '@/lib/api'
import { formatDate, formatPercent } from '@/lib/utils'

export function InspectionCard({ inspection }: { inspection: InspectionOut }) {
  const imageUrl = useAuthedImage(inspection.image_url)

  return (
    <Link to={`/app/inspections/${inspection.id}`}>
      <motion.div whileHover={{ y: -3 }} className="glass-card rounded-2xl overflow-hidden group">
        <div className="aspect-video bg-white/5 overflow-hidden">
          {imageUrl && (
            <img
              src={imageUrl}
              alt={inspection.asset_name}
              className="h-full w-full object-cover transition-transform duration-500 group-hover:scale-105"
            />
          )}
        </div>
        <div className="p-4">
          <div className="flex items-center justify-between mb-2">
            <p className="text-sm font-medium text-white truncate">{inspection.asset_name}</p>
            <span className="text-xs text-slate-500 shrink-0 ml-2">{formatDate(inspection.created_at)}</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-sm text-cyan-300">{inspection.display_name}</span>
            <span className="text-xs text-slate-500">{formatPercent(inspection.confidence)}</span>
          </div>
          <div className="mt-3">
            <SeverityBadge severity={inspection.severity} />
          </div>
        </div>
      </motion.div>
    </Link>
  )
}
