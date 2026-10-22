import { Input } from './ui/controls'
import { FIELDS } from '../lib/profile'

// Grid of labelled numeric inputs for the student-profile keys given.
export default function ProfileFields({ keys, values, errors, onChange }) {
  return (
    <>
      {keys.map((k) => {
        const f = FIELDS[k]
        return (
          <Input key={k} id={`f-${k}`} label={f.label} type="number" inputMode="decimal" min={f.min} max={f.max} step={f.step}
            value={values[k]} onChange={(e) => onChange(k, e.target.value)} error={errors[k]} hint={errors[k] ? undefined : f.hint} />
        )
      })}
    </>
  )
}
