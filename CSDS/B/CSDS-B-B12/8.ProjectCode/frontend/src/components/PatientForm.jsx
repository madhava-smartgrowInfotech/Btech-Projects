import { useState } from 'react'
import { UserPlus } from 'lucide-react'
import api, { errorMessage } from '../api.js'
import { Alert, Button, Input, Select } from './ui/index.js'
import { useToast } from './ui/Toast.jsx'

const EMPTY = { name: '', phone: '', age: '', sex: 'Male' }

/** Register a patient. Calls onCreated with the saved patient. */
export default function PatientForm({ onCreated, nameRef, idPrefix = 'patient' }) {
  const toast = useToast()
  const [form, setForm] = useState(EMPTY)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }))

  const submit = async (e) => {
    e.preventDefault()
    setBusy(true)
    setError('')
    try {
      const body = { name: form.name.trim(), phone: form.phone.trim(), age: Number(form.age), sex: form.sex }
      const { data } = await api.post('/patients', body)
      setForm(EMPTY)
      toast.success(`Registered ${data.code}.`)
      onCreated?.(data)
    } catch (err) {
      setError(await errorMessage(err))
    } finally {
      setBusy(false)
    }
  }

  return (
    <form onSubmit={submit} className="page" style={{ gap: 14 }}>
      <Input ref={nameRef} id={`${idPrefix}-name`} label="Full name" value={form.name} onChange={set('name')} required maxLength={120} autoComplete="off" />
      <div className="form-row">
        <Input id={`${idPrefix}-age`} label="Age" type="number" min={0} max={120} value={form.age} onChange={set('age')} required />
        <Select id={`${idPrefix}-sex`} label="Sex" value={form.sex} onChange={set('sex')}>
          <option>Male</option>
          <option>Female</option>
          <option>Other</option>
        </Select>
      </div>
      <Input id={`${idPrefix}-phone`} label="Phone (optional)" type="tel" value={form.phone} onChange={set('phone')} maxLength={20} autoComplete="off" />
      {error && <Alert tone="error">{error}</Alert>}
      <Button type="submit" variant="secondary" icon={UserPlus} loading={busy} block>
        {busy ? 'Saving…' : 'Register patient'}
      </Button>
    </form>
  )
}
