import { useEffect, useState } from 'react'
import { navigate } from '../navigation'
import { AuthLayout, buttonClass } from './AuthLayout'
import { errorMessage, postJson } from './api'
import { StatusMessage } from './StatusMessage'

export function VerifyEmailPage() {
  const token = new URLSearchParams(window.location.search).get('token')
  const email = sessionStorage.getItem('verification_email') ?? ''
  const [state, setState] = useState(token ? 'loading' : 'pending')
  const [message, setMessage] = useState('')

  useEffect(() => {
    if (!token) return
    void postJson('/auth/verify-email', { token })
      .then(() => {
        setState('verified')
      })
      .catch((reason: unknown) => {
        setMessage(errorMessage(reason))
        setState('error')
      })
  }, [token])

  async function resend() {
    const result = await postJson<{ data: { message: string } }>(
      '/auth/resend-verification',
      { email },
    )
    setMessage(result.data.message)
  }

  return (
    <AuthLayout
      title={state === 'verified' ? 'Compte vérifié' : 'Vérifiez votre e-mail'}
      subtitle={
        state === 'verified'
          ? 'Votre compte est actif. Vous pouvez maintenant compléter votre profil.'
          : 'Nous vous avons envoyé un lien unique, valable 24 heures.'
      }
    >
      <div className="space-y-5">
        <StatusMessage message={message} success={state !== 'error'} />
        {state === 'loading' && <p role="status">Vérification en cours…</p>}
        {state === 'verified' ? (
          <button
            className={buttonClass}
            onClick={() => {
              navigate('/')
            }}
          >
            Se connecter pour compléter mon profil
          </button>
        ) : (
          <>
            <button
              className={buttonClass}
              disabled={!email}
              onClick={() => {
                void resend()
              }}
            >
              Renvoyer l’e-mail
            </button>
            <button
              className="w-full text-sm font-semibold text-[#d43d37]"
              onClick={() => {
                navigate('/')
              }}
            >
              Retour à la connexion
            </button>
          </>
        )}
      </div>
    </AuthLayout>
  )
}
