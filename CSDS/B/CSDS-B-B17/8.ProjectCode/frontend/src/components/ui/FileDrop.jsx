import { useId, useRef, useState } from 'react'
import { FileAudio, Trash2, Upload } from 'lucide-react'
import { Button } from './Button'

const size = (f) => (f.size >= 1048576 ? `${(f.size / 1048576).toFixed(1)} MB` : `${Math.max(1, Math.round(f.size / 1024))} KB`)

/**
 * Drag-and-drop (or click / keyboard) file picker, single or multiple files.
 * Controlled: pass `files` (array) and `onFiles(array)`.
 */
export function FileDrop({
  label = 'Drop recordings here',
  hint = 'WAV, MP3, FLAC, OGG, M4A, WEBM · or click to browse',
  accept = 'audio/*,.wav,.mp3,.flac,.ogg,.webm,.m4a,.aac,.opus',
  multiple = false,
  files = [],
  onFiles,
}) {
  const inputRef = useRef(null)
  const [over, setOver] = useState(false)
  const id = useId()

  const take = (list) => {
    const arr = [...(list || [])]
    if (arr.length) onFiles(multiple ? arr : arr.slice(0, 1))
  }

  if (files.length) {
    return (
      <div className="filedrop-preview" style={{ alignItems: 'flex-start' }}>
        <FileAudio size={28} aria-hidden="true" style={{ flex: 'none' }} />
        <div className="stack" style={{ '--gap': '6px', minWidth: 0, flex: 1 }}>
          <ul className="file-list">
            {files.map((f) => (
              <li key={f.name + f.size}>
                <strong style={{ overflowWrap: 'anywhere' }}>{f.name}</strong> <span className="small muted mono">{size(f)}</span>
              </li>
            ))}
          </ul>
          <div>
            <Button size="sm" variant="ghost" icon={Trash2} onClick={() => onFiles([])}>
              {files.length > 1 ? 'Remove all' : 'Remove'}
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
      <Upload size={32} aria-hidden="true" />
      <strong>{label}</strong>
      <span id={id} className="small">
        {hint}
      </span>
      <input
        ref={inputRef}
        type="file"
        accept={accept}
        multiple={multiple}
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
