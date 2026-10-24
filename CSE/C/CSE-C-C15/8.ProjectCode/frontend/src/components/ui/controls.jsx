import { Check, ChevronDown, FileUp, Loader2, Search, X } from 'lucide-react'
import { forwardRef, useEffect, useId, useRef, useState } from 'react'
import { Tooltip } from './feedback'

const BTN = 'relative inline-flex items-center justify-center gap-2 rounded-[6px] font-medium whitespace-nowrap select-none transition-[background-color,border-color,color,box-shadow,filter] duration-150 disabled:opacity-50 disabled:cursor-not-allowed'
const VARIANTS = {
  primary: 'bg-ok text-on-ok hover:brightness-110 shadow-[0_0_0_1px_var(--ok),0_0_22px_-8px_var(--ok)]',
  secondary: 'bg-panel-2 text-fg border border-line-strong hover:border-ok/60 hover:text-ok',
  ghost: 'text-muted hover:text-fg hover:bg-panel-2',
  danger: 'bg-alert/10 text-alert border border-alert/40 hover:bg-alert hover:text-on-ok',
}
const SIZES = { sm: 'h-8 px-3 text-xs', md: 'h-9 px-3.5 text-sm', lg: 'h-11 px-5 text-sm' }

export const Button = forwardRef(function Button(
  { variant = 'primary', size = 'md', loading = false, icon: Icon, children, className = '', disabled, type = 'button', ...props }, ref) {
  return (
    <button ref={ref} type={type} className={`${BTN} ${VARIANTS[variant]} ${SIZES[size]} ${className}`}
      disabled={disabled || loading} aria-busy={loading || undefined} {...props}>
      {loading ? <Loader2 size={size === 'sm' ? 14 : 16} className="animate-spin" aria-hidden="true" /> : Icon && <Icon size={size === 'sm' ? 14 : 16} aria-hidden="true" />}
      {children}
    </button>
  )
})

export const IconButton = forwardRef(function IconButton({ label, icon: Icon, size = 'md', variant = 'ghost', tooltip = true, tooltipAlign = 'center', className = '', ...props }, ref) {
  const dim = size === 'sm' ? 'h-8 w-8' : 'h-9 w-9'
  const btn = (
    <button ref={ref} type="button" aria-label={label} className={`${BTN} ${VARIANTS[variant]} ${dim} ${className}`} {...props}>
      <Icon size={size === 'sm' ? 15 : 17} aria-hidden="true" />
    </button>
  )
  return tooltip ? <Tooltip content={label} align={tooltipAlign}>{btn}</Tooltip> : btn
})

const FIELD = 'w-full rounded-[6px] border border-line-strong bg-panel-2 px-3 text-sm text-fg placeholder:text-dim transition-colors hover:border-ok/40 focus:border-ok focus:outline-none focus:ring-2 focus:ring-ok/20 disabled:opacity-60 aria-[invalid=true]:border-alert'

export function Label({ htmlFor, children, className = '' }) {
  return <label htmlFor={htmlFor} className={`block font-mono text-[11px] uppercase tracking-[0.12em] text-muted ${className}`}>{children}</label>
}

function Help({ id, error, hint }) {
  if (error) return <p id={id} className="mt-1 text-xs text-alert">{error}</p>
  if (hint) return <p id={id} className="mt-1 text-xs text-dim">{hint}</p>
  return null
}

export const Input = forwardRef(function Input({ label, hint, error, className = '', id, ...props }, ref) {
  const auto = useId()
  const fid = id || auto
  return (
    <div className={className}>
      {label && <Label htmlFor={fid} className="mb-1.5">{label}</Label>}
      <input ref={ref} id={fid} className={`${FIELD} h-10 font-mono`} aria-invalid={!!error || undefined}
        aria-describedby={error || hint ? `${fid}-help` : undefined} {...props} />
      <Help id={`${fid}-help`} error={error} hint={hint} />
    </div>
  )
})

export function Textarea({ label, hint, error, className = '', id, rows = 4, ...props }) {
  const auto = useId()
  const fid = id || auto
  return (
    <div className={className}>
      {label && <Label htmlFor={fid} className="mb-1.5">{label}</Label>}
      <textarea id={fid} rows={rows} className={`${FIELD} py-2 leading-relaxed`} aria-invalid={!!error || undefined}
        aria-describedby={error || hint ? `${fid}-help` : undefined} {...props} />
      <Help id={`${fid}-help`} error={error} hint={hint} />
    </div>
  )
}

export function Select({ label, srLabel, options, className = '', id, ...props }) {
  const auto = useId()
  const fid = id || auto
  return (
    <div className={className}>
      {label && <Label htmlFor={fid} className="mb-1.5">{label}</Label>}
      <div className="relative">
        <select id={fid} aria-label={!label ? srLabel : undefined} className={`${FIELD} h-10 appearance-none pr-8 cursor-pointer`} {...props}>
          {options.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
        </select>
        <ChevronDown size={15} className="pointer-events-none absolute right-2.5 top-1/2 -translate-y-1/2 text-dim" aria-hidden="true" />
      </div>
    </div>
  )
}

export function Checkbox({ label, checked, onChange, className = '', ...props }) {
  const id = useId()
  return (
    <label htmlFor={id} className={`inline-flex cursor-pointer items-center gap-2 text-sm text-fg ${className}`}>
      <span className="relative inline-flex h-4 w-4 items-center justify-center">
        <input id={id} type="checkbox" checked={checked} onChange={(e) => onChange?.(e.target.checked)}
          className="peer absolute inset-0 m-0 cursor-pointer appearance-none rounded-[4px] border border-line-strong bg-panel-2 checked:border-ok checked:bg-ok" {...props} />
        <Check size={12} strokeWidth={3} className="pointer-events-none relative text-on-ok opacity-0 peer-checked:opacity-100" aria-hidden="true" />
      </span>
      {label}
    </label>
  )
}

export function Switch({ checked, onChange, label, className = '' }) {
  return (
    <button type="button" role="switch" aria-checked={checked} onClick={() => onChange(!checked)}
      className={`inline-flex items-center gap-2 text-xs font-mono uppercase tracking-wider text-muted hover:text-fg ${className}`}>
      <span className={`relative h-[18px] w-8 rounded-full border transition-colors ${checked ? 'border-ok bg-ok/25' : 'border-line-strong bg-panel-2'}`}>
        <span className={`absolute top-[2px] h-3 w-3 rounded-full transition-all ${checked ? 'left-[16px] bg-ok' : 'left-[2px] bg-dim'}`} />
      </span>
      {label}
    </button>
  )
}

export const SearchField = forwardRef(function SearchField({ value, onChange, placeholder = 'Search', label = 'Search', shortcut, className = '', ...props }, ref) {
  return (
    <div className={`relative ${className}`}>
      <Search size={15} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-dim" aria-hidden="true" />
      <input ref={ref} type="search" aria-label={label} value={value} onChange={(e) => onChange(e.target.value)} placeholder={placeholder}
        className={`${FIELD} h-10 pl-9 pr-16 [&::-webkit-search-cancel-button]:hidden`} {...props} />
      <div className="absolute right-2 top-1/2 flex -translate-y-1/2 items-center gap-1">
        {value && (
          <button type="button" onClick={() => onChange('')} aria-label="Clear search" className="rounded p-1 text-dim hover:text-fg"><X size={14} /></button>
        )}
        {shortcut && !value && <kbd className="rounded border border-line-strong px-1.5 font-mono text-[10px] text-dim">{shortcut}</kbd>}
      </div>
    </div>
  )
})

// Drag-and-drop file picker with previews (images get a thumbnail).
export function FileDrop({ label = 'Drop files here', accept, multiple = true, onFiles, className = '' }) {
  const [files, setFiles] = useState([])
  const [over, setOver] = useState(false)
  const input = useRef(null)
  const id = useId()
  useEffect(() => () => files.forEach((f) => f.url && URL.revokeObjectURL(f.url)), [files])
  function take(list) {
    const next = Array.from(list).map((file) => ({ file, url: file.type.startsWith('image/') ? URL.createObjectURL(file) : null }))
    setFiles(next)
    onFiles?.(next.map((f) => f.file))
  }
  return (
    <div className={className}>
      <label htmlFor={id}
        onDragOver={(e) => { e.preventDefault(); setOver(true) }} onDragLeave={() => setOver(false)}
        onDrop={(e) => { e.preventDefault(); setOver(false); take(e.dataTransfer.files) }}
        className={`flex cursor-pointer flex-col items-center justify-center gap-2 rounded-[6px] border border-dashed p-6 text-center text-sm transition-colors ${over ? 'border-ok bg-ok/5 text-ok' : 'border-line-strong text-muted hover:border-ok/50'}`}>
        <FileUp size={20} aria-hidden="true" />
        <span>{label}</span>
        <span className="font-mono text-[11px] text-dim">or click to browse</span>
        <input ref={input} id={id} type="file" accept={accept} multiple={multiple} className="sr-only" onChange={(e) => take(e.target.files)} />
      </label>
      {files.length > 0 && (
        <ul className="mt-2 space-y-1">
          {files.map(({ file, url }) => (
            <li key={file.name} className="flex items-center gap-2 rounded border border-line bg-panel-2 px-2 py-1.5 text-xs">
              {url ? <img src={url} alt="" className="h-8 w-8 rounded object-cover" /> : <FileUp size={14} className="text-dim" />}
              <span className="flex-1 truncate">{file.name}</span>
              <span className="font-mono text-dim">{(file.size / 1024).toFixed(1)} KB</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
