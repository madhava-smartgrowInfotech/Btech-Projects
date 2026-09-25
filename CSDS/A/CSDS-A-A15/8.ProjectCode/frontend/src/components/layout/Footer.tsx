import { ScanEye } from 'lucide-react'

export function Footer() {
  return (
    <footer className="border-t border-white/5 py-12">
      <div className="mx-auto max-w-7xl px-6 flex flex-col md:flex-row items-center justify-between gap-6">
        <div className="flex items-center gap-2 text-white font-display font-semibold">
          <ScanEye className="h-5 w-5 text-cyan-400" />
          VisionForge AI
        </div>
        <p className="text-sm text-slate-500 text-center">
          Explainable inspection intelligence for modern manufacturing lines.
        </p>
        <p className="text-xs text-slate-600">© {new Date().getFullYear()} VisionForge AI. All rights reserved.</p>
      </div>
    </footer>
  )
}
