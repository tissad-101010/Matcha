import { type SyntheticEvent, useState } from 'react'

import { navigate } from '../navigation'
import { AuthLayout, buttonClass, fieldClass } from './AuthLayout'
import { errorMessage, postJson } from './api'
import { StatusMessage } from './StatusMessage'

export function LoginPage() {
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function submit(event: SyntheticEvent<HTMLFormElement, SubmitEvent>) {
    event.preventDefault()
    setLoading(true)
    setError('')
    const data = new FormData(event.currentTarget)
    try {
      const result = await postJson<{
        data: { user: { profile_complete: boolean } }
      }>('/auth/login', {
        username: data.get('username'),
        password: data.get('password'),
      })
      navigate(result.data.user.profile_complete ? '/discover' : '/onboarding')
    } catch (reason) {
      setError(errorMessage(reason))
    } finally {
      setLoading(false)
    }
  }

  return (
    <AuthLayout
      title="Connexion"
      subtitle="Connectez-vous avec votre nom d’utilisateur."
    >
      <form
        className="space-y-5"
        onSubmit={(event) => {
          void submit(event)
        }}
      >
        <StatusMessage message={error} />
        <label className="block text-sm font-medium">
          Nom d’utilisateur
          <input
            className={fieldClass}
            name="username"
            autoComplete="username"
            required
          />
        </label>
        <label className="block text-sm font-medium">
          Mot de passe
          <input
            className={fieldClass}
            name="password"
            type="password"
            autoComplete="current-password"
            required
          />
        </label>
        <button className={buttonClass} disabled={loading}>
          {loading ? 'Connexion…' : 'Continuer'}
        </button>
      </form>
      <button
        className="mt-5 text-sm font-medium text-[#d43d37]"
        onClick={() => {
          navigate('/forgot-password')
        }}
      >
        Mot de passe oublié ?
      </button>
      <p className="mt-8 text-sm text-[#755f6d]">
        Pas encore de compte ?{' '}
        <button
          className="font-semibold text-[#d43d37]"
          onClick={() => {
            navigate('/register')
          }}
        >
          Créer mon compte
        </button>
      </p>
    </AuthLayout>
  )
}
