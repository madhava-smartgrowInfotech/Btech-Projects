import { useState } from 'react'
import { CreditCard, ExternalLink } from 'lucide-react'
import { Button, useToast } from './ui'
import { Api } from '../lib/api'
import { money } from '../lib/format'

/**
 * Payment controls for one reservation.
 * - demo provider (no Stripe keys): the backend marks the payment paid when confirmed here.
 * - stripe provider: the checkout page opens in a new tab; Stripe's webhook marks it paid.
 */
export default function PayActions({ rid, amount, provider, url, onPaid, size }) {
  const toast = useToast()
  const [busy, setBusy] = useState(false)

  if (provider === 'stripe') {
    return url ? (
      <Button as="a" variant="primary" size={size} icon={ExternalLink} href={url} target="_blank" rel="noreferrer">
        Pay {amount != null ? money(amount) : ''} with Stripe
      </Button>
    ) : (
      <span className="faint">Awaiting Stripe confirmation</span>
    )
  }

  const confirm = async () => {
    setBusy(true)
    try {
      await Api.confirmPayment(rid)
      toast({ tone: 'success', title: 'Payment confirmed', message: `Booking #${rid} is paid.` })
      onPaid?.()
    } catch (e) {
      toast({ tone: 'error', title: 'Payment failed', message: `${e.message} Try again, or contact an admin if it keeps failing.` })
    } finally {
      setBusy(false)
    }
  }
  return (
    <Button variant="primary" size={size} icon={CreditCard} loading={busy} onClick={confirm}>
      {amount != null ? `Confirm demo payment ${money(amount)}` : 'Confirm demo payment'}
    </Button>
  )
}
