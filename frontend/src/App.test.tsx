import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from '@testing-library/react'
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

  it('renders ranked discovery cards from the API', async () => {
    window.history.replaceState({}, '', '/discover')
    const responses = [
      { data: { csrf_token: 'csrf' } },
      {
        data: [
          {
            id: 'profile-1',
            first_name: 'Ada',
            age: 30,
            main_photo: null,
            tags: [{ id: 'tag-1', name: 'Cinéma' }],
            location: {
              city: 'Paris',
              district: null,
              distance_km: 2.4,
              same_zone: true,
            },
            popularity: 42,
            presence: { online: true, last_seen_at: null },
            common_tags: 1,
          },
        ],
        meta: { next_cursor: null, count: 1 },
      },
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
      await screen.findByRole('heading', { name: 'Ada, 30' }),
    ).toBeVisible()
    expect(screen.getByText(/même zone/i)).toBeVisible()
    expect(screen.getByText('42/100')).toBeVisible()
  })

  it('combines and preserves advanced search criteria', async () => {
    window.history.replaceState({}, '', '/search')
    const emptyPage = { data: [], meta: { next_cursor: null, count: 0 } }
    const responses = [
      { data: { csrf_token: 'csrf' } },
      emptyPage,
      {
        data: [
          {
            id: '00000000-0000-4000-8000-000000000010',
            city: 'Paris',
            district: null,
            label: 'Paris',
          },
        ],
      },
      emptyPage,
    ]
    const fetchMock = vi.fn().mockImplementation(() =>
      Promise.resolve({
        ok: true,
        status: 200,
        json: () => Promise.resolve(responses.shift()),
      }),
    )
    vi.stubGlobal('fetch', fetchMock)
    render(<App />)

    expect(
      await screen.findByRole('heading', {
        name: 'Trouvez des profils selon vos critères',
      }),
    ).toBeVisible()
    fireEvent.change(screen.getByLabelText('Âge minimum'), {
      target: { value: '25' },
    })
    fireEvent.change(screen.getByLabelText('Localisation'), {
      target: { value: '00000000-0000-4000-8000-000000000010' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Appliquer' }))

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith(
        expect.stringContaining('/search/profiles?'),
        expect.anything(),
      )
    })
    const requestedUrl = String(fetchMock.mock.calls.at(-1)?.[0])
    expect(requestedUrl).toContain('age_min=25')
    expect(requestedUrl).toContain(
      'location_id=00000000-0000-4000-8000-000000000010',
    )
    expect(screen.getByLabelText('Âge minimum')).toHaveValue(25)
  })
})
