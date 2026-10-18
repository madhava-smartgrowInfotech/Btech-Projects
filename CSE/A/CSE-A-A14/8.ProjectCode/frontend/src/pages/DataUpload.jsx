import { useEffect, useState } from 'react'
import { ArrowRight, Check, Columns3, Database, FileSpreadsheet, ListChecks, Save, Sparkles, Wand2 } from 'lucide-react'
import { PageHeader, Button, Card, ErrorState, FileDrop, KeyValueList, Select, Skeleton, StatCard, Stepper, Table, useToast } from '../components/ui'
import { Callout } from '../components/app'
import { api } from '../lib/api'
import { useAppState } from '../lib/appstate'
import { useAsync } from '../lib/hooks'
import { fmtInt } from '../lib/format'

const ROLE_OPTIONS = [
  { value: 'numeric', label: 'Numeric' },
  { value: 'categorical', label: 'Categorical' },
  { value: 'skip', label: 'Skip (not a feature)' },
]

export default function DataUpload() {
  const toast = useToast()
  const { state, refresh } = useAppState()
  const ds = state?.dataset
  const [busy, setBusy] = useState('')
  const [version, setVersion] = useState(0)
  const [prepared, setPrepared] = useState(null)

  const loaded = Boolean(ds?.loaded)
  const preview = useAsync(() => api.preview(15), [version], { enabled: loaded })
  const config = useAsync(() => api.dataConfig(), [version], { enabled: loaded })
  const quality = useAsync(() => api.quality(), [version, ds?.prepared], { enabled: loaded })

  const done = async (msg) => {
    setPrepared(null)
    setVersion((v) => v + 1)
    await refresh()
    toast({ kind: 'success', title: 'Dataset loaded', message: msg })
  }

  const loadSample = async () => {
    setBusy('sample')
    try {
      const r = await api.loadSample()
      await done(`${r.rows.toLocaleString('en-IN')} sample customers, ${r.columns} columns.`)
    } catch (e) {
      toast({ kind: 'error', title: 'Could not load the sample', message: e.message })
    } finally {
      setBusy('')
    }
  }

  const onFiles = async (files) => {
    const file = files[0]
    if (!file) return
    setBusy('upload')
    try {
      const r = await api.upload(file)
      await done(`${file.name}: ${r.rows.toLocaleString('en-IN')} rows, ${r.columns} columns.`)
    } catch (e) {
      toast({ kind: 'error', title: 'That file could not be loaded', message: e.message })
    } finally {
      setBusy('')
    }
  }

  const prepare = async () => {
    setBusy('prepare')
    try {
      const r = await api.prepare()
      setPrepared(r)
      await refresh()
      toast({ kind: 'success', title: 'Data prepared', message: `${r.rows_remaining.toLocaleString('en-IN')} rows ready for training.` })
    } catch (e) {
      toast({ kind: 'error', title: 'Could not prepare the data', message: e.message })
    } finally {
      setBusy('')
    }
  }

  const stepNow = !loaded ? 0 : ds?.prepared ? 4 : quality.data?.ready ? 3 : 1

  return (
    <div className="stack">
      <PageHeader
        eyebrow="Data"
        icon={Database}
        title="Data upload"
        lead="Bring in a telecom customer CSV, confirm which column is churn, review quality, then prepare it for training. The target and ID columns are detected for you."
      />

      <Card hover={false}>
        <Stepper
          label="Data preparation progress"
          current={stepNow}
          steps={[
            { label: 'Load data', hint: 'CSV or sample' },
            { label: 'Configure', hint: 'Target and ID' },
            { label: 'Check quality', hint: 'Review warnings' },
            { label: 'Prepare', hint: 'Ready to train' },
          ]}
        />
      </Card>

      <Card title="1. Load a dataset" subtitle="Your file stays on this machine.">
        <div className="grid-2">
          <div className="file-pick">
            <FileDrop accept=".csv,text/csv" label="Drop a CSV here or click to browse" hint="Classic Telco schema works out of the box; any CSV with a churn column is fine." onFiles={onFiles} />
          </div>
          <div className="stack" style={{ justifyContent: 'center' }}>
            <p className="muted">No file handy? Load 1,000 synthetic telecom customers with a realistic churn rate of about 26%.</p>
            <div className="row">
              <Button icon={Sparkles} onClick={loadSample} loading={busy === 'sample'} variant="secondary">
                Use sample dataset
              </Button>
            </div>
            {busy === 'upload' && <Callout tone="info">Reading your file…</Callout>}
            {loaded && (
              <Callout tone="success" title="Dataset in memory">
                {ds.name} · {ds.rows.toLocaleString('en-IN')} rows · {ds.columns} columns
              </Callout>
            )}
          </div>
        </div>
      </Card>

      {!loaded ? (
        <Callout tone="info" title="Nothing loaded yet">
          Upload a CSV or use the sample dataset to continue. The preview, column settings and quality report appear here.
        </Callout>
      ) : (
        <>
          <Card title="Dataset preview" subtitle="First 15 rows" actions={<FileSpreadsheet size={20} aria-hidden="true" />}>
            {preview.error ? (
              <ErrorState compact title="Preview unavailable" error={preview.error} onRetry={preview.reload} />
            ) : !preview.data ? (
              <Skeleton height={220} radius={18} />
            ) : (
              <Table
                caption="Dataset preview"
                pageSize={0}
                cards={false}
                tall
                rowKey={(_, i) => i}
                columns={preview.data.columns.map((c) => ({ key: c, label: c, sortable: false, render: (r) => (r[c] == null ? '–' : String(r[c])) }))}
                rows={preview.data.rows}
              />
            )}
          </Card>

          <ColumnConfig config={config} onSaved={async () => { setPrepared(null); setVersion((v) => v + 1); await refresh() }} />

          <Card title="3. Data quality report" actions={<ListChecks size={20} aria-hidden="true" />}>
            {quality.error ? (
              <ErrorState compact title="Quality report unavailable" error={quality.error} onRetry={quality.reload} />
            ) : !quality.data ? (
              <Skeleton height={140} radius={18} />
            ) : (
              <div className="stack">
                <div className="grid-kpi">
                  <StatCard label="Rows" value={quality.data.rows} format={fmtInt} tone="lavender" />
                  <StatCard label="Columns" value={quality.data.columns} format={fmtInt} tone="sky" />
                  <StatCard label="Duplicate rows" value={quality.data.duplicates} format={fmtInt} tone="peach" />
                  <StatCard label="Columns with missing values" value={quality.data.missing.length} format={fmtInt} tone="rose" />
                </div>
                {quality.data.warnings.map((w) => (
                  <Callout key={w} tone="warn">
                    {w}
                  </Callout>
                ))}
                {quality.data.errors.map((w) => (
                  <Callout key={w} tone="error" title="Not ready for training">
                    {w}
                  </Callout>
                ))}
                {quality.data.ready ? (
                  <Callout tone="success" title="Passes the training-readiness checks">
                    {quality.data.feature_count} feature columns selected. Missing values are imputed automatically inside the training pipeline.
                  </Callout>
                ) : (
                  quality.data.errors.length === 0 && <Callout tone="warn">Select at least one feature column in the settings above.</Callout>
                )}
                {quality.data.missing.length > 0 && (
                  <Table
                    caption="Missing values by column"
                    pageSize={8}
                    rowKey={(r) => r.column}
                    columns={[
                      { key: 'column', label: 'Column' },
                      { key: 'count', label: 'Missing cells', numeric: true },
                    ]}
                    rows={quality.data.missing}
                  />
                )}
              </div>
            )}
          </Card>

          <Card title="4. Prepare for training" subtitle="Removes exact duplicate rows and freezes the working copy used by every other screen.">
            <div className="row">
              <Button icon={Wand2} onClick={prepare} loading={busy === 'prepare'} disabled={!quality.data?.ready}>
                {ds?.prepared ? 'Prepare again' : 'Prepare data'}
              </Button>
              {ds?.prepared && (
                <>
                  <Button variant="secondary" to="/app/eda" iconRight={ArrowRight}>
                    Explore the data
                  </Button>
                  <Button variant="secondary" to="/app/train" iconRight={ArrowRight}>
                    Train models
                  </Button>
                </>
              )}
            </div>
            {!quality.data?.ready && quality.data && <p className="small muted" style={{ marginTop: 10 }}>Fix the issues above to enable preparation.</p>}
            {ds?.prepared && (
              <div style={{ marginTop: 16 }}>
                <Callout tone="success" title="Data prepared">
                  {prepared ? (
                    <KeyValueList items={[['Duplicate rows removed', fmtInt(prepared.duplicates_removed)], ['Rows ready for training', fmtInt(prepared.rows_remaining)], ['Missing cells (imputed later)', fmtInt(prepared.missing_before)]]} />
                  ) : (
                    <>{ds.prepared_rows.toLocaleString('en-IN')} customers are ready. Continue to exploration or model training.</>
                  )}
                </Callout>
              </div>
            )}
          </Card>
        </>
      )}
    </div>
  )
}

function ColumnConfig({ config, onSaved }) {
  const toast = useToast()
  const [target, setTarget] = useState('')
  const [idCol, setIdCol] = useState('')
  const [roles, setRoles] = useState({})
  const [saving, setSaving] = useState(false)
  const c = config.data

  useEffect(() => {
    if (!c) return
    setTarget(c.target_col || '')
    setIdCol(c.id_col || '')
    const r = {}
    c.numeric_cols.forEach((x) => (r[x] = 'numeric'))
    c.categorical_cols.forEach((x) => (r[x] = 'categorical'))
    setRoles(r)
  }, [c])

  if (config.error) return <ErrorState compact title="Column settings unavailable" error={config.error} onRetry={config.reload} />
  if (!c) return <Skeleton height={180} radius={24} />

  const candidates = c.columns.filter((x) => x !== target && x !== idCol)
  const role = (col) => roles[col] || 'skip'
  const save = async () => {
    setSaving(true)
    try {
      await api.saveConfig({
        target_col: target || null,
        id_col: idCol || null,
        numeric_cols: candidates.filter((x) => role(x) === 'numeric'),
        categorical_cols: candidates.filter((x) => role(x) === 'categorical'),
      })
      toast({ kind: 'success', title: 'Column settings saved', message: 'Prepare the data again to apply them.' })
      await onSaved()
    } catch (e) {
      toast({ kind: 'error', title: 'Settings not saved', message: e.message })
    } finally {
      setSaving(false)
    }
  }
  const dirty =
    target !== (c.target_col || '') ||
    idCol !== (c.id_col || '') ||
    candidates.some((x) => role(x) !== (c.numeric_cols.includes(x) ? 'numeric' : c.categorical_cols.includes(x) ? 'categorical' : 'skip'))

  return (
    <Card title="2. Column configuration" subtitle="Check what was auto-detected." actions={<Columns3 size={20} aria-hidden="true" />}>
      <div className="form-grid wide">
        <Select
          id="target"
          label="Churn / target column"
          value={target}
          onChange={(e) => setTarget(e.target.value)}
          options={[{ value: '', label: '— none detected —' }, ...c.columns]}
          hint={c.detected_target ? `Detected: ${c.detected_target}` : 'Could not detect one, please choose.'}
          error={!target ? 'A churn column is required.' : undefined}
        />
        <Select id="idcol" label="Customer ID column (optional)" value={idCol} onChange={(e) => setIdCol(e.target.value)} options={[{ value: '', label: '— none —' }, ...c.columns]} hint={c.detected_id ? `Detected: ${c.detected_id}` : undefined} />
      </div>
      <details style={{ marginTop: 18 }}>
        <summary style={{ cursor: 'pointer', fontWeight: 600, padding: '8px 0' }}>Advanced: feature column types ({candidates.filter((x) => role(x) !== 'skip').length} of {candidates.length} used)</summary>
        <div className="form-grid wide" style={{ marginTop: 12 }}>
          {candidates.map((col) => (
            <Select key={col} id={`role-${col}`} label={col} value={role(col)} onChange={(e) => setRoles((r) => ({ ...r, [col]: e.target.value }))} options={ROLE_OPTIONS} />
          ))}
        </div>
      </details>
      <div className="row" style={{ marginTop: 18 }}>
        <Button icon={dirty ? Save : Check} onClick={save} loading={saving} disabled={!dirty || !target} variant={dirty ? 'primary' : 'secondary'}>
          {dirty ? 'Save column settings' : 'Settings saved'}
        </Button>
        {dirty && <span className="small muted">Saving resets the prepared copy, so you will prepare it again.</span>}
      </div>
    </Card>
  )
}
