import { useState } from 'react'
import { LogIn, UserPlus } from 'lucide-react'
import { api } from '../lib/api'
import { useAuth } from '../lib/auth'
import { useConfig } from '../lib/config'
import { Alert, Button, Input, useToast } from './ui'
import { FacePhotoInput } from './FacePhotoInput'

/** Mirrors ui/common.login_form: role-specific label, wrong-portal guard, welcome message. */
export function LoginForm({ role, defaultUsername = '', onSuccess }) {
  const { login } = useAuth()
  const toast = useToast()
  const [username, setUsername] = useState(defaultUsername)
  const [password, setPassword] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  const submit = async (e) => {
    e.preventDefault()
    setError('')
    if (!username.trim() || !password) {
      setError('Enter your username and password.')
      return
    }
    setBusy(true)
    try {
      const d = await login(username, password, role)
      toast.success(`Welcome, ${d.user.full_name}! (JWT issued, valid ${d.jwt_expiry_minutes} min)`)
      onSuccess?.(d.user)
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <form className="stack" onSubmit={submit} noValidate>
      <Input
        label={role === 'student' ? 'Roll number or username' : 'Username / email'}
        autoComplete="username"
        value={username}
        onChange={(e) => setUsername(e.target.value)}
        placeholder={role === 'student' ? '23K91A6706' : 'faculty@college.edu'}
        data-autofocus
      />
      <Input label="Password" type="password" autoComplete="current-password" value={password} onChange={(e) => setPassword(e.target.value)} />
      {error && <Alert tone="error">{error}</Alert>}
      <Button type="submit" variant="primary" size="lg" icon={LogIn} loading={busy} block>
        Sign in
      </Button>
    </form>
  )
}

/** Mirrors ui/common.register_form (students enrol a neutral reference face). */
export function RegisterForm({ role, onRegistered }) {
  const { config } = useConfig()
  const toast = useToast()
  const [fullName, setFullName] = useState('')
  const [roll, setRoll] = useState('')
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [face, setFace] = useState(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [errors, setErrors] = useState({})

  const requireFace = role === 'student' && (config ? config.require_enrollment : true)

  const submit = async (e) => {
    e.preventDefault()
    setError('')
    const errs = {}
    if (!fullName.trim()) errs.fullName = 'Full name is required.'
    if (role === 'student' && !roll.trim()) errs.roll = 'Roll number is required for students.'
    if (role === 'faculty' && !username.trim()) errs.username = 'Username / email is required.'
    if (password.length < 6) errs.password = 'Use at least 6 characters.'
    if (requireFace && !face) errs.face = 'A reference face photo is required for student registration.'
    setErrors(errs)
    if (Object.keys(errs).length) return
    const form = new FormData()
    form.append('role', role)
    form.append('full_name', fullName)
    form.append('password', password)
    form.append('username', username)
    if (role === 'student') form.append('roll_number', roll)
    if (face) form.append('face', face, face.name || 'face.jpg')
    setBusy(true)
    try {
      const d = await api('/api/auth/register', { method: 'POST', form, auth: false })
      toast.success(d.message)
      onRegistered?.(d.user)
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <form className="stack" onSubmit={submit} noValidate>
      <Input label="Full name" autoComplete="name" value={fullName} onChange={(e) => setFullName(e.target.value)} error={errors.fullName} data-autofocus />
      {role === 'student' ? (
        <>
          <Input label="Roll number (hall-ticket no.)" placeholder="23K91A6706" value={roll} onChange={(e) => setRoll(e.target.value)} error={errors.roll} />
          <Input label="Username (optional)" hint="Defaults to your roll number." value={username} onChange={(e) => setUsername(e.target.value)} autoComplete="username" />
        </>
      ) : (
        <Input label="Username / email" value={username} onChange={(e) => setUsername(e.target.value)} error={errors.username} autoComplete="username" />
      )}
      <Input label="Password (min 6 chars)" type="password" autoComplete="new-password" value={password} onChange={(e) => setPassword(e.target.value)} error={errors.password} />
      {role === 'student' && (
        <div className="stack" style={{ '--gap': '8px' }}>
          <span className="field-label">Reference face photo{requireFace ? '' : ' (optional)'}</span>
          <p className="small muted">Enrol your reference face now. Look straight at the camera, good light, no mask/cap.</p>
          <FacePhotoInput label="Reference face" value={face} onChange={setFace} mirrored={config?.camera_mirrored ?? true} />
          {errors.face && <span className="field-error">{errors.face}</span>}
        </div>
      )}
      {error && <Alert tone="error">{error}</Alert>}
      <Button type="submit" variant="primary" size="lg" icon={UserPlus} loading={busy} block>
        {busy && role === 'student' ? 'Checking face & creating account…' : 'Create account'}
      </Button>
    </form>
  )
}
