import { motion } from 'framer-motion'
import { CheckCircle2, Download, FileWarning } from 'lucide-react'
import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { ClassProbabilityChart } from '@/components/dashboard/ClassProbabilityChart'
import { CompareSlider } from '@/components/dashboard/CompareSlider'
import { PageHeader } from '@/components/dashboard/PageHeader'
import { SeverityBadge } from '@/components/dashboard/SeverityBadge'
import { Button } from '@/components/ui/Button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { useAuthedImage } from '@/hooks/useAuthedImage'
import { api, inspectionsApi, type InspectionOut } from '@/lib/api'
import { formatDate, formatPercent } from '@/lib/utils'

export function InspectionDetailPage() {
  const { id } = useParams<{ id: string }>()
  const [inspection, setInspection] = useState<InspectionOut | null>(null)
  const [loading, setLoading] = useState(true)
  const [downloading, setDownloading] = useState(false)

  const originalUrl = useAuthedImage(inspection?.image_url ?? null)
  const heatmapUrl = useAuthedImage(inspection?.heatmap_url ?? null)

  useEffect(() => {
    if (!id) return
    inspectionsApi
      .get(Number(id))
      .then(setInspection)
      .finally(() => setLoading(false))
  }, [id])

  async function handleDownloadReport() {
    if (!inspection) return
    setDownloading(true)
    try {
      const res = await api.get(inspectionsApi.reportPath(inspection.id), {
        responseType: 'blob',
      })
      const url = URL.createObjectURL(res.data)
      const a = document.createElement('a')
      a.href = url
      a.download = `VisionForge_Inspection_${inspection.id}.pdf`
      a.click()
      URL.revokeObjectURL(url)
    } finally {
      setDownloading(false)
    }
  }

  if (loading) {
    return (
      <div className="p-8">
        <div className="h-8 w-8 rounded-full border-2 border-cyan-400/30 border-t-cyan-400 animate-spin" />
      </div>
    )
  }

  if (!inspection) {
    return <div className="p-8 text-slate-400">Inspection not found.</div>
  }

  return (
    <div>
      <PageHeader
        title={inspection.asset_name}
        description={`Inspection #${inspection.id} · ${formatDate(inspection.created_at)}`}
        action={
          <Button size="sm" variant="secondary" onClick={handleDownloadReport} disabled={downloading}>
            <Download className="h-4 w-4" />
            {downloading ? 'Preparing…' : 'Download PDF Report'}
          </Button>
        }
      />

      <div className="p-8 grid grid-cols-1 lg:grid-cols-5 gap-6">
        <div className="lg:col-span-3 space-y-6">
          <Card>
            <CardContent className="pt-6">
              {originalUrl && heatmapUrl ? (
                <CompareSlider beforeSrc={originalUrl} afterSrc={heatmapUrl} />
              ) : (
                <div className="aspect-video rounded-xl bg-white/5 animate-pulse" />
              )}
              <p className="text-xs text-slate-500 mt-3 text-center">
                Drag the handle to compare the original surface against the Grad-CAM explainability heatmap.
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Defect Probability Breakdown</CardTitle>
            </CardHeader>
            <CardContent className="pt-2">
              <ClassProbabilityChart data={inspection.class_probabilities} />
            </CardContent>
          </Card>
        </div>

        <div className="lg:col-span-2 space-y-6">
          <Card>
            <CardContent className="pt-6 space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-sm text-slate-400">Detected defect</span>
                <span className="font-display font-semibold text-white">{inspection.display_name}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-slate-400">Model confidence</span>
                <span className="text-cyan-300 font-medium">{formatPercent(inspection.confidence)}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-slate-400">Severity</span>
                <SeverityBadge severity={inspection.severity} />
              </div>
              <p className="text-sm text-slate-400 leading-relaxed border-t border-white/5 pt-4">
                {inspection.description}
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center gap-2 space-y-0">
              <FileWarning className="h-4 w-4 text-amber-400" />
              <CardTitle className="text-base">Root Cause Analysis</CardTitle>
            </CardHeader>
            <CardContent className="pt-2">
              <div className="space-y-2">
                {inspection.root_cause_text.split('\n').map((line, i) => (
                  <p key={i} className="text-sm text-slate-400 leading-relaxed">
                    {line}
                  </p>
                ))}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center gap-2 space-y-0">
              <CheckCircle2 className="h-4 w-4 text-emerald-400" />
              <CardTitle className="text-base">Corrective Actions</CardTitle>
            </CardHeader>
            <CardContent className="pt-2">
              <ul className="space-y-2.5">
                {inspection.corrective_actions.map((action, i) => (
                  <motion.li
                    key={i}
                    initial={{ opacity: 0, x: -8 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: i * 0.08 }}
                    className="flex items-start gap-2.5 text-sm text-slate-300"
                  >
                    <span className="mt-1.5 h-1.5 w-1.5 rounded-full bg-emerald-400 shrink-0" />
                    {action}
                  </motion.li>
                ))}
              </ul>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
