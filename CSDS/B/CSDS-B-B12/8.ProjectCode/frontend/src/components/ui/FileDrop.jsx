import { useEffect, useId, useRef, useState } from 'react'
import { ImageUp, Trash2 } from 'lucide-react'
import { Button } from './Button'

/** Drag-and-drop (or click / keyboard) file picker with an image preview. */
export function FileDrop({ label = 'Drop a file here', hint = 'Or click to browse', accept = 'image/*', file, onFile }) {
  const inputRef = useRef(null)
  const [over, setOver] = useState(false)
  const [preview, setPreview] = useState(null)
  const id = useId()

  useEffect(() => {
    // Only real images get a preview; DICOM (.dcm) and other formats show a text placeholder instead.
    if (!file || !file.type?.startsWith('image/')) {
      setPreview(null)
      return undefined
    }
    const url = URL.createObjectURL(file)
    setPreview(url)
    return () => URL.revokeObjectURL(url)
  }, [file])

  const take = (files) => {
    const f = files && files[0]
    if (f) onFile(f)
  }

  if (file) {
    return (
      <div className="filedrop-preview">
        {preview ? (
          <img src={preview} alt="Selected file preview" />
        ) : (
          <div className="filedrop-placeholder" aria-hidden="true">
            {(file.name || '').split('.').pop().toUpperCase() || 'FILE'}
          </div>
        )}
        <div className="stack" style={{ '--gap': '6px', minWidth: 0, flex: 1 }}>
          <strong style={{ overflowWrap: 'anywhere' }}>{file.name || 'scan'}</strong>
          <span className="small muted">{Math.max(1, Math.round(file.size / 1024))} KB</span>
          <div>
            <Button size="sm" variant="ghost" icon={Trash2} onClick={() => onFile(null)}>
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
      <ImageUp size={32} aria-hidden="true" />
      <strong>{label}</strong>
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
