import { Phone } from 'lucide-react'
import { Button, Card } from '../components/ui'
import { EMERGENCY_CONTACTS } from '../lib/format'

export function ContactsCard() {
  return (
    <Card title="Emergency contacts">
      <div className="stack" style={{ '--gap': '10px' }}>
        {EMERGENCY_CONTACTS.map((c) => (
          <div key={c.number} className="row-between">
            <span style={{ fontWeight: 600 }}>{c.label}</span>
            <Button size="sm" icon={Phone} href={`tel:${c.number}`} aria-label={`Call ${c.label} on ${c.number}`}>
              {c.number}
            </Button>
          </div>
        ))}
      </div>
    </Card>
  )
}
