import { forwardRef, useId } from 'react'
import { Check, ChevronDown, Search } from 'lucide-react'

export function Field({ label, hint, error, htmlFor, children, extra }) {
  return (
    <div className="field">
      {label && (
        <label className="field-label" htmlFor={htmlFor}>
          {label}
          {extra}
        </label>
      )}
      {children}
      {error ? (
        <span className="field-error" role="alert">
          {error}
        </span>
      ) : (
        hint && <span className="field-hint">{hint}</span>
      )}
    </div>
  )
}

export const Input = forwardRef(function Input({ label, hint, error, id, extra, className = '', ...rest }, ref) {
  const auto = useId()
  const fid = id || auto
  return (
    <Field label={label} hint={hint} error={error} htmlFor={fid} extra={extra}>
      <input ref={ref} id={fid} className={`input ${className}`} aria-invalid={error ? 'true' : undefined} {...rest} />
    </Field>
  )
})

export const Textarea = forwardRef(function Textarea({ label, hint, error, id, ...rest }, ref) {
  const auto = useId()
  const fid = id || auto
  return (
    <Field label={label} hint={hint} error={error} htmlFor={fid}>
      <textarea ref={ref} id={fid} className="textarea" aria-invalid={error ? 'true' : undefined} {...rest} />
    </Field>
  )
})

export function Select({ label, hint, error, id, options = [], children, ...rest }) {
  const auto = useId()
  const fid = id || auto
  return (
    <Field label={label} hint={hint} error={error} htmlFor={fid}>
      <div className="select-wrap">
        <select id={fid} className="select" {...rest}>
          {children ||
            options.map((o) => (
              <option key={o.value} value={o.value}>
                {o.label}
              </option>
            ))}
        </select>
        <ChevronDown size={18} aria-hidden="true" />
      </div>
    </Field>
  )
}

export function Checkbox({ label, checked, onChange, ...rest }) {
  return (
    <label className="check">
      <input type="checkbox" checked={checked} onChange={(e) => onChange?.(e.target.checked)} {...rest} />
      <span className="check-box" aria-hidden="true">
        {checked && <Check size={16} strokeWidth={3} />}
      </span>
      {label}
    </label>
  )
}

export function Switch({ label, checked, onChange, ...rest }) {
  return (
    <label className="switch">
      <input type="checkbox" role="switch" checked={checked} onChange={(e) => onChange?.(e.target.checked)} {...rest} />
      <span className="switch-track" aria-hidden="true">
        <span className="switch-thumb" />
      </span>
      {label}
    </label>
  )
}

export function SearchField({ value, onChange, label = 'Search', placeholder = 'Search…', ...rest }) {
  const id = useId()
  return (
    <div className="field" style={{ minWidth: 0, flex: '1 1 220px', maxWidth: 360 }}>
      <label htmlFor={id} className="sr-only">
        {label}
      </label>
      <div className="input-group">
        <Search size={18} aria-hidden="true" />
        <input
          id={id}
          type="search"
          className="input"
          value={value}
          placeholder={placeholder}
          onChange={(e) => onChange(e.target.value)}
          {...rest}
        />
      </div>
    </div>
  )
}
