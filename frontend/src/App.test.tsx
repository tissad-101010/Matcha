import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { App } from './App'

describe('authentication experience', () => {
  afterEach(() => {
    cleanup()
    vi.unstubAllGlobals()
  })
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

  it('loads the mandatory onboarding from real API contracts', async () => {
    window.history.replaceState({}, '', '/onboarding')
    const responses = [
      { data: { csrf_token: 'csrf' } },
      {
        data: {
          first_name: 'Ada',
          last_name: 'Lovelace',
          birth_date: '1990-12-10',
          gender: null,
          bio: null,
          desired_genders: [],
          tags: [],
          photos: [],
          location: null,
          consents: [],
          profile_complete: false,
          missing_profile_fields: ['gender', 'bio', 'tags', 'location'],
        },
      },
      { data: [{ id: 'tag-1', name: 'Cinéma' }] },
      {
        data: [
          {
            id: 'location-1',
            city: 'Paris',
            district: null,
            label: 'Paris',
          },
        ],
      },
      { data: [], meta: { current_policy_version: '2026-08' } },
    ]
    vi.stubGlobal(
      'fetch',
      vi.fn().mockImplementation(() =>
        Promise.resolve({
          ok: true,
          status: 200,
          json: () => Promise.resolve(responses.shift()),
        }),
      ),
    )

    render(<App />)

    expect(
      await screen.findByRole('heading', { name: 'Votre profil' }),
    ).toBeVisible()
    expect(screen.getByText('Préférences et consentement')).toBeVisible()
    expect(screen.getByText('Centres d’intérêt')).toBeVisible()
    expect(screen.getByText('Localisation approximative')).toBeVisible()
    expect(screen.getByText('Photos facultatives')).toBeVisible()
    expect(screen.getByLabelText(/je consens explicitement/i)).not.toBeChecked()
  })
})
