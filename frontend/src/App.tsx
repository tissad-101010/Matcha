import { useEffect, useState } from 'react'

import { ForgotPasswordPage } from './auth/ForgotPasswordPage'
import { LoginPage } from './auth/LoginPage'
import { RegisterPage } from './auth/RegisterPage'
import { ResetPasswordPage } from './auth/ResetPasswordPage'
import { VerifyEmailPage } from './auth/VerifyEmailPage'
import { OnboardingPage } from './onboarding/OnboardingPage'
import { DiscoveryPage } from './discovery/DiscoveryPage'
import { PublicProfilePage } from './discovery/PublicProfilePage'
import { RealtimeNotifications } from './realtime/RealtimeNotifications'

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

  const authenticated =
    path === '/onboarding' ||
    path === '/discover' ||
    path === '/search' ||
    path.startsWith('/profiles/')

  return (
    <>
      <RealtimeNotifications enabled={authenticated} />
      {pageForPath(path)}
    </>
  )
}

function pageForPath(path: string) {
  if (path === '/register') return <RegisterPage />
  if (path === '/forgot-password') return <ForgotPasswordPage />
  if (path === '/reset-password') return <ResetPasswordPage />
  if (path === '/verify-email') return <VerifyEmailPage />
  if (path === '/onboarding') return <OnboardingPage />
  if (path === '/discover') return <DiscoveryPage />
  if (path === '/search') return <DiscoveryPage advanced />
  if (path.startsWith('/profiles/')) {
    return <PublicProfilePage profileId={path.slice('/profiles/'.length)} />
  }
  return <LoginPage />
}
