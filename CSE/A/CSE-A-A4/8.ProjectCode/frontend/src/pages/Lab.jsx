import { useEffect, useRef, useState } from 'react'
import { useReducedMotion } from 'framer-motion'
import { AlertTriangle, Database, FlaskConical, Layers, Play, RefreshCw } from 'lucide-react'
import { api } from '../lib/api'
import { useApi } from '../lib/useApi'
import { fmtInt, fmtNum, fmtPct } from '../lib/format'
import { MODES, MODE_CODE, MODE_LABEL, MODE_TONE } from '../lib/labels'
import { BarCompare } from '../components/charts'
import { Badge, Button, Card, Checkbox, EmptyState, ErrorState, Input, KeyValueList, Modal, PageHeader, ProgressBar, Select, Stepper, useToast } from '../components/ui'
import { SlideUp } from '../components/motion'
import Loadable from '../components/app/Loadable'
import MetricTiles from '../components/app/MetricTiles'
import ConfusionMatrix from '../components/app/ConfusionMatrix'

const STEPS = [
  { label: 'Dataset', hint: 'Generate or inspect' },
  { label: 'Preprocess', hint: 'Encode, scale, select' },
  { label: 'Train', hint: 'Fit the three models' },
]
const METHODS = [
  { value: 'manual', label: 'Manual undersampling' },
  { value: 'smote', label: 'SMOTE oversampling' },
  { value: 'tomek', label: 'Tomek links' },
]
const load = () => Promise.all([api.datasetInfo(), api.trainStatus(), api.featureImportance()])

function inRange(v, lo, hi) {
  const n = Number(v)
  return Number.isInteger(n) && n >= lo && n <= hi
}

function Elapsed({ running }) {
  const [s, setS] = useState(0)
  useEffect(() => {
    if (!running) return undefined
    const t0 = Date.now()
    setS(0)
    const t = setInterval(() => setS(Math.round((Date.now() - t0) / 1000)), 500)
    return () => clearInterval(t)
  }, [running])
  return <span className="num">{s}s elapsed</span>
}

export default function Lab() {
  const toast = useToast()
  const reduce = useReducedMotion()
  const state = useApi(load)
  const [info, status, fi] = state.data || []

  const [step, setStep] = useState(0)
  const [confirm, setConfirm] = useState(null) // 'generate' | 'train' | 'preprocess'

  // dataset
  const [nFraud, setNFraud] = useState('19500')
  const [nLegit, setNLegit] = useState('19500')
  const [gen, setGen] = useState({ busy: false, error: null })
  // preprocess
  const [method, setMethod] = useState('manual')
  const [topK, setTopK] = useState('18')
  const [pre, setPre] = useState({ busy: false, error: null, res: null })
  // train
  const [modes, setModes] = useState({ classical: true, sa: true, qa: true })
  const [epochs, setEpochs] = useState('10')
  const [hidden, setHidden] = useState('65')
  const [train, setTrain] = useState({ busy: false, error: null, res: null })
  const mounted = useRef(true)
  useEffect(() => {
    mounted.current = true // re-arm: StrictMode runs mount -> cleanup -> mount in dev
    return () => { mounted.current = false }
  }, [])

  const fraudErr = inRange(nFraud, 500, 50000) ? undefined : 'Whole number from 500 to 50,000.'
  const legitErr = inRange(nLegit, 500, 50000) ? undefined : 'Whole number from 500 to 50,000.'
  const kErr = inRange(topK, 5, 30) ? undefined : 'Whole number from 5 to 30.'
  const epochErr = inRange(epochs, 1, 50) ? undefined : 'Whole number from 1 to 50.'
  const hidErr = inRange(hidden, 10, 300) ? undefined : 'Whole number from 10 to 300.'
  const chosen = MODES.filter((m) => modes[m])
  // feature count of the pipeline the trained models were fitted on (first value seen this session)
  const baseline = useRef(null)
  if (fi && baseline.current == null) baseline.current = fi.columns.length
  const modelFeatures = baseline.current

  const requestGenerate = () => (fraudErr || legitErr ? toast({ kind: 'error', title: 'Check the sizes', message: 'Both counts must be between 500 and 50,000.' }) : setConfirm('generate'))
  const requestPreprocess = () => {
    if (kErr) return toast({ kind: 'error', title: 'Check the feature count', message: kErr })
    return Number(topK) !== modelFeatures ? setConfirm('preprocess') : runPreprocess()
  }
  const requestTrain = () => {
    if (!chosen.length) return toast({ kind: 'error', title: 'Pick at least one model' })
    if (epochErr || hidErr) return toast({ kind: 'error', title: 'Check the training settings', message: epochErr || hidErr })
    return setConfirm('train')
  }

  const runGenerate = async () => {
    setConfirm(null)
    setGen({ busy: true, error: null })
    try {
      const r = await api.generateDataset(Number(nFraud), Number(nLegit))
      setGen({ busy: false, error: null })
      setStep(1)
      toast({ kind: 'success', title: 'Dataset generated', message: `${fmtInt(r.rows)} rows (${fmtInt(r.fraud)} fraud, ${fmtInt(r.legit)} legitimate).` })
      state.reload()
    } catch (error) {
      setGen({ busy: false, error })
    }
  }

  const runPreprocess = async () => {
    setConfirm(null)
    setPre({ busy: true, error: null, res: null })
    try {
      const res = await api.preprocess(method, Number(topK))
      setPre({ busy: false, error: null, res })
      setStep(2)
      toast({ kind: 'success', title: 'Preprocessing done', message: `${res.columns.length} features selected.` })
      state.reload()
    } catch (error) {
      setPre({ busy: false, error, res: null })
    }
  }

  const runTrain = async () => {
    setConfirm(null)
    setTrain({ busy: true, error: null, res: null })
    try {
      const res = await api.train(chosen, Number(epochs), Number(hidden))
      if (!mounted.current) return
      setTrain({ busy: false, error: null, res })
      baseline.current = Object.values(res)[0].config.n_visible
      toast({ kind: 'success', title: 'Training finished', message: `${chosen.length} model${chosen.length > 1 ? 's' : ''} trained and saved.` })
      state.reload()
      if (!reduce) import('canvas-confetti').then((m) => m.default({ particleCount: 70, spread: 70, origin: { y: 0.7 }, colors: ['#C7B9FF', '#A7E8C8', '#FFC9A3', '#A9D6FF'] }))
    } catch (error) {
      if (mounted.current) setTrain({ busy: false, error, res: null })
    }
  }

  const mismatch = pre.res && pre.res.columns.length !== modelFeatures

  return (
    <div className="stack" style={{ '--gap': '24px' }}>
      <PageHeader
        eyebrow="Advanced"
        icon={FlaskConical}
        title="Model lab"
        lead="Regenerate the dataset, rebuild the preprocessing pipeline and retrain the three models. Everyday screening does not need this."
      />
      <Loadable state={state} kpis={3} title="The lab could not load">
        {state.data && (
          <>
            <div className="cols-3">
              {MODES.map((m) => {
                const s = status[m]
                return (
                  <Card key={m} title={MODE_LABEL[m]} actions={<Badge tone={MODE_TONE[m]}>{MODE_CODE[m]}</Badge>} hover={false}>
                    {s ? (
                      <KeyValueList items={[['Epochs trained', s.epochs], ['Best F1', fmtPct(s.best_f1)], ['Last accuracy', fmtPct(s.last_metrics.accuracy)], ['Last recall', fmtPct(s.last_metrics.recall)]]} />
                    ) : (
                      <p className="muted small">Not trained yet.</p>
                    )}
                  </Card>
                )
              })}
            </div>
            <Stepper steps={STEPS} current={step} label="Lab workflow" />

            <Card title="1 · Dataset" subtitle="Synthetic card transactions with a fraud label" actions={<Badge tone="lavender" icon={Database}>{fmtInt(info.rows)} rows</Badge>} hover={false}>
              <div className="stack">
                <KeyValueList items={[['Fraud', fmtInt(info.fraud_count)], ['Legitimate', fmtInt(info.legit_count)], ['Columns', info.columns.length]]} />
                <div className="form-grid">
                  <Input label="Fraud rows" type="number" min="500" max="50000" step="500" value={nFraud} onChange={(e) => setNFraud(e.target.value)} error={fraudErr} />
                  <Input label="Legitimate rows" type="number" min="500" max="50000" step="500" value={nLegit} onChange={(e) => setNLegit(e.target.value)} error={legitErr} />
                </div>
                {gen.error && <ErrorState title="Dataset generation failed" error={gen.error} compact onRetry={requestGenerate} />}
                <div className="row">
                  <Button variant="secondary" icon={RefreshCw} loading={gen.busy} onClick={requestGenerate}>Generate new dataset</Button>
                  <span className="small muted">Overwrites data/creditcard_synthetic.csv.</span>
                </div>
              </div>
            </Card>

            <Card title="2 · Preprocess" subtitle="One-hot encoding, z-score scaling, correlation filter, balancing and feature selection" hover={false}>
              <div className="stack">
                <div className="form-grid">
                  <Select label="Balancing" value={method} onChange={(e) => setMethod(e.target.value)} options={METHODS} />
                  <Input label="Features to keep" type="number" min="5" max="30" value={topK} onChange={(e) => setTopK(e.target.value)} error={kErr} hint={`The loaded models use ${modelFeatures} features`} />
                </div>
                <div className="notice warn">
                  <AlertTriangle size={18} aria-hidden="true" />
                  <span>Preprocessing replaces the pipeline in memory. If the feature count differs from the {modelFeatures} the trained models expect, retrain all three before verifying transactions.</span>
                </div>
                {pre.error && <ErrorState title="Preprocessing failed" error={pre.error} compact onRetry={requestPreprocess} />}
                <div className="row">
                  <Button icon={Layers} loading={pre.busy} onClick={requestPreprocess}>Run preprocessing</Button>
                </div>
                {pre.res && (
                  <SlideUp className="stack">
                    <div className="notice ok" role="status">
                      <span>{pre.res.message}. Train {pre.res.train_shape.join(' × ')}, test {pre.res.test_shape.join(' × ')}.</span>
                    </div>
                    {mismatch && (
                      <div className="notice warn" role="alert">
                        <AlertTriangle size={18} aria-hidden="true" />
                        <span>This pipeline has {pre.res.columns.length} features, but the models were trained on {modelFeatures}. Retrain the models in step 3 before using Verify or Bulk.</span>
                      </div>
                    )}
                    <BarCompare
                      horizontal
                      yWidth={225}
                      height={Math.max(260, Object.keys(pre.res.feature_importance).length * 26)}
                      name="Importance"
                      label="Top feature importances after preprocessing"
                      valueFormat={(v) => fmtNum(v, 3)}
                      data={Object.entries(pre.res.feature_importance).map(([name, value]) => ({ name, value, highlight: pre.res.columns.includes(name) }))}
                    />
                    <KeyValueList items={[['Dropped as correlated', pre.res.dropped_corr.length ? pre.res.dropped_corr.join(', ') : 'None'], ['Scaling', pre.res.scaler]]} />
                  </SlideUp>
                )}
              </div>
            </Card>

            <Card title="3 · Train" subtitle="Fits the selected models on the current pipeline and saves them to models/" hover={false}>
              <div className="stack">
                <div className="row" role="group" aria-label="Models to train">
                  {MODES.map((m) => (
                    <Checkbox key={m} label={`${MODE_LABEL[m]} (${MODE_CODE[m]})`} checked={modes[m]} onChange={(v) => setModes((x) => ({ ...x, [m]: v }))} />
                  ))}
                </div>
                <div className="form-grid">
                  <Input label="Epochs" type="number" min="1" max="50" value={epochs} onChange={(e) => setEpochs(e.target.value)} error={epochErr} hint="More epochs take longer" />
                  <Input label="Hidden units" type="number" min="10" max="300" value={hidden} onChange={(e) => setHidden(e.target.value)} error={hidErr} hint="65 is the default (classical widens to 200)" />
                </div>
                {train.error && <ErrorState title="Training failed" error={train.error} compact onRetry={requestTrain} />}
                <div className="row">
                  <Button icon={Play} loading={train.busy} onClick={requestTrain}>Train selected models</Button>
                  {train.busy && <Elapsed running />}
                </div>
                {train.busy && (
                  <div role="status" aria-label="Training in progress" className="stack" style={{ '--gap': '8px' }}>
                    <ProgressBar indeterminate label="Training" />
                    <p className="small muted">Training runs on the server and cannot report per-epoch progress. Keep this tab open.</p>
                  </div>
                )}
                {!train.res && !train.busy && !train.error && (
                  <EmptyState compact icon={FlaskConical} title="No training run this session" message="Results with metrics and a confusion matrix appear here when training finishes." />
                )}
                {train.res && (
                  <SlideUp className="stack">
                    {Object.entries(train.res).map(([m, r]) => (
                      <Card key={m} title={`${MODE_LABEL[m]} (${MODE_CODE[m]})`} subtitle={`${r.config.n_hidden} hidden units · batch ${r.config.batch_size} · ${r.config.n_visible} features · ${fmtNum(r.history.elapsed_sec, 1)} s`} hover={false} tint={MODE_TONE[m]}>
                        <div className="stack">
                          <MetricTiles metrics={r.metrics} />
                          <ConfusionMatrix matrix={r.metrics.confusion_matrix} />
                        </div>
                      </Card>
                    ))}
                    <Button to="/app/models" variant="secondary">Compare the models</Button>
                  </SlideUp>
                )}
              </div>
            </Card>
          </>
        )}
      </Loadable>

      <Modal
        open={confirm === 'generate'}
        onClose={() => setConfirm(null)}
        title="Generate a new dataset?"
        description="This overwrites data/creditcard_synthetic.csv and clears the models and training histories held in memory until you retrain. Model files already saved in models/ are not deleted."
        footer={
          <>
            <Button variant="ghost" onClick={() => setConfirm(null)}>Cancel</Button>
            <Button variant="danger" data-autofocus onClick={runGenerate}>Generate dataset</Button>
          </>
        }
      />
      <Modal
        open={confirm === 'preprocess'}
        onClose={() => setConfirm(null)}
        title="Change the feature count?"
        description={`The trained models expect ${modelFeatures} features but you asked for ${topK}. Predictions will fail until you retrain all three models.`}
        footer={
          <>
            <Button variant="ghost" onClick={() => setConfirm(null)}>Cancel</Button>
            <Button variant="danger" data-autofocus onClick={runPreprocess}>Run anyway</Button>
          </>
        }
      />
      <Modal
        open={confirm === 'train'}
        onClose={() => setConfirm(null)}
        title="Start training?"
        description={`Trains ${chosen.map((m) => MODE_CODE[m]).join(', ')} for ${epochs} epochs. It runs in a single request and can take a minute or more. Existing model files for these modes will be overwritten.`}
        footer={
          <>
            <Button variant="ghost" onClick={() => setConfirm(null)}>Cancel</Button>
            <Button data-autofocus onClick={runTrain}>Start training</Button>
          </>
        }
      />
    </div>
  )
}
