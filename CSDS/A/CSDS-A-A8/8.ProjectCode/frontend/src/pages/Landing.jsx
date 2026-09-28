import { Link } from 'react-router-dom'
import { BarChart3, Brain, Dna, FileText, Fingerprint, Layers } from 'lucide-react'
import { Logo } from '../components/Layout.jsx'
import { getUser } from '../api.js'

const features = [
  { icon: Layers, title: 'JEPA pre-training', text: 'A compact vision transformer learns brain-MRI structure by predicting the features of hidden patches, with no masks needed.' },
  { icon: Brain, title: 'Few-label segmentation', text: 'A light decoder turns the pre-trained encoder into a tumour segmenter using only 10% of expert masks.' },
  { icon: BarChart3, title: 'Label-efficiency evidence', text: 'Dice and IoU at 10% and 100% of masks against a supervised U-Net and a reconstruction-based baseline.' },
  { icon: Dna, title: 'DNA sequence encoder', text: 'k-mer tokens and the same latent-prediction objective detect STR repeat types in sequencing reads.' },
  { icon: Fingerprint, title: 'STR profile matching', text: 'Query profiles are ranked against a reference database with theta-corrected likelihood ratios.' },
  { icon: FileText, title: 'Structured reports', text: 'Every segmentation and match comes with a structured written report generated from the real model output.' },
]

export default function Landing() {
  const user = getUser()
  return (
    <div className="min-h-screen bg-white">
      <header className="mx-auto flex max-w-6xl items-center justify-between px-4 py-4">
        <Logo />
        <Link to={user ? '/mri' : '/login'} className="btn">{user ? 'Open workspace' : 'Sign in'}</Link>
      </header>
      <section className="mx-auto max-w-6xl px-4 pb-12 pt-10 text-center sm:pt-16">
        <span className="rounded-full bg-teal-50 px-3 py-1 text-xs font-medium text-teal-700">Label-efficient imaging and DNA analysis</span>
        <h1 className="mx-auto mt-5 max-w-3xl text-4xl font-bold tracking-tight text-slate-900 sm:text-5xl">
          Segment tumours and match DNA profiles from few labels
        </h1>
        <p className="mx-auto mt-4 max-w-2xl text-lg text-slate-600">
          BioSight uses joint-embedding predictive learning across medical images and DNA sequences,
          then explains each result in a structured report for radiology and forensic teams.
        </p>
        <div className="mt-8 flex justify-center gap-3">
          <Link to={user ? '/mri' : '/login'} className="btn px-6 py-2.5">Get started</Link>
          <Link to={user ? '/label-efficiency' : '/login'} className="btn-outline px-6 py-2.5">See the results</Link>
        </div>
      </section>
      <section className="border-t border-slate-100 bg-slate-50">
        <div className="mx-auto grid max-w-6xl gap-4 px-4 py-12 sm:grid-cols-2 lg:grid-cols-3">
          {features.map(({ icon: Icon, title, text }) => (
            <div key={title} className="card">
              <Icon className="text-teal-600" size={22} />
              <h3 className="mt-3 font-semibold text-slate-900">{title}</h3>
              <p className="mt-1 text-sm text-slate-600">{text}</p>
            </div>
          ))}
        </div>
      </section>
      <section className="mx-auto max-w-6xl px-4 py-10 text-sm text-slate-500">
        <h2 className="mb-2 font-semibold text-slate-800">Who it is for</h2>
        <p>Radiology and research teams that need tumour segmentation with few annotations, forensic DNA laboratories matching STR profiles, and bioinformatics researchers exploring learned representations.</p>
        <p className="mt-4 text-xs">Decision-support software. Results must be reviewed by a qualified radiologist or DNA analyst.</p>
      </section>
    </div>
  )
}
