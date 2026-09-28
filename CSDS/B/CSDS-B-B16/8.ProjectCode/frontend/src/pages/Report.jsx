import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { ArrowLeft, Download } from 'lucide-react'
import api, { errorText } from '../api.js'
import { ErrorBox, Spinner } from '../components/ui.jsx'

export default function Report() {
  const { id } = useParams()
  const [url, setUrl] = useState('')
  const [error, setError] = useState('')

  const load = () => {
    setError('')
    setUrl('')
    api.get(`/screenings/${id}/report`, { responseType: 'blob' })
      .then(({ data }) => setUrl(URL.createObjectURL(new Blob([data], { type: 'application/pdf' }))))
      .catch((e) => setError(errorText(e)))
  }
  useEffect(() => {
    load()
    return () => url && URL.revokeObjectURL(url)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id])

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <Link to={`/screenings/${id}`} className="flex items-center gap-1 text-sm text-teal-700 hover:underline"><ArrowLeft className="h-4 w-4" /> Back to result</Link>
          <h1 className="text-2xl font-bold text-slate-900">Screening report #{id}</h1>
        </div>
        {url && (
          <a href={url} download={`retinaguard_report_${id}.pdf`} className="btn-primary">
            <Download className="h-4 w-4" /> Download PDF
          </a>
        )}
      </div>
      <ErrorBox error={error} onRetry={load} />
      {!url && !error && <Spinner text="Generating PDF report..." />}
      {url && <iframe title="Screening report" src={url} className="h-[80vh] w-full rounded-xl border border-slate-200 bg-white" />}
    </div>
  )
}
