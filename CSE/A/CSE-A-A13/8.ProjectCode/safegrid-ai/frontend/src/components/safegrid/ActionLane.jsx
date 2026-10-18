import { ArrowRight } from 'lucide-react'
import { ACTION_LABEL, CHECK_LABEL, kw } from '../../lib/format'
import { ShieldBadge, SourceBadge } from './badges'

export function Checks({ checks = [] }) {
  return (
    <div className="checks" role="list" aria-label="Shield checks">
      {checks.map((c) => {
        const state = c.passed === null ? 'skip' : c.passed ? 'pass' : 'fail'
        const word = c.passed === null ? 'not evaluated' : c.passed ? 'passed' : 'failed'
        return (
          <span key={c.name} role="listitem" className={`check-chip ${state}`} title={word}>
            {CHECK_LABEL[c.name] || c.name}
            <span className="sr-only"> {word}</span>
          </span>
        )
      })}
    </div>
  )
}

/** AI proposal -> Safety Shield decision -> action executed on the grid. Always shows all three. */
export default function ActionLane({ record, showChecks = true }) {
  const { proposal, shield, decision_source: source, fallback_reason: fallback } = record
  const executed = shield.validated_action
  const corrections = (shield.corrections || []).filter((c) => c.field === 'power_kw')
  return (
    <div>
      <div className="lane">
        <div className="lane-cell proposed">
          <div className="lane-who">
            AI proposal <SourceBadge source={source} />
          </div>
          <div className="lane-big">{kw(proposal.power_kw)}</div>
          <div>{ACTION_LABEL[proposal.action_type] || proposal.action_type}</div>
          <small>confidence {(proposal.confidence * 100).toFixed(0)}%</small>
        </div>
        <ArrowRight className="lane-arrow" size={20} aria-hidden="true" />
        <div className={`lane-cell ${shield.status}`}>
          <div className="lane-who">Safety shield</div>
          <div className="lane-big">
            <ShieldBadge status={shield.status} />
          </div>
          <div>{shield.violations.length ? `${shield.violations.length} violation${shield.violations.length > 1 ? 's' : ''} found` : 'No violations'}</div>
          {corrections.map((c) => (
            <small key={c.field}>
              scaled {kw(c.from)} to {kw(c.to)}
            </small>
          ))}
        </div>
        <ArrowRight className="lane-arrow" size={20} aria-hidden="true" />
        <div className="lane-cell executed">
          <div className="lane-who">Executed on grid</div>
          <div className="lane-big">{kw(executed ? executed.power_kw : 0)}</div>
          <div>{executed ? ACTION_LABEL[executed.action_type] || executed.action_type : 'Nothing executed'}</div>
        </div>
      </div>
      {fallback && (
        <p className="faint" style={{ marginTop: 10 }}>
          LLM unavailable or invalid, fallback used: <span className="mono">{fallback}</span>
        </p>
      )}
      {shield.violations.length > 0 && (
        <div className="viol-list">
          {shield.violations.map((v, i) => (
            <div className="viol" key={i}>
              <strong className="mono">{v.code}</strong> at {v.component}: {v.message}
              <span className="faint">
                {' '}
                (requested {Number(v.requested).toFixed(2)} {v.unit}, allowed {Number(v.allowed).toFixed(2)} {v.unit})
              </span>
            </div>
          ))}
        </div>
      )}
      {showChecks && shield.checks && (
        <div style={{ marginTop: 12 }}>
          <Checks checks={shield.checks} />
        </div>
      )}
    </div>
  )
}
