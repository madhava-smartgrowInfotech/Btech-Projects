import { useId } from 'react'
import { motion } from 'framer-motion'
import { Check, Search, X } from 'lucide-react'
import { spring } from '../../lib/motion'

export function Field({ label, hint, error, id, children }) {
  return (
    <div className="field">
      {label && (
        <label className="field-label" htmlFor={id}>
          {label}
        </label>
      )}
      {children}
      {error ? (
        <span className="field-error" id={`${id}-err`} role="alert">
          {error}
        </span>
      ) : (
        hint && (
          <span className="field-hint" id={`${id}-hint`}>
            {hint}
          </span>
        )
      )}
    </div>
  )
}

function describedBy(id, hint, error) {
  return error ? `${id}-err` : hint ? `${id}-hint` : undefined
}

export function Input({ label, hint, error, id, className = '', ...rest }) {
  const auto = useId()
  const fid = id || auto
  return (
    <Field label={label} hint={hint} error={error} id={fid}>
      <input
        id={fid}
        className={`input ${className}`}
        aria-invalid={error ? 'true' : undefined}
        aria-describedby={describedBy(fid, hint, error)}
        {...rest}
      />
    </Field>
  )
}

export function Textarea({ label, hint, error, id, className = '', ...rest }) {
  const auto = useId()
  const fid = id || auto
  return (
    <Field label={label} hint={hint} error={error} id={fid}>
      <textarea
        id={fid}
        className={`textarea ${className}`}
        aria-invalid={error ? 'true' : undefined}
        aria-describedby={describedBy(fid, hint, error)}
        {...rest}
      />
    </Field>
  )
}

/** options: [{value, label}] or strings */
export function Select({ label, hint, error, id, options = [], className = '', ...rest }) {
  const auto = useId()
  const fid = id || auto
  return (
    <Field label={label} hint={hint} error={error} id={fid}>
      <select id={fid} className={`select ${className}`} aria-describedby={describedBy(fid, hint, error)} {...rest}>
        {options.map((o) => {
          const opt = typeof o === 'string' ? { value: o, label: o } : o
          return (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          )
        })}
      </select>
    </Field>
  )
}

export function Checkbox({ label, checked, onChange, ...rest }) {
  return (
    <label className="check">
      <input type="checkbox" checked={checked} onChange={(e) => onChange?.(e.target.checked)} {...rest} />
      <motion.span className="check-box" animate={{ scale: checked ? [1, 1.18, 1] : 1 }} transition={spring}>
        {checked && <Check size={16} strokeWidth={3} aria-hidden="true" />}
      </motion.span>
      {label}
    </label>
  )
}

export function Switch({ checked, onChange, label, description, id }) {
  return (
    <button type="button" role="switch" id={id} aria-checked={checked} className="switch" onClick={() => onChange?.(!checked)}>
      <span className="switch-track">
        <motion.span layout className="switch-thumb" transition={spring} />
      </span>
      {(label || description) && (
        <span className="switch-text">
          {label}
          {description && <small>{description}</small>}
        </span>
      )}
    </button>
  )
}

export function SearchField({ value, onChange, placeholder = 'Search', label = 'Search', className = '' }) {
  const id = useId()
  return (
    <div className={`input-wrap ${className}`}>
      <label htmlFor={id} className="sr-only">
        {label}
      </label>
      <Search size={18} aria-hidden="true" />
      <input id={id} type="search" className="input" value={value} placeholder={placeholder} onChange={(e) => onChange(e.target.value)} />
      {value && (
        <button type="button" className="icon-btn plain clear" aria-label="Clear search" onClick={() => onChange('')} style={{ width: 38, height: 38 }}>
          <X size={16} aria-hidden="true" />
        </button>
      )}
    </div>
  )
}

/** Pill radio group. options: [{value, label, icon}] */
export function Segmented({ value, onChange, options, label, name }) {
  const lid = useId()
  return (
    <div className="field">
      {label && (
        <span className="field-label" id={lid}>
          {label}
        </span>
      )}
      <div className="segmented" role="radiogroup" aria-labelledby={label ? lid : undefined}>
        {options.map((o) => {
          const on = o.value === value
          const Icon = o.icon
          return (
            <motion.button
              key={o.value}
              type="button"
              role="radio"
              aria-checked={on}
              onClick={() => onChange(o.value)}
              whileTap={{ scale: 0.95 }}
              transition={spring}
            >
              {on && <motion.span layoutId={`seg-${name}`} className="seg-pill" transition={spring} />}
              <span>
                {Icon && <Icon size={16} aria-hidden="true" />}
                {o.label}
              </span>
            </motion.button>
          )
        })}
      </div>
    </div>
  )
}
