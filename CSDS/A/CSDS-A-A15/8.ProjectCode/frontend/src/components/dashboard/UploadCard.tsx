import { AnimatePresence, motion } from 'framer-motion'
import { ImageIcon, Loader2, ScanSearch, UploadCloud } from 'lucide-react'
import { useCallback, useState } from 'react'
import { useDropzone } from 'react-dropzone'
import { useNavigate } from 'react-router-dom'
import { Button } from '@/components/ui/Button'
import { Input, Label } from '@/components/ui/Input'
import { inspectionsApi } from '@/lib/api'

export function UploadCard() {
  const navigate = useNavigate()
  const [file, setFile] = useState<File | null>(null)
  const [preview, setPreview] = useState<string | null>(null)
  const [assetName, setAssetName] = useState('')
  const [analyzing, setAnalyzing] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const onDrop = useCallback((accepted: File[]) => {
    const f = accepted[0]
    if (!f) return
    setFile(f)
    setPreview(URL.createObjectURL(f))
    setError(null)
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'image/jpeg': [], 'image/png': [], 'image/webp': [], 'image/bmp': [] },
    maxFiles: 1,
  })

  async function handleAnalyze() {
    if (!file) return
    setAnalyzing(true)
    setError(null)
    try {
      const result = await inspectionsApi.create(file, assetName || 'Unnamed Asset')
      navigate(`/app/inspections/${result.id}`)
    } catch {
      setError('Analysis failed. Please try a different image.')
      setAnalyzing(false)
    }
  }

  return (
    <div className="space-y-4">
      <div
        {...getRootProps()}
        className={`relative rounded-2xl border-2 border-dashed p-10 text-center cursor-pointer transition-colors ${
          isDragActive ? 'border-cyan-400 bg-cyan-400/5' : 'border-white/15 hover:border-white/25'
        }`}
      >
        <input {...getInputProps()} />
        <AnimatePresence mode="wait">
          {preview ? (
            <motion.div
              key="preview"
              initial={{ opacity: 0, scale: 0.96 }}
              animate={{ opacity: 1, scale: 1 }}
              className="flex flex-col items-center gap-3"
            >
              <img src={preview} alt="Selected upload" className="h-40 w-40 object-cover rounded-xl ring-1 ring-white/10" />
              <p className="text-sm text-slate-400">{file?.name}</p>
            </motion.div>
          ) : (
            <motion.div
              key="empty"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="flex flex-col items-center gap-3"
            >
              <div className="h-14 w-14 rounded-2xl bg-white/5 flex items-center justify-center">
                <UploadCloud className="h-6 w-6 text-cyan-400" />
              </div>
              <div>
                <p className="text-white font-medium">Drop a surface image here</p>
                <p className="text-sm text-slate-500 mt-1">or click to browse — JPG, PNG, WEBP, BMP</p>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {file && (
        <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="space-y-3">
          <div>
            <Label htmlFor="asset-name">Asset / line reference (optional)</Label>
            <Input
              id="asset-name"
              placeholder="e.g. Coil Line 3 — Batch 214"
              value={assetName}
              onChange={(e) => setAssetName(e.target.value)}
            />
          </div>

          {error && <p className="text-sm text-rose-400">{error}</p>}

          <Button onClick={handleAnalyze} disabled={analyzing} className="w-full">
            {analyzing ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                Analyzing surface…
              </>
            ) : (
              <>
                <ScanSearch className="h-4 w-4" />
                Run Inspection
              </>
            )}
          </Button>
        </motion.div>
      )}

      {!file && (
        <div className="flex items-center gap-2 text-xs text-slate-500">
          <ImageIcon className="h-3.5 w-3.5" />
          Best results with well-lit, close-up surface photos.
        </div>
      )}
    </div>
  )
}
