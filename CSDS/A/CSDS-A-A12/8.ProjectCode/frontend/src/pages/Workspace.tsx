import { useState } from 'react'
import { motion } from 'framer-motion'
import { ScanLine } from 'lucide-react'
import { AppShell } from '../components/layout/AppShell'
import { Card } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { ImageDropzone } from '../components/workspace/ImageDropzone'
import { ConditionsForm, type Conditions } from '../components/workspace/ConditionsForm'
import { ResultsPanel } from '../components/workspace/ResultsPanel'
import { predictGermination } from '../lib/api'
import type { PredictionRecord } from '../types'

const defaultConditions: Conditions = {
  soil_moisture: 45,
  temperature: 26,
  humidity: 55,
  rainfall: 40,
  soil_ph: 6.5,
  seed_type: 'Pearl Millet',
}

export function Workspace() {
  const [file, setFile] = useState<File | null>(null)
  const [conditions, setConditions] = useState<Conditions>(defaultConditions)
  const [result, setResult] = useState<PredictionRecord | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function handleSubmit() {
    if (!file) {
      setError('Attach a seed image before running an analysis.')
      return
    }
    setLoading(true)
    setError(null)
    try {
      const data = await predictGermination({ image: file, ...conditions })
      setResult(data)
    } catch (err) {
      console.error(err)
      setError('Unable to reach the SeedIQ prediction service. Confirm the API is running.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <AppShell>
      <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="mb-8">
        <h1 className="font-display text-2xl sm:text-3xl font-bold">Workspace</h1>
        <p className="text-sm text-[var(--color-text-muted)] mt-1.5">
          Upload a seed image and field conditions to generate a confidence-scored germination
          prediction.
        </p>
      </motion.div>

      <div className="grid grid-cols-1 lg:grid-cols-[400px_1fr] gap-6 items-start">
        <div className="flex flex-col gap-5">
          <Card>
            <h4 className="text-xs font-semibold uppercase tracking-wide text-[var(--color-text-faint)] mb-4">
              Seed image
            </h4>
            <ImageDropzone onFileChange={setFile} />
          </Card>

          <Card>
            <h4 className="text-xs font-semibold uppercase tracking-wide text-[var(--color-text-faint)] mb-4">
              Field conditions
            </h4>
            <ConditionsForm values={conditions} onChange={setConditions} />
          </Card>

          <Button size="lg" icon={<ScanLine size={17} />} onClick={handleSubmit} disabled={loading}>
            {loading ? 'Analyzing…' : 'Run analysis'}
          </Button>
          {error && !loading && <p className="text-xs text-red-400 text-center">{error}</p>}
        </div>

        <ResultsPanel result={result} loading={loading} error={null} />
      </div>
    </AppShell>
  )
}
