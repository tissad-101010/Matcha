import { type SyntheticEvent, useState } from 'react'
import { navigate } from '../navigation'
import { AuthLayout, buttonClass, fieldClass } from './AuthLayout'
import { postJson } from './api'
import { StatusMessage } from './StatusMessage'

export function ForgotPasswordPage() {
  const [message, setMessage] = useState('')
  async function submit(event: SyntheticEvent<HTMLFormElement, SubmitEvent>) {
    event.preventDefault()
    const email = new FormData(event.currentTarget).get('email')
    const result = await postJson<{ data: { message: string } }>(
      '/auth/forgot-password',
      { email },
    )
    setMessage(result.data.message)
  }
  return (
    <AuthLayout
      title="Mot de passe oublié"
      subtitle="Entrez votre e-mail pour recevoir un lien valable 30 minutes."
    >
      <form
        className="space-y-5"
        onSubmit={(event) => {
          void submit(event)
        }}
      >
        <StatusMessage message={message} success />
        <label className="block text-sm font-medium">
          E-mail
          <input
            className={fieldClass}
            name="email"
            type="email"
            autoComplete="email"
            required
          />
        </label>
        <button className={buttonClass}>Envoyer le lien</button>
      </form>
      <button
        className="mt-6 text-sm font-semibold text-[#d43d37]"
        onClick={() => {
          navigate('/')
        }}
      >
        Retour à la connexion
      </button>
    </AuthLayout>
  )
}
