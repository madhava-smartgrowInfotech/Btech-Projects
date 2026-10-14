import { ClipboardList, GitBranch, LayoutDashboard, Stethoscope, Ticket } from 'lucide-react'

// Sidebar links per role. Every role sees Referrals; each role's landing page is homeFor() in auth.jsx.
const LINKS = {
  patient: [
    { to: '/book', label: 'Book a visit', icon: Stethoscope },
    { to: '/tokens', label: 'My tokens', icon: Ticket },
    { to: '/referrals', label: 'Referrals', icon: GitBranch },
  ],
  staff: [
    { to: '/console', label: 'Hospital console', icon: ClipboardList },
    { to: '/referrals', label: 'Referrals', icon: GitBranch },
  ],
  admin: [
    { to: '/dashboard', label: 'District dashboard', icon: LayoutDashboard },
    { to: '/console', label: 'Hospital console', icon: ClipboardList },
    { to: '/referrals', label: 'Referrals', icon: GitBranch },
  ],
}

export const navFor = (user) => (user ? LINKS[user.role] || [] : [])
