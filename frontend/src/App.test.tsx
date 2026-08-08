import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it } from 'vitest'

import { App } from './App'

describe('authentication experience', () => {
  afterEach(cleanup)
  beforeEach(() => {
    window.history.replaceState({}, '', '/')
  })

  it('renders the login screen from the UX contract', () => {
    render(<App />)

    expect(screen.getByRole('heading', { name: 'Connexion' })).toBeVisible()
    expect(screen.getByLabelText('Nom d’utilisateur')).toHaveAttribute(
      'autocomplete',
      'username',
    )
    expect(screen.getByText(/réservé aux personnes majeures/i)).toBeVisible()
  })

  it('navigates to the complete mandatory registration form', () => {
    render(<App />)
    fireEvent.click(screen.getByRole('button', { name: 'Créer mon compte' }))

    expect(
      screen.getByRole('heading', { name: 'Créer mon compte' }),
    ).toBeVisible()
    expect(screen.getByLabelText('Prénom')).toBeRequired()
    expect(screen.getByLabelText('Nom')).toBeRequired()
    expect(screen.getByLabelText('Nom d’utilisateur')).toBeRequired()
    expect(screen.getByLabelText('E-mail')).toBeRequired()
    expect(screen.getByLabelText('Date de naissance')).toBeRequired()
    expect(screen.getByLabelText('Mot de passe')).toBeRequired()
  })
})
