import { useId, useRef, useState } from 'react'
import { FileSpreadsheet, Trash2 } from 'lucide-react'
import { Button } from './Button'

/** Drag-and-drop (or click / keyboard) file picker. Shows the chosen file's name and size. */
export function FileDrop({ label = 'Drop a file here', hint = 'or click to browse', accept = '.csv,text/csv', file, onFile, icon: Icon = FileSpreadsheet, required }) {
  const inputRef = useRef(null)
  const [over, setOver] = useState(false)
  const id = useId()

  const take = (files) => {
    const f = files && files[0]
    if (f) onFile(f)
  }

  if (file) {
    return (
      <div className="filedrop-preview">
        <div className="feature-icon" style={{ margin: 0, flex: 'none' }} aria-hidden="true">
          <Icon size={26} />
        </div>
        <div className="stack" style={{ '--gap': '6px', minWidth: 0, flex: 1 }}>
          <strong style={{ overflowWrap: 'anywhere' }}>{file.name}</strong>
          <span className="small muted">{file.size >= 1048576 ? `${(file.size / 1048576).toFixed(1)} MB` : `${Math.max(1, Math.round(file.size / 1024))} KB`}</span>
          <div>
            <Button size="sm" variant="ghost" icon={Trash2} onClick={() => onFile(null)} aria-label={`Remove ${file.name}`}>
              Remove
            </Button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div
      className={`filedrop ${over ? 'is-over' : ''}`}
      role="button"
      tabIndex={0}
      aria-describedby={id}
      onClick={() => inputRef.current?.click()}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault()
          inputRef.current?.click()
        }
      }}
      onDragOver={(e) => {
        e.preventDefault()
        setOver(true)
      }}
      onDragLeave={() => setOver(false)}
      onDrop={(e) => {
        e.preventDefault()
        setOver(false)
        take(e.dataTransfer.files)
      }}
    >
      <Icon size={32} aria-hidden="true" />
      <strong>
        {label}
        {required && <span className="sr-only"> (required)</span>}
      </strong>
      <span id={id} className="small">
        {hint}
      </span>
      <input
        ref={inputRef}
        type="file"
        accept={accept}
        hidden
        aria-label={label}
        onChange={(e) => {
          take(e.target.files)
          e.target.value = ''
        }}
      />
    </div>
  )
}
