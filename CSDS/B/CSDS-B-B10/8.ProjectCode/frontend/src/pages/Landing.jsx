import { Link } from 'react-router-dom'
import { Activity, Gauge, ImageIcon, Layers, LockKeyhole, Radio, ShieldCheck, Zap } from 'lucide-react'

const features = [
  [Layers, 'Wavelet + chaos engine', 'Integer Haar lifting splits every frame into LL / LH / HL / HH sub-bands; Henon and 2-D logistic key streams drive permutation and XOR diffusion. Decryption is bit-exact.'],
  [ImageIcon, 'Image studio', 'Encrypt and decrypt drone imagery, inspect the sub-bands, the cipher image and the histograms, and verify the SHA-256 checksum.'],
  [ShieldCheck, 'Security lab', 'Entropy, histogram uniformity, correlation, NPCR, UACI, PSNR, MSE, SSIM, key sensitivity and key space - exportable as a report.'],
  [Activity, 'Attack tests', 'Salt-and-pepper noise, Gaussian noise and cropping applied to the cipher image, with the recovered quality measured.'],
  [Radio, 'Live UAV link', 'A sender streams encrypted drone frames over a WebSocket; the ground station decrypts them with FPS, latency and throughput on screen.'],
  [Gauge, 'Benchmark', 'Encryption and decryption time against AES-256-CTR and ChaCha20 on the same images.'],
]

export default function Landing({ user }) {
  return (
    <div className="min-h-screen bg-slate-900 text-white">
      <header className="mx-auto flex max-w-6xl items-center justify-between px-4 py-5">
        <div className="flex items-center gap-2 text-lg font-semibold"><LockKeyhole className="h-6 w-6 text-sky-400" /> SkyCipher</div>
        <Link to={user ? '/studio' : '/login'} className="btn-primary">{user ? 'Open console' : 'Sign in'}</Link>
      </header>
      <section className="mx-auto max-w-6xl px-4 pb-16 pt-12">
        <p className="mb-3 inline-flex items-center gap-2 rounded-full bg-sky-500/10 px-3 py-1 text-xs font-medium text-sky-300">
          <Zap className="h-3.5 w-3.5" /> Real-time image encryption for drone links
        </p>
        <h1 className="max-w-3xl text-4xl font-bold leading-tight sm:text-5xl">
          Lightweight, chaos-based encryption for every frame your UAV sends.
        </h1>
        <p className="mt-5 max-w-2xl text-lg text-slate-300">
          SkyCipher decomposes imagery with a wavelet transform, scrambles it with chaotic key streams and diffuses it
          with XOR - fast enough for live video, and backed by a full security lab so auditors can check the numbers.
        </p>
        <div className="mt-8 flex flex-wrap gap-3">
          <Link to={user ? '/studio' : '/login'} className="btn-primary px-6 py-3 text-base">Get started</Link>
          <Link to={user ? '/live' : '/login'} className="btn px-6 py-3 text-base border border-slate-600 text-slate-200 hover:bg-slate-800">See the live link</Link>
        </div>
      </section>
      <section className="bg-slate-50 py-14 text-slate-900">
        <div className="mx-auto grid max-w-6xl gap-5 px-4 sm:grid-cols-2 lg:grid-cols-3">
          {features.map(([Icon, title, text]) => (
            <div key={title} className="card">
              <Icon className="h-6 w-6 text-sky-600" />
              <h3 className="mt-3 font-semibold">{title}</h3>
              <p className="mt-1 text-sm text-slate-600">{text}</p>
            </div>
          ))}
        </div>
        <p className="mx-auto mt-10 max-w-6xl px-4 text-sm text-slate-500">
          Built for drone operators in survey, agriculture, inspection and disaster response, ground-station crews, and
          security auditors validating the link.
        </p>
      </section>
    </div>
  )
}
