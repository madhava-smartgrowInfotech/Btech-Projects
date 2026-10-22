import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { AlertTriangle, ClipboardList, Sparkles, RotateCcw } from 'lucide-react'
import { api } from '../lib/api'
import { useAsync } from '../lib/useAsync'
import { loadBaseline, saveBaseline, saveResult } from '../lib/baseline'
import { Button, Card, PageHeader, Skeleton, useToast } from '../components/ui'
import { SlideUp } from '../components/motion'
import Async from '../components/Async'
import ProfileForm, { EMPTY_PROFILE, SAMPLE_PROFILE, validateProfile } from '../components/ProfileForm'
import { Disclaimer } from '../components/Common'

function FormSkeleton() {
  return (
    <div className="card" role="status" aria-label="Loading form">
      <div className="form-grid">
        {Array.from({ length: 12 }).map((_, i) => (
          <div key={i}><Skeleton width="45%" height={13} /><Skeleton height={50} radius={16} style={{ marginTop: 8 }} /></div>
        ))}
      </div>
    </div>
  )
}

function AssessForm({ options }) {
  const navigate = useNavigate()
  const toast = useToast()
  const [values, setValues] = useState(() => ({ ...EMPTY_PROFILE, ...(loadBaseline() || {}) }))
  const [errors, setErrors] = useState({})
  const [serverErrors, setServerErrors] = useState([])
  const [busy, setBusy] = useState(false)

  const submit = async (e) => {
    e.preventDefault()
    const errs = validateProfile(values, options)
    setErrors(errs)
    setServerErrors([])
    if (Object.keys(errs).length) {
      setServerErrors(['Please fix the highlighted fields and try again.'])
      document.querySelector('[aria-invalid="true"]')?.focus()
      return
    }
    setBusy(true)
    try {
      const result = await api.predict(values)
      saveBaseline(values)
      saveResult(result)
      toast({ kind: 'success', title: 'Analysis complete', message: `Profile: ${result.profile} · risk ${result.risk}.` })
      navigate('/app/result')
    } catch (err) {
      setServerErrors(err.errors?.length ? err.errors : [err.message])
      toast({ kind: 'error', title: 'Analysis failed', message: err.status === 0 ? 'The API is offline.' : 'Check the inputs and try again.' })
    } finally {
      setBusy(false)
    }
  }

  return (
    <form onSubmit={submit} noValidate className="stack" style={{ '--gap': '18px' }}>
      {serverErrors.length > 0 && (
        <SlideUp>
          <div className="state error" role="alert" style={{ alignItems: 'flex-start', textAlign: 'left', padding: '18px 20px' }}>
            <strong className="row" style={{ '--gap': '8px' }}><AlertTriangle size={18} aria-hidden="true" />Could not analyse this profile</strong>
            <ul style={{ margin: 0, paddingLeft: 20 }}>{serverErrors.map((m) => <li key={m}>{m}</li>)}</ul>
            <p className="small">Fix the fields above, or make sure the API is running (run.bat), then try again.</p>
          </div>
        </SlideUp>
      )}
      <Card hover={false} title="Your information" subtitle="Every field is used by the trained model. Validation also runs on the server before analysis.">
        <ProfileForm values={values} onChange={setValues} errors={errors} options={options} prefix="assess" />
      </Card>
      <div className="row between">
        <div className="row">
          <Button type="submit" size="lg" icon={Sparkles} loading={busy}>Analyse my profile</Button>
          <Button variant="ghost" icon={ClipboardList} onClick={() => { setValues(SAMPLE_PROFILE); setErrors({}); setServerErrors([]) }}>Use sample profile</Button>
          <Button variant="ghost" icon={RotateCcw} onClick={() => { setValues(EMPTY_PROFILE); setErrors({}); setServerErrors([]) }}>Clear</Button>
        </div>
      </div>
      <Disclaimer />
    </form>
  )
}

export default function Assess() {
  const state = useAsync(api.options)
  return (
    <div className="stack" style={{ '--gap': '8px' }}>
      <PageHeader
        eyebrow="Assessment"
        icon={ClipboardList}
        title="Financial assessment"
        lead="Enter demographic and financial information. The trained model returns your profile, risk band, the factors behind the score and a forecast context."
      />
      <Async state={state} skeleton={<FormSkeleton />} title="Could not load the form options">
        {(options) => <AssessForm options={options} />}
      </Async>
    </div>
  )
}
