import { fmtInt } from '../../lib/format'

/** matrix: [[TN, FP], [FN, TP]] as returned by the API (labels 0 = legitimate, 1 = fraud). */
export default function ConfusionMatrix({ matrix }) {
  if (!matrix || matrix.length < 2) return null
  const [[tn, fp], [fn, tp]] = matrix
  return (
    <div className="confmat" role="table" aria-label="Confusion matrix">
      <span />
      <span className="h">Predicted legitimate</span>
      <span className="h">Predicted fraud</span>
      <span className="h">Actually legitimate</span>
      <div className="cell good"><b>{fmtInt(tn)}</b>true negative</div>
      <div className="cell bad"><b>{fmtInt(fp)}</b>false alarm</div>
      <span className="h">Actually fraud</span>
      <div className="cell bad"><b>{fmtInt(fn)}</b>missed fraud</div>
      <div className="cell good"><b>{fmtInt(tp)}</b>caught fraud</div>
    </div>
  )
}
