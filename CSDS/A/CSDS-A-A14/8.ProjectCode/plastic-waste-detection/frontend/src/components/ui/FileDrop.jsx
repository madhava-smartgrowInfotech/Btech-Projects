import { useId, useRef, useState } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import { FileText, UploadCloud, X } from 'lucide-react'
import { softSpring } from '../../lib/motion'

/** Drag-and-drop file picker with a preview list. */
export function FileDrop({ accept, multiple = false, onFiles, label = 'Drop a file here or click to browse', hint }) {
  const [over, setOver] = useState(false)
  const [files, setFiles] = useState([])
  const input = useRef(null)
  const id = useId()
  const take = (list) => {
    const arr = Array.from(list || [])
    if (!arr.length) return
    const next = multiple ? [...files, ...arr] : arr.slice(0, 1)
    setFiles(next)
    onFiles?.(next)
  }
  const remove = (i) => {
    const next = files.filter((_, j) => j !== i)
    setFiles(next)
    onFiles?.(next)
  }
  return (
    <div>
      <motion.div
        role="button"
        tabIndex={0}
        aria-describedby={hint ? id : undefined}
        className={`filedrop ${over ? 'over' : ''}`}
        onClick={() => input.current?.click()}
        onKeyDown={(e) => (e.key === 'Enter' || e.key === ' ') && (e.preventDefault(), input.current?.click())}
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
        animate={{ scale: over ? 1.02 : 1 }}
        transition={softSpring}
      >
        <UploadCloud size={30} aria-hidden="true" style={{ color: 'var(--lavender-ink)' }} />
        <p style={{ fontWeight: 600, marginTop: 8 }}>{label}</p>
        {hint && (
          <p className="small muted" id={id}>
            {hint}
          </p>
        )}
        <input ref={input} type="file" hidden accept={accept} multiple={multiple} onChange={(e) => take(e.target.files)} />
      </motion.div>
      <ul className="filedrop-list">
        <AnimatePresence>
          {files.map((f, i) => (
            <motion.li key={f.name + i} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, x: 20 }} transition={softSpring}>
              <FileText size={18} aria-hidden="true" />
              <span style={{ flex: 1, minWidth: 0, overflow: 'hidden', textOverflow: 'ellipsis' }}>{f.name}</span>
              <span className="tiny muted">{(f.size / 1024).toFixed(1)} KB</span>
              <button type="button" className="icon-btn plain" style={{ width: 34, height: 34 }} aria-label={`Remove ${f.name}`} onClick={() => remove(i)}>
                <X size={16} aria-hidden="true" />
              </button>
            </motion.li>
          ))}
        </AnimatePresence>
      </ul>
    </div>
  )
}
