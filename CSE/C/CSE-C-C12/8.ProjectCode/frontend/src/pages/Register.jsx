import { useEffect } from 'react'
import AuthForm from './AuthForm'

export default function Register() {
  useEffect(() => {
    document.title = 'Create account - CareLens AI'
  }, [])
  return <AuthForm mode="register" />
}
