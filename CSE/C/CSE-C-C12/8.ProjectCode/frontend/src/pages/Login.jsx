import { useEffect } from 'react'
import AuthForm from './AuthForm'

export default function Login() {
  useEffect(() => {
    document.title = 'Sign in - CareLens AI'
  }, [])
  return <AuthForm mode="login" />
}
