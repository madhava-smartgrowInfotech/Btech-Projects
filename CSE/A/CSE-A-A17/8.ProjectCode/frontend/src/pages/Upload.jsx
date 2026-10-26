import { useEffect, useState } from 'react'
import { ArrowRight, Database } from 'lucide-react'
import { Alert, Button, Card, Field, FileDrop, Input, KeyValueList, PageHeader, Skeleton, StatCard } from '../components/ui'
import { ActionError, useAction } from '../components/app/common'
import { api } from '../lib/api'
import { fmtInt } from '../lib/format'
import { usePipeline } from '../lib/pipeline'

function Report({ report }) {
  return (
    <div className="page-stack">
      <div className="metric-grid">
        <StatCard label="Transactions" value={report.num_transactions} />
        <StatCard label="Customers" value={report.num_customers} />
        <StatCard label="Products" value={report.num_products} />
        <StatCard label="Columns" value={report.columns} hint="After merging" />
      </div>
      <div className="metric-grid">
        <StatCard label="Missing values" value={report.missing_values_total} hint="Across the merged table" />
        <StatCard label="Duplicate rows" value={report.duplicate_rows} />
        <StatCard label="Rows removed" value={report.rows_removed} hint={`of ${fmtInt(report.raw_rows)} read`} />
      </div>
      <Card title="Date range">
        <KeyValueList
          items={[
            { label: 'First sale', value: report.date_min },
            { label: 'Last sale', value: report.date_max },
            { label: 'Catalogue', value: `${fmtInt(report.articles)} articles` },
            { label: 'Customers file', value: report.customers_file ? 'Merged' : 'Not provided (optional)' },
          ]}
        />
      </Card>
    </div>
  )
}

export default function Upload() {
  const { state, refresh } = usePipeline()
  const { run, loading, error, clear } = useAction()
  const [txn, setTxn] = useState(null)
  const [art, setArt] = useState(null)
  const [cust, setCust] = useState(null)
  const [rows, setRows] = useState('200000')
  const [missing, setMissing] = useState({})
  const [report, setReport] = useState(null)
  const [loadingExisting, setLoadingExisting] = useState(false)
  const [replacing, setReplacing] = useState(false)

  // Data may already be loaded in the API from earlier in the session.
  useEffect(() => {
    if (!state?.data_loaded || report) return
    setLoadingExisting(true)
    api('/api/data/report')
      .then(setReport)
      .catch(() => {})
      .finally(() => setLoadingExisting(false))
  }, [state?.data_loaded, report])

  const submit = async (e) => {
    e.preventDefault()
    const m = {}
    if (!txn) m.txn = 'Choose the transactions CSV.'
    if (!art) m.art = 'Choose the articles CSV.'
    const n = Number(rows)
    if (!Number.isInteger(n) || n < 0) m.rows = 'Enter a whole number, 0 for no limit.'
    setMissing(m)
    if (Object.keys(m).length) return
    clear()
    const form = new FormData()
    form.append('transactions', txn)
    form.append('articles', art)
    if (cust) form.append('customers', cust)
    form.append('sample_rows', String(n))
    const out = await run(() => api('/api/data/upload', { method: 'POST', form }), { success: 'Data loaded and cleaned successfully.' })
    if (out) {
      setReport(out)
      setReplacing(false)
      await refresh()
    }
  }

  const showForm = !state?.data_loaded || replacing
  return (
    <>
      <PageHeader
        eyebrow="01 · Data upload"
        title="Upload data"
        description="Upload your H&M dataset files. Only transactions and articles are required; customers adds demographic columns."
        actions={
          state?.data_loaded && !replacing ? (
            <Button onClick={() => setReplacing(true)}>Replace files</Button>
          ) : undefined
        }
      />
      <div className="page-stack">
        {showForm && (
          <form onSubmit={submit} noValidate className="page-stack" aria-label="Upload CSV files">
            <Card title="Files">
              <div className="grid grid-3">
                <Field label="Transactions CSV" error={missing.txn} hint="transactions_train.csv · required">
                  <FileDrop label="Transactions CSV" hint="Drop it here or click to browse" file={txn} onFile={setTxn} required />
                </Field>
                <Field label="Articles CSV" error={missing.art} hint="articles.csv · required">
                  <FileDrop label="Articles CSV" hint="Drop it here or click to browse" file={art} onFile={setArt} required />
                </Field>
                <Field label="Customers CSV" hint="customers.csv · optional">
                  <FileDrop label="Customers CSV" hint="Optional" file={cust} onFile={setCust} />
                </Field>
              </div>
            </Card>
            <Card title="Options">
              <div style={{ maxWidth: 420 }}>
                <Input
                  label="Max transaction rows to load"
                  type="number"
                  min="0"
                  step="50000"
                  inputMode="numeric"
                  value={rows}
                  onChange={(e) => setRows(e.target.value)}
                  error={missing.rows}
                  hint="Caps the read for speed on the very large H&M file. 0 means no limit."
                />
              </div>
            </Card>
            <ActionError error={error} />
            <div className="row">
              <Button type="submit" variant="primary" size="lg" loading={loading} icon={Database}>
                {loading ? 'Loading and cleaning…' : 'Load & process data'}
              </Button>
              {replacing && (
                <Button onClick={() => setReplacing(false)} disabled={loading}>
                  Cancel
                </Button>
              )}
              {loading && <span className="small muted">Large files can take a minute.</span>}
            </div>
          </form>
        )}

        {state?.data_loaded && !replacing && (
          <Alert tone="success" action={<Button size="sm" to="/app/explore" iconRight={ArrowRight}>Explore</Button>}>
            Data is loaded in this session. Upload new files to replace it.
          </Alert>
        )}

        {loadingExisting && !report && <Skeleton height={140} />}
        {report && !replacing && (
          <section aria-label="Data quality report" className="page-stack">
            <h2 className="display-sm">Data quality report</h2>
            <Report report={report} />
          </section>
        )}
      </div>
    </>
  )
}
