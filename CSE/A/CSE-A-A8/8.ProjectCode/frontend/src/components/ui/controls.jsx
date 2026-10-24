import { forwardRef, useId, useRef, useState } from 'react'
import { ChevronDown, FileText, Search, UploadCloud, X } from 'lucide-react'

const cx = (...c) => c.filter(Boolean).join(' ')

export const Button = forwardRef(function Button(
  { variant = 'secondary', size, loading = false, icon: Icon, iconRight: IconRight, className, children, disabled, as: As = 'button', ...rest },
  ref,
) {
  const cls = cx('btn', variant !== 'secondary' && `btn-${variant}`, size && `btn-${size}`, className)
  const busy = loading ? { 'aria-busy': true } : {}
  const props = As === 'button' ? { type: 'button', disabled: disabled || loading } : { 'aria-disabled': disabled || undefined }
  return (
    <As ref={ref} className={cls} {...props} {...busy} {...rest}>
      {loading ? <span className="spinner" aria-hidden="true" /> : Icon ? <Icon size={size === 'sm' ? 15 : 17} aria-hidden="true" /> : null}
      {children}
      {IconRight && !loading ? <IconRight size={size === 'sm' ? 15 : 17} aria-hidden="true" /> : null}
    </As>
  )
})

export const IconButton = forwardRef(function IconButton({ icon: Icon, label, variant = 'ghost', size, className, ...rest }, ref) {
  return (
    <button
      ref={ref}
      type="button"
      aria-label={label}
      title={label}
      className={cx('btn icon-btn', `btn-${variant}`, size && `btn-${size}`, className)}
      {...rest}
    >
      <Icon size={size === 'sm' ? 16 : 18} aria-hidden="true" />
    </button>
  )
})

function Field({ id, label, hint, error, children, labelHidden }) {
  return (
    <div className="field">
      {label && (
        <label htmlFor={id} className={labelHidden ? 'sr-only' : 'field-label'}>
          {label}
        </label>
      )}
      {children}
      {error ? (
        <span id={`${id}-err`} className="field-error" role="alert">
          {error}
        </span>
      ) : hint ? (
        <span id={`${id}-hint`} className="field-hint">
          {hint}
        </span>
      ) : null}
    </div>
  )
}

const describedBy = (id, hint, error) => (error ? `${id}-err` : hint ? `${id}-hint` : undefined)

export const Input = forwardRef(function Input({ label, hint, error, labelHidden, size, mono, className, id: idProp, ...rest }, ref) {
  const auto = useId()
  const id = idProp || auto
  return (
    <Field id={id} label={label} hint={hint} error={error} labelHidden={labelHidden}>
      <input
        ref={ref}
        id={id}
        className={cx('input', size === 'lg' && 'input-lg', mono && 'mono', className)}
        aria-invalid={error ? true : undefined}
        aria-describedby={describedBy(id, hint, error)}
        {...rest}
      />
    </Field>
  )
})

export const Textarea = forwardRef(function Textarea({ label, hint, error, mono, className, id: idProp, ...rest }, ref) {
  const auto = useId()
  const id = idProp || auto
  return (
    <Field id={id} label={label} hint={hint} error={error}>
      <textarea
        ref={ref}
        id={id}
        className={cx('textarea', mono && 'mono', className)}
        aria-invalid={error ? true : undefined}
        aria-describedby={describedBy(id, hint, error)}
        {...rest}
      />
    </Field>
  )
})

export function Select({ label, hint, error, options, labelHidden, id: idProp, ...rest }) {
  const auto = useId()
  const id = idProp || auto
  return (
    <Field id={id} label={label} hint={hint} error={error} labelHidden={labelHidden}>
      <div className="select-wrap">
        <select id={id} className="select" aria-describedby={describedBy(id, hint, error)} {...rest}>
          {options.map((o) => (
            <option key={o.value} value={o.value}>
              {o.label}
            </option>
          ))}
        </select>
        <ChevronDown size={16} aria-hidden="true" />
      </div>
    </Field>
  )
}

export function Checkbox({ label, ...rest }) {
  return (
    <label className="check">
      <input type="checkbox" {...rest} />
      <span>{label}</span>
    </label>
  )
}

export function Switch({ label, ...rest }) {
  return (
    <label className="switch">
      <input type="checkbox" role="switch" {...rest} />
      <span>{label}</span>
    </label>
  )
}

export function SearchField({ value, onChange, label = 'Search', placeholder = 'Search…', className }) {
  const id = useId()
  return (
    <div className={cx('search', className)}>
      <label htmlFor={id} className="sr-only">
        {label}
      </label>
      <Search size={16} aria-hidden="true" />
      <input id={id} type="search" className="input" value={value} placeholder={placeholder} onChange={(e) => onChange(e.target.value)} />
      {value && <IconButton icon={X} label="Clear search" size="sm" className="search-clear" onClick={() => onChange('')} />}
    </div>
  )
}

// Drag-and-drop file picker. Keeps the File itself (binary uploads such as PDF / images);
// image files get a thumbnail, other files show their type and size.
export function FileDrop({ accept = '.pdf,.jpg,.jpeg,.png', label = 'Drop a file here or click to browse', hint, onFile, onReject, maxBytes = 15 * 1024 * 1024, disabled }) {
  const [drag, setDrag] = useState(false)
  const [file, setFile] = useState(null)
  const [error, setError] = useState(null)
  const inputRef = useRef(null)
  const id = useId()
  const allowed = accept.split(',').map((a) => a.trim().toLowerCase())

  const take = (f) => {
    if (!f || disabled) return
    setError(null)
    const ext = `.${f.name.split('.').pop().toLowerCase()}`
    let problem = null
    if (!allowed.includes(ext)) problem = `${f.name} is not a supported file type. Choose one of: ${allowed.join(', ')}.`
    else if (f.size === 0) problem = `${f.name} is empty. Choose a different file.`
    else if (f.size > maxBytes) problem = `${f.name} is ${(f.size / 1024 / 1024).toFixed(1)} MB - the limit is ${(maxBytes / 1024 / 1024).toFixed(0)} MB.`
    if (problem) {
      setError(problem)
      onReject?.(problem)
      return
    }
    const info = { name: f.name, size: f.size, type: f.type, file: f, preview: f.type.startsWith('image/') ? URL.createObjectURL(f) : null }
    setFile((old) => {
      if (old?.preview) URL.revokeObjectURL(old.preview)
      return info
    })
    onFile?.(info)
  }

  return (
    <div>
      <div
        className={cx('filedrop', drag && 'dragging')}
        onDragOver={(e) => {
          e.preventDefault()
          setDrag(true)
        }}
        onDragLeave={() => setDrag(false)}
        onDrop={(e) => {
          e.preventDefault()
          setDrag(false)
          take(e.dataTransfer.files?.[0])
        }}
      >
        <input
          ref={inputRef}
          id={id}
          type="file"
          accept={accept}
          disabled={disabled}
          aria-describedby={`${id}-hint`}
          onChange={(e) => {
            take(e.target.files?.[0])
            e.target.value = ''
          }}
        />
        <span className="filedrop-icon">
          <UploadCloud size={22} aria-hidden="true" />
        </span>
        <label htmlFor={id} style={{ fontWeight: 600 }}>
          {label}
        </label>
        <span id={`${id}-hint`} className="faint">
          {hint || `Accepted: ${accept}`}
        </span>
      </div>
      {error && (
        <p className="field-error" role="alert" style={{ marginTop: 8 }}>
          {error}
        </p>
      )}
      {file && (
        <div className="filedrop-preview">
          {file.preview ? (
            <img src={file.preview} alt="" style={{ width: 56, height: 56, objectFit: 'cover', borderRadius: 8, flexShrink: 0 }} />
          ) : (
            <FileText size={20} aria-hidden="true" style={{ flexShrink: 0, color: 'var(--accent)' }} />
          )}
          <div style={{ minWidth: 0, flex: 1 }}>
            <div className="row" style={{ justifyContent: 'space-between' }}>
              <strong className="break">{file.name}</strong>
              <span className="faint">{(file.size / 1024).toFixed(1)} KB</span>
            </div>
            <span className="faint">{file.type || 'unknown type'}</span>
          </div>
          <IconButton
            icon={X}
            size="sm"
            label="Remove file"
            disabled={disabled}
            onClick={() => {
              if (file.preview) URL.revokeObjectURL(file.preview)
              setFile(null)
              onFile?.(null)
            }}
          />
        </div>
      )}
    </div>
  )
}
