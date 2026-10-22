import { useState } from 'react'
import { ShieldCheck } from 'lucide-react'
import { Badge, Skeleton } from './ui'

export const PROFILE_TONE = { Established: 'mint', Developing: 'sky', Emerging: 'peach' }
export const RISK_TONE = { Low: 'mint', Moderate: 'peach', High: 'rose' }

export function ProfileBadge({ profile }) {
  return <Badge tone={PROFILE_TONE[profile] || 'neutral'} dot>{profile}</Badge>
}
export function RiskBadge({ risk }) {
  return <Badge tone={RISK_TONE[risk] || 'neutral'}>Risk: {risk}</Badge>
}

export function Disclaimer({ children }) {
  return (
    <p className="small muted row" style={{ '--gap': '8px', alignItems: 'flex-start', flexWrap: 'nowrap' }}>
      <ShieldCheck size={16} aria-hidden="true" style={{ flex: 'none', marginTop: 3 }} />
      <span>{children || 'Informational model-based estimates, not professional financial advice, a credit decision or a guarantee of any outcome.'}</span>
    </p>
  )
}

/** Renders a human label for the API's raw field names. */
export const FIELD_LABELS = {
  age: 'Age',
  workclass: 'Employment type',
  education: 'Education',
  'education-num': 'Years of education',
  'marital-status': 'Marital status',
  occupation: 'Occupation',
  relationship: 'Household relationship',
  race: 'Race',
  sex: 'Sex',
  'native-country': 'Country',
  'capital-gain': 'Investment gains ($)',
  'capital-loss': 'Investment losses ($)',
  'hours-per-week': 'Hours per week',
}

/** Server-rendered chart image (matplotlib PNG) with a skeleton and a clear failure message. */
export function ArtifactImage({ name, alt }) {
  const [state, setState] = useState('loading')
  return (
    <div style={{ background: '#fff', borderRadius: 18, padding: 8, position: 'relative', minHeight: state === 'loading' ? 220 : 0 }}>
      {state === 'loading' && <Skeleton height={220} radius={14} style={{ position: 'absolute', inset: 8, width: 'auto' }} />}
      {state === 'error' ? (
        <p className="small" style={{ color: '#4E5566', padding: 24 }}>Chart unavailable. Run <code>python scripts/train.py</code> to regenerate it.</p>
      ) : (
        <img
          src={`/artifacts/${name}`}
          alt={alt}
          loading="lazy"
          style={{ display: 'block', width: '100%', height: 'auto', opacity: state === 'loading' ? 0 : 1, transition: 'opacity .3s' }}
          onLoad={() => setState('ok')}
          onError={() => setState('error')}
        />
      )}
    </div>
  )
}
