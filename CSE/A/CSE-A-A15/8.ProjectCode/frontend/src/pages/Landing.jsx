import { Link } from 'react-router-dom'
import { EyeOff, FileLock2, ImageIcon, KeyRound, ShieldCheck } from 'lucide-react'
import { getToken } from '../api'

const steps = [
  [FileLock2, 'Encrypt the file', 'AES-256-GCM seals your file with a fresh session key for every message. Any tampering is detected.'],
  [KeyRound, 'Wrap the key', "The session key is locked with the receiver's RSA public key (OAEP). Only their private key can open it."],
  [ImageIcon, 'Hide it in a picture', 'The sealed bundle is written into the lowest bits of an ordinary-looking PNG. Nothing looks unusual.'],
]

export default function Landing() {
  return (
    <div className="min-h-screen bg-ink-950 text-slate-200">
      <header className="mx-auto flex max-w-5xl items-center justify-between px-4 py-5">
        <span className="flex items-center gap-2 text-lg font-semibold text-white">
          <ShieldCheck className="h-6 w-6 text-brand-500" /> CipherVeil
        </span>
        <Link to={getToken() ? '/send' : '/login'} className="btn-primary">{getToken() ? 'Open app' : 'Sign in'}</Link>
      </header>

      <section className="mx-auto max-w-5xl px-4 pb-14 pt-12 text-center">
        <h1 className="!text-4xl font-bold leading-tight !text-white sm:!text-5xl">
          Two layers of protection.<br />One ordinary-looking image.
        </h1>
        <p className="mx-auto mt-5 max-w-2xl text-slate-400">
          Encryption tells an eavesdropper that something secret is moving. Hiding alone offers no protection once it is found.
          CipherVeil does both: your file is encrypted, then hidden where nobody thinks to look.
        </p>
        <div className="mt-8 flex justify-center gap-3">
          <Link to="/login" className="btn-primary px-6 py-3">Get started</Link>
          <a href="#how" className="btn border border-ink-700 px-6 py-3 text-slate-200 hover:bg-ink-800">How it works</a>
        </div>
      </section>

      <section id="how" className="mx-auto grid max-w-5xl gap-4 px-4 pb-14 sm:grid-cols-3">
        {steps.map(([Icon, title, text], i) => (
          <div key={title} className="rounded-xl border border-ink-700 bg-ink-900 p-5">
            <div className="mb-3 flex items-center gap-2 text-brand-500"><Icon className="h-5 w-5" /> <span className="text-sm">Step {i + 1}</span></div>
            <h3 className="font-semibold text-white">{title}</h3>
            <p className="mt-2 text-sm text-slate-400">{text}</p>
          </div>
        ))}
      </section>

      <section className="mx-auto max-w-5xl px-4 pb-16">
        <div className="rounded-xl border border-ink-700 bg-ink-900 p-6">
          <h3 className="flex items-center gap-2 font-semibold text-white"><EyeOff className="h-5 w-5 text-brand-500" /> Measured, not promised</h3>
          <p className="mt-2 text-sm text-slate-400">
            Every message reports PSNR and SSIM against the original cover, histograms and bit planes before and after, how much of the image was used,
            and timings. The robustness test is blunt: lossless handling keeps the payload, while JPEG recompression, noise or resizing destroys it. Send the result as a PNG.
          </p>
        </div>
      </section>
    </div>
  )
}
