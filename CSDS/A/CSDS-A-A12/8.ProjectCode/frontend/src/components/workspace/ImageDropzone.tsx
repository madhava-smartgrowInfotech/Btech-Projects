import { useCallback, useState } from 'react'
import { useDropzone } from 'react-dropzone'
import { motion, AnimatePresence } from 'framer-motion'
import { ImagePlus, X } from 'lucide-react'

interface ImageDropzoneProps {
  onFileChange: (file: File | null) => void
}

export function ImageDropzone({ onFileChange }: ImageDropzoneProps) {
  const [preview, setPreview] = useState<string | null>(null)

  const onDrop = useCallback(
    (accepted: File[]) => {
      const file = accepted[0]
      if (!file) return
      onFileChange(file)
      setPreview(URL.createObjectURL(file))
    },
    [onFileChange]
  )

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'image/*': ['.png', '.jpg', '.jpeg', '.webp'] },
    maxFiles: 1,
  })

  function clear(e: React.MouseEvent) {
    e.stopPropagation()
    setPreview(null)
    onFileChange(null)
  }

  return (
    <div
      {...getRootProps()}
      className={`relative rounded-2xl border-2 border-dashed cursor-pointer transition-colors overflow-hidden ${
        isDragActive ? 'border-emerald-400 bg-emerald-500/5' : 'border-[var(--color-border)] hover:border-emerald-500/40'
      } ${preview ? 'h-64' : 'h-52'}`}
    >
      <input {...getInputProps()} />
      <AnimatePresence mode="wait">
        {preview ? (
          <motion.div
            key="preview"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="relative w-full h-full"
          >
            <img src={preview} alt="Seed sample" className="w-full h-full object-cover" />
            <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent" />
            <button
              onClick={clear}
              className="absolute top-3 right-3 w-8 h-8 rounded-full bg-black/50 backdrop-blur flex items-center justify-center text-white hover:bg-black/70 transition-colors"
            >
              <X size={15} />
            </button>
            <span className="absolute bottom-3 left-3 text-xs text-white/90 font-medium">
              Click or drop to replace
            </span>
          </motion.div>
        ) : (
          <motion.div
            key="empty"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="flex flex-col items-center justify-center h-full text-center px-6"
          >
            <div className="w-12 h-12 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center mb-3">
              <ImagePlus size={20} className="text-emerald-300" />
            </div>
            <p className="text-sm font-medium text-[var(--color-text)]">
              {isDragActive ? 'Drop the seed image here' : 'Drag & drop a seed image'}
            </p>
            <p className="text-xs text-[var(--color-text-faint)] mt-1">or click to browse · PNG, JPG, WEBP</p>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
