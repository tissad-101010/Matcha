import {
  act,
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { App } from './App'

const realtime = vi.hoisted(() => ({
  handlers: new Map<string, (payload: unknown) => void>(),
}))

vi.mock('socket.io-client', () => ({
  io: vi.fn(() => ({
    on: vi.fn((event: string, handler: (payload: unknown) => void) => {
      realtime.handlers.set(event, handler)
    }),
    emit: vi.fn(),
    disconnect: vi.fn(),
  })),
}))

describe('authentication experience', () => {
  afterEach(() => {
    cleanup()
    vi.unstubAllGlobals()
  })
  beforeEach(() => {
    window.history.replaceState({}, '', '/')
    sessionStorage.clear()
    realtime.handlers.clear()
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
    const getCurrentPosition = vi.fn((success: PositionCallback) => {
      success({
        coords: { latitude: 48.85, longitude: 2.35 },
      } as GeolocationPosition)
    })
    Object.defineProperty(window.navigator, 'geolocation', {
      configurable: true,
      value: { getCurrentPosition },
    })
    const responses: unknown[] = [
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
    expect(screen.getByText('Votre genre')).toBeVisible()
    expect(getCurrentPosition).not.toHaveBeenCalled()
    responses.push(null, {
      data: {
        catalog_location_id: 'location-1',
        city: 'Paris',
        source: 'gps_reduced',
      },
    })
    fireEvent.click(
      screen.getByRole('button', {
        name: /utiliser ma position approximative/i,
      }),
    )
    await waitFor(() => {
      expect(getCurrentPosition).toHaveBeenCalledOnce()
    })
    expect(
      await screen.findByRole('button', {
        name: /retirer mon consentement gps/i,
      }),
    ).toBeVisible()
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

  it('renders an allowlisted detailed public profile', async () => {
    window.history.replaceState(
      {},
      '',
      '/profiles/00000000-0000-4000-8000-000000000010',
    )
    const responses = [
      {
        data: {
          id: '00000000-0000-4000-8000-000000000010',
          username: 'ada42',
          first_name: 'Ada',
          last_name: 'Lovelace',
          age: 30,
          gender: 'woman',
          desired_genders: ['man', 'non_binary'],
          bio: 'Mathématiques et poésie.',
          photos: [],
          tags: [{ id: 'tag-1', name: 'Sciences' }],
          location: { city: 'Paris', district: null },
          popularity: 73,
          presence: { online: true, last_seen_at: null },
          viewer_state: {
            liked_by_me: false,
            likes_me: true,
            matched: false,
            match_id: null,
            can_like: true,
            can_message: false,
          },
        },
      },
      { data: { csrf_token: 'csrf' } },
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
      await screen.findByRole('heading', { name: 'Ada Lovelace, 30' }),
    ).toBeVisible()
    expect(screen.getByText('@ada42')).toBeVisible()
    expect(screen.getByText('73/100')).toBeVisible()
    expect(screen.getByText(/vous a déjà liké/i)).toBeVisible()
    expect(
      screen.getByRole('button', { name: 'Liker la photo de profil' }),
    ).toBeEnabled()
    expect(screen.queryByText(/e-mail/i)).not.toBeInTheDocument()
  })

  it('likes a public profile and immediately displays the match state', async () => {
    window.history.replaceState(
      {},
      '',
      '/profiles/00000000-0000-4000-8000-000000000010',
    )
    const profile = {
      id: '00000000-0000-4000-8000-000000000010',
      username: 'ada42',
      first_name: 'Ada',
      last_name: 'Lovelace',
      age: 30,
      gender: 'woman',
      desired_genders: ['man'],
      bio: 'Bio',
      photos: [],
      tags: [],
      location: { city: 'Paris', district: null },
      popularity: 50,
      presence: { online: true, last_seen_at: null },
      viewer_state: {
        liked_by_me: false,
        likes_me: true,
        matched: false,
        match_id: null,
        can_like: true,
        can_message: false,
      },
    }
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: () => Promise.resolve({ data: profile }),
      })
      .mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: () => Promise.resolve({ data: { csrf_token: 'csrf' } }),
      })
      .mockResolvedValueOnce({
        ok: true,
        status: 204,
        json: () => Promise.resolve(null),
      })
      .mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: () =>
          Promise.resolve({
            data: { liked: true, matched: true, match_id: 'match-1' },
          }),
      })
    vi.stubGlobal('fetch', fetchMock)
    render(<App />)
    fireEvent.click(
      await screen.findByRole('button', { name: 'Liker la photo de profil' }),
    )
    expect(
      await screen.findByRole('button', { name: 'Se déconnecter' }),
    ).toBeVisible()
    expect(screen.getByText('Vous êtes connectés.')).toBeVisible()
  })

  it('submits a controlled profile report', async () => {
    window.history.replaceState(
      {},
      '',
      '/profiles/00000000-0000-4000-8000-000000000010',
    )
    const profile = {
      id: '00000000-0000-4000-8000-000000000010',
      username: 'ada42',
      first_name: 'Ada',
      last_name: 'Lovelace',
      age: 30,
      gender: 'woman',
      desired_genders: ['man'],
      bio: 'Bio',
      photos: [],
      tags: [],
      location: { city: 'Paris', district: null },
      popularity: 50,
      presence: { online: true, last_seen_at: null },
      viewer_state: {
        liked_by_me: false,
        likes_me: false,
        matched: false,
        match_id: null,
        can_like: true,
        can_message: false,
      },
    }
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: () => Promise.resolve({ data: profile }),
      })
      .mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: () => Promise.resolve({ data: { csrf_token: 'csrf' } }),
      })
      .mockResolvedValueOnce({
        ok: true,
        status: 204,
        json: () => Promise.resolve(null),
      })
      .mockResolvedValueOnce({
        ok: true,
        status: 201,
        json: () => Promise.resolve({ data: { id: 'report-1' } }),
      })
    vi.stubGlobal('fetch', fetchMock)
    render(<App />)
    fireEvent.click(await screen.findByRole('button', { name: 'Signaler' }))
    fireEvent.change(screen.getByLabelText('Motif du signalement'), {
      target: { value: 'spam' },
    })
    fireEvent.change(screen.getByLabelText('Description facultative'), {
      target: { value: 'Messages répétés' },
    })
    fireEvent.click(
      screen.getByRole('button', { name: 'Envoyer le signalement' }),
    )
    expect(
      await screen.findByRole('button', { name: 'Signalement envoyé' }),
    ).toBeDisabled()
    expect(fetchMock).toHaveBeenLastCalledWith(
      '/api/v1/profiles/00000000-0000-4000-8000-000000000010/reports',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({
          reason: 'spam',
          description: 'Messages répétés',
        }),
      }),
    )
  })

  it('displays a like notification received in real time on a private page', async () => {
    window.history.replaceState({}, '', '/discover')
    const responses = [
      { data: { csrf_token: 'csrf' } },
      { data: [], meta: { next_cursor: null, count: 0 } },
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
    await screen.findByText(/aucune suggestion pour le moment/i)
    act(() => {
      realtime.handlers.get('notification.created')?.({
        id: 'notification-1',
        type: 'like_received',
        actor_user_id: 'profile-1',
        created_at: '2026-08-28T09:20:00+00:00',
      })
    })
    expect(
      await screen.findByText(/vient de recevoir un nouveau like/i),
    ).toHaveAttribute('role', 'status')
  })

  it('updates a displayed relationship immediately from Socket.IO', async () => {
    window.history.replaceState(
      {},
      '',
      '/profiles/00000000-0000-4000-8000-000000000010',
    )
    const profile = {
      id: '00000000-0000-4000-8000-000000000010',
      username: 'ada42',
      first_name: 'Ada',
      last_name: 'Lovelace',
      age: 30,
      gender: 'woman',
      desired_genders: ['man'],
      bio: 'Bio',
      photos: [],
      tags: [],
      location: { city: 'Paris', district: null },
      popularity: 50,
      presence: { online: true, last_seen_at: null },
      viewer_state: {
        liked_by_me: true,
        likes_me: false,
        matched: false,
        match_id: null,
        can_like: true,
        can_message: false,
      },
    }
    const responses = [
      { data: profile },
      { data: { csrf_token: 'csrf' } },
      null,
    ]
    vi.stubGlobal(
      'fetch',
      vi.fn().mockImplementation(() =>
        Promise.resolve({
          ok: true,
          status: responses.length === 1 ? 204 : 200,
          json: () => Promise.resolve(responses.shift()),
        }),
      ),
    )
    render(<App />)
    await screen.findByText('Vous avez déjà liké ce profil.')
    act(() => {
      realtime.handlers.get('relationship.updated')?.({
        target_user_id: profile.id,
        liked_by_me: true,
        likes_me: true,
        matched: true,
        match_id: 'match-1',
      })
    })
    expect(await screen.findByText('Vous êtes connectés.')).toBeVisible()
    expect(screen.getByRole('button', { name: 'Se déconnecter' })).toBeVisible()
  })

  it('shows the authenticated empty conversation state', async () => {
    window.history.replaceState({}, '', '/messages')
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
        json: () => Promise.resolve({ data: [], meta: { count: 0 } }),
      }),
    )
    render(<App />)
    expect(await screen.findByText(/aucune conversation/i)).toBeVisible()
    expect(screen.getByRole('heading', { name: 'Messages' })).toBeVisible()
  })

  it('shows visitors and received likes without blocked-profile assumptions', async () => {
    window.history.replaceState({}, '', '/activity')
    const responses = [
      {
        data: [
          {
            visitor: {
              id: 'profile-1',
              first_name: 'Ada',
              age: 31,
              popularity: 72,
              location: { city: 'Paris', district: null },
              main_photo: null,
            },
            visited_at: '2026-08-31T12:00:00+00:00',
          },
        ],
      },
      { data: [] },
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
    expect(await screen.findByText('Ada, 31')).toBeVisible()
    fireEvent.click(screen.getByRole('tab', { name: 'Likes reçus' }))
    expect(screen.getByText(/aucune activité/i)).toBeVisible()
  })
})
