import { useEffect, useState } from 'react'

import { ForgotPasswordPage } from './auth/ForgotPasswordPage'
import { LoginPage } from './auth/LoginPage'
import { RegisterPage } from './auth/RegisterPage'
import { ResetPasswordPage } from './auth/ResetPasswordPage'
import { VerifyEmailPage } from './auth/VerifyEmailPage'

function currentPath() {
  return window.location.pathname
}

export function App() {
  const [path, setPath] = useState(currentPath)

  useEffect(() => {
    const updatePath = () => {
      setPath(currentPath())
    }
    window.addEventListener('popstate', updatePath)
    return () => {
      window.removeEventListener('popstate', updatePath)
    }
  }, [])

  if (path === '/register') return <RegisterPage />
  if (path === '/forgot-password') return <ForgotPasswordPage />
  if (path === '/reset-password') return <ResetPasswordPage />
  if (path === '/verify-email') return <VerifyEmailPage />
  return <LoginPage />
}
