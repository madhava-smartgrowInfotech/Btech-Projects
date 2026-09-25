import { AnimatePresence, motion } from 'framer-motion'
import { X } from 'lucide-react'
import { ResultsPanel } from '../workspace/ResultsPanel'
import type { PredictionRecord } from '../../types'

interface HistoryDetailModalProps {
  record: PredictionRecord | null
  onClose: () => void
}

export function HistoryDetailModal({ record, onClose }: HistoryDetailModalProps) {
  return (
    <AnimatePresence>
      {record && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-start justify-center p-4 sm:p-8 overflow-y-auto"
          onClick={onClose}
        >
          <motion.div
            initial={{ opacity: 0, y: 24, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 12, scale: 0.98 }}
            transition={{ type: 'spring', stiffness: 320, damping: 32 }}
            onClick={(e) => e.stopPropagation()}
            className="w-full max-w-2xl mt-8 mb-8"
          >
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-display text-lg font-semibold">Prediction detail</h3>
              <button
                onClick={onClose}
                className="w-9 h-9 rounded-full glass flex items-center justify-center hover:border-emerald-500/40 transition-colors"
              >
                <X size={16} />
              </button>
            </div>
            <ResultsPanel result={record} loading={false} error={null} />
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}
