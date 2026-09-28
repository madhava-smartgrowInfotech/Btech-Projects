import { Link } from 'react-router-dom'
import { Activity, Eye, FileText, Flame, HeartPulse, Layers, LineChart, ScanEye } from 'lucide-react'
import { Disclaimer } from '../components/ui.jsx'

const features = [
  [ScanEye, 'Fundus preprocessing', 'Green channel, CLAHE enhancement, resizing and normalisation shown step by step, with a blur and illumination quality check.'],
  [Layers, 'Haar wavelet features', 'A 2-level Haar transform splits the image into LL, LH, HL and HH sub-bands that highlight vessels and lesions.'],
  [Eye, 'Retinopathy detection', 'A compact LeNet CNN reads the wavelet sub-bands and returns a hypertensive retinopathy probability.'],
  [Flame, 'Explainable results', 'Grad-CAM heatmaps show where the model looked; a Frangi filter maps the retinal vessels.'],
  [HeartPulse, 'Heart-disease risk', 'A Random Forest scores the clinical profile and SHAP lists the factors that drive the risk.'],
  [Activity, 'Combined risk stage', 'Retinal and clinical results merge into Low, Moderate, High or Very high with recommendations.'],
  [FileText, 'Screening report', 'A PDF with the images, findings, risk stage and recommendations, ready to file or share.'],
  [LineChart, 'Measured performance', 'Accuracy, sensitivity, specificity, F1, ROC-AUC and confusion matrices for both models.'],
]

export default function Landing() {
  const signedIn = !!localStorage.getItem('rg_token')
  return (
    <div className="min-h-screen bg-white">
      <header className="mx-auto flex max-w-6xl items-center justify-between px-4 py-5">
        <div className="flex items-center gap-2 text-lg font-bold text-teal-800">
          <Eye className="h-6 w-6" /> RetinaGuard
        </div>
        <Link to={signedIn ? '/screening/new' : '/login'} className="btn-primary">
          {signedIn ? 'Open app' : 'Sign in'}
        </Link>
      </header>
      <section className="bg-gradient-to-b from-teal-50 to-white">
        <div className="mx-auto max-w-6xl px-4 py-16 md:py-24">
          <p className="mb-3 text-sm font-semibold uppercase tracking-wide text-teal-700">Eye and heart risk in one screening</p>
          <h1 className="max-w-3xl text-4xl font-bold leading-tight text-slate-900 md:text-5xl">
            Catch hypertensive retinopathy and cardiovascular risk before symptoms appear.
          </h1>
          <p className="mt-5 max-w-2xl text-lg text-slate-600">
            RetinaGuard analyses a fundus photograph with wavelet features and a CNN, scores the patient's clinical profile, and
            combines both into a single, explained risk stage for ophthalmologists, physicians and screening camps.
          </p>
          <div className="mt-8 flex flex-wrap gap-3">
            <Link to={signedIn ? '/screening/new' : '/login'} className="btn-primary px-6 py-3 text-base">
              Start a screening
            </Link>
            <a href="#features" className="btn-secondary px-6 py-3 text-base">
              How it works
            </a>
          </div>
        </div>
      </section>
      <section id="features" className="mx-auto max-w-6xl px-4 py-14">
        <h2 className="mb-8 text-2xl font-bold text-slate-900">From fundus image to risk stage</h2>
        <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
          {features.map(([Icon, title, text]) => (
            <div key={title} className="card">
              <Icon className="mb-3 h-7 w-7 text-teal-700" />
              <h3 className="mb-1 font-semibold text-slate-900">{title}</h3>
              <p className="text-sm text-slate-600">{text}</p>
            </div>
          ))}
        </div>
        <div className="mt-10">
          <Disclaimer />
        </div>
      </section>
      <footer className="border-t border-slate-200 py-6 text-center text-xs text-slate-500">RetinaGuard - clinical decision support for retinal and cardiovascular screening</footer>
    </div>
  )
}
