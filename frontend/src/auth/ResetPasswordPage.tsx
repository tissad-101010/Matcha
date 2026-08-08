import { type SyntheticEvent, useState } from 'react'
import { navigate } from '../navigation'
import { AuthLayout, buttonClass, fieldClass } from './AuthLayout'
import { errorMessage, postJson } from './api'
import { StatusMessage } from './StatusMessage'

export function ResetPasswordPage() {
  const [message, setMessage] = useState('')
  const token = new URLSearchParams(window.location.search).get('token') ?? ''
  async function submit(event: SyntheticEvent<HTMLFormElement, SubmitEvent>) {
    event.preventDefault()
    const form = new FormData(event.currentTarget)
    if (form.get('password') !== form.get('confirmation')) {
      setMessage('Les mots de passe ne correspondent pas.')
      return
    }
    try {
      await postJson('/auth/reset-password', {
        token,
        new_password: form.get('password'),
      })
      navigate('/')
    } catch (reason) {
      setMessage(errorMessage(reason))
    }
  }
  return (
    <AuthLayout
      title="Nouveau mot de passe"
      subtitle="Choisissez un mot de passe fort différent de l’ancien."
    >
      <form
        className="space-y-5"
        onSubmit={(event) => {
          void submit(event)
        }}
      >
        <StatusMessage message={message} />
        <label className="block text-sm font-medium">
          Nouveau mot de passe
          <input
            className={fieldClass}
            name="password"
            type="password"
            autoComplete="new-password"
            minLength={12}
            required
          />
        </label>
        <label className="block text-sm font-medium">
          Confirmer le mot de passe
          <input
            className={fieldClass}
            name="confirmation"
            type="password"
            autoComplete="new-password"
            required
          />
        </label>
        <button className={buttonClass} disabled={!token}>
          Changer mon mot de passe
        </button>
      </form>
    </AuthLayout>
  )
}
