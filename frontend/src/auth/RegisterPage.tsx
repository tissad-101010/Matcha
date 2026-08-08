import { type SyntheticEvent, useState } from 'react'

import { navigate } from '../navigation'
import { AuthLayout, buttonClass, fieldClass } from './AuthLayout'
import { errorMessage, postJson } from './api'
import { StatusMessage } from './StatusMessage'

const fields = [
  ['first_name', 'Prénom', 'given-name'],
  ['last_name', 'Nom', 'family-name'],
  ['username', 'Nom d’utilisateur', 'username'],
  ['email', 'E-mail', 'email'],
] as const

export function RegisterPage() {
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function submit(event: SyntheticEvent<HTMLFormElement, SubmitEvent>) {
    event.preventDefault()
    setLoading(true)
    setError('')
    const data = Object.fromEntries(new FormData(event.currentTarget))
    try {
      await postJson('/auth/register', data)
      sessionStorage.setItem('verification_email', data.email as string)
      navigate('/verify-email')
    } catch (reason) {
      setError(errorMessage(reason))
    } finally {
      setLoading(false)
    }
  }

  return (
    <AuthLayout
      title="Créer mon compte"
      subtitle="C’est rapide, gratuit et réservé aux personnes de 18 ans ou plus."
    >
      <form
        className="space-y-4"
        onSubmit={(event) => {
          void submit(event)
        }}
      >
        <StatusMessage message={error} />
        <div className="grid gap-4 sm:grid-cols-2">
          {fields.slice(0, 2).map(([name, label, complete]) => (
            <label className="text-sm font-medium" key={name}>
              {label}
              <input
                className={fieldClass}
                name={name}
                autoComplete={complete}
                required
              />
            </label>
          ))}
        </div>
        {fields.slice(2).map(([name, label, complete]) => (
          <label className="block text-sm font-medium" key={name}>
            {label}
            <input
              className={fieldClass}
              name={name}
              type={name === 'email' ? 'email' : 'text'}
              autoComplete={complete}
              required
            />
          </label>
        ))}
        <label className="block text-sm font-medium">
          Date de naissance
          <input
            className={fieldClass}
            name="birth_date"
            type="date"
            required
          />
        </label>
        <label className="block text-sm font-medium">
          Mot de passe
          <input
            className={fieldClass}
            name="password"
            type="password"
            autoComplete="new-password"
            minLength={12}
            required
          />
        </label>
        <p className="text-xs leading-5 text-[#755f6d]">
          12 caractères minimum, avec majuscule, minuscule, chiffre et caractère
          spécial. Les mots anglais courants sont refusés.
        </p>
        <button className={buttonClass} disabled={loading}>
          {loading ? 'Création…' : 'Créer mon compte'}
        </button>
      </form>
      <button
        className="mt-6 text-sm font-semibold text-[#d43d37]"
        onClick={() => {
          navigate('/')
        }}
      >
        Déjà un compte ? Se connecter
      </button>
    </AuthLayout>
  )
}
