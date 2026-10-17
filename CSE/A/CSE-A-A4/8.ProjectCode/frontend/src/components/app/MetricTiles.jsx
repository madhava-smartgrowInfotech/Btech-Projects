import { fmtPct } from '../../lib/format'

/** metrics: {accuracy, precision, recall, f1, roc_auc} as fractions. */
export default function MetricTiles({ metrics }) {
  const items = [
    ['Accuracy', metrics.accuracy],
    ['Precision', metrics.precision],
    ['Recall', metrics.recall],
    ['F1 score', metrics.f1],
    ['ROC AUC', metrics.roc_auc],
  ].filter(([, v]) => v != null)
  return (
    <div className="metric-tiles">
      {items.map(([k, v]) => (
        <div className="metric-tile" key={k}>
          <span>{k}</span>
          <b>{fmtPct(v)}</b>
        </div>
      ))}
    </div>
  )
}
