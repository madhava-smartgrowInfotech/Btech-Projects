import { useEffect, useState } from 'react'
import { PageHeader } from '@/components/dashboard/PageHeader'
import { SeverityBadge } from '@/components/dashboard/SeverityBadge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { analyticsApi, type DefectInfo } from '@/lib/api'

export function DefectCatalogPage() {
  const [catalog, setCatalog] = useState<Record<string, DefectInfo> | null>(null)

  useEffect(() => {
    analyticsApi.defectCatalog().then(setCatalog)
  }, [])

  if (!catalog) {
    return (
      <div className="p-8">
        <div className="h-8 w-8 rounded-full border-2 border-cyan-400/30 border-t-cyan-400 animate-spin" />
      </div>
    )
  }

  return (
    <div>
      <PageHeader
        title="Defect Catalog"
        description="Reference knowledge base used by the root-cause engine."
      />
      <div className="p-8 grid grid-cols-1 md:grid-cols-2 gap-5">
        {Object.entries(catalog).map(([key, info]) => (
          <Card key={key}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0">
              <CardTitle>{info.display_name}</CardTitle>
              <SeverityBadge severity={info.severity_baseline} />
            </CardHeader>
            <CardContent className="space-y-4 pt-2">
              <p className="text-sm text-slate-400 leading-relaxed">{info.description}</p>
              <div>
                <p className="text-xs font-semibold text-slate-300 uppercase tracking-wide mb-2">
                  Typical causes
                </p>
                <ul className="space-y-1.5">
                  {info.likely_causes.map((c, i) => (
                    <li key={i} className="text-sm text-slate-400 flex gap-2">
                      <span className="text-cyan-400">—</span> {c}
                    </li>
                  ))}
                </ul>
              </div>
              <div>
                <p className="text-xs font-semibold text-slate-300 uppercase tracking-wide mb-2">
                  Corrective actions
                </p>
                <ul className="space-y-1.5">
                  {info.corrective_actions.map((c, i) => (
                    <li key={i} className="text-sm text-slate-400 flex gap-2">
                      <span className="text-emerald-400">—</span> {c}
                    </li>
                  ))}
                </ul>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )
}
