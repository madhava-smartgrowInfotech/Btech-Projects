import { Leaf } from "lucide-react";

export function Footer() {
  return (
    <footer className="border-t border-ink-100 bg-ink-950 text-ink-300">
      <div className="mx-auto max-w-7xl px-5 sm:px-8 py-14 grid grid-cols-2 md:grid-cols-4 gap-8">
        <div className="col-span-2">
          <div className="flex items-center gap-2 text-white font-display font-semibold text-lg mb-3">
            <span className="flex h-7 w-7 items-center justify-center rounded-md bg-brand-600">
              <Leaf size={15} />
            </span>
            CropSight
          </div>
          <p className="text-sm max-w-xs text-ink-400">
            AI-based crop quality grading, price intelligence and smart delivery — built to move harvests
            from farm to buyer with clarity at every step.
          </p>
        </div>
        <div>
          <p className="text-xs font-semibold uppercase tracking-wider text-ink-500 mb-3">Platform</p>
          <ul className="space-y-2 text-sm">
            <li>Quality grading</li>
            <li>Price intelligence</li>
            <li>Delivery planning</li>
            <li>Live monitoring</li>
          </ul>
        </div>
        <div>
          <p className="text-xs font-semibold uppercase tracking-wider text-ink-500 mb-3">Company</p>
          <ul className="space-y-2 text-sm">
            <li>About</li>
            <li>Marketplace</li>
            <li>Model transparency</li>
          </ul>
        </div>
      </div>
      <div className="border-t border-ink-800 py-5 text-center text-xs text-ink-500">
        © {new Date().getFullYear()} CropSight. All rights reserved.
      </div>
    </footer>
  );
}
