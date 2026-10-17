import { motion } from 'framer-motion'
import { softSpring } from '../../lib/motion'

/** Probability 0-1 on a mint/butter/rose track (bands match the API: <40 low, 40-70 medium, >70 high). */
export default function RiskMeter({ probability }) {
  const pct = Math.max(0, Math.min(1, probability)) * 100
  return (
    <div>
      <div className="meter" role="meter" aria-label="Fraud probability" aria-valuemin={0} aria-valuemax={100} aria-valuenow={Math.round(pct)}>
        <motion.span className="meter-pin" initial={{ left: '0%' }} animate={{ left: `${pct}%` }} transition={softSpring} />
      </div>
      <div className="meter-scale" aria-hidden="true">
        <span>0%</span>
        <span>40%</span>
        <span>70%</span>
        <span>100%</span>
      </div>
    </div>
  )
}
