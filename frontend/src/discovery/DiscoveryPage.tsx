import { useEffect, useState } from 'react'
import type { SyntheticEvent } from 'react'

import { errorMessage, requestJson } from '../auth/api'
import { navigate } from '../navigation'
import type { ProfileCard } from './types'
import type { LocationSuggestion } from '../onboarding/types'

export function DiscoveryPage({ advanced = false }: { advanced?: boolean }) {
  const [profiles, setProfiles] = useState<ProfileCard[]>([])
  const [csrfToken, setCsrfToken] = useState('')
  const [nextCursor, setNextCursor] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [filters, setFilters] = useState<DiscoveryFilters>(emptyFilters)
  const [appliedFilters, setAppliedFilters] =
    useState<DiscoveryFilters>(emptyFilters)
  const [locations, setLocations] = useState<LocationSuggestion[]>([])
  const availableTags = Array.from(
    new Map(
      profiles.flatMap((profile) => profile.tags).map((tag) => [tag.id, tag]),
    ).values(),
  ).sort((left, right) => left.name.localeCompare(right.name, 'fr'))

  useEffect(() => {
    void loadInitial(advanced)
      .then(({ token, page, locationOptions }) => {
        setCsrfToken(token)
        setProfiles(page.data)
        setNextCursor(page.meta.next_cursor)
        setLocations(locationOptions)
      })
      .catch((reason: unknown) => {
        setError(errorMessage(reason))
      })
      .finally(() => {
        setLoading(false)
      })
  }, [advanced])

  async function loadMore() {
    if (!nextCursor) return
    setLoading(true)
    try {
      const page = await requestJson<DiscoveryResponse>(
        discoveryUrl(appliedFilters, nextCursor, advanced),
      )
      setProfiles((current) => [...current, ...page.data])
      setNextCursor(page.meta.next_cursor)
    } catch (reason) {
      setError(errorMessage(reason))
    } finally {
      setLoading(false)
    }
  }

  async function applyFilters(event: SyntheticEvent<HTMLFormElement>) {
    event.preventDefault()
    setLoading(true)
    setError('')
    try {
      const page = await requestJson<DiscoveryResponse>(
        discoveryUrl(filters, undefined, advanced),
      )
      setAppliedFilters(filters)
      setProfiles(page.data)
      setNextCursor(page.meta.next_cursor)
    } catch (reason) {
      setError(errorMessage(reason))
    } finally {
      setLoading(false)
    }
  }

  async function resetFilters() {
    setFilters(emptyFilters)
    setLoading(true)
    setError('')
    try {
      const page = await requestJson<DiscoveryResponse>(
        discoveryUrl(emptyFilters, undefined, advanced),
      )
      setAppliedFilters(emptyFilters)
      setProfiles(page.data)
      setNextCursor(page.meta.next_cursor)
    } catch (reason) {
      setError(errorMessage(reason))
    } finally {
      setLoading(false)
    }
  }

  async function logout() {
    await requestJson('/auth/logout', 'POST', undefined, csrfToken)
    navigate('/')
  }

  return (
    <main className="min-h-screen bg-[#fffaf7] text-[#281320]">
      <header className="sticky top-0 z-10 border-b border-[#efdeda] bg-white/95 px-4 py-4 backdrop-blur sm:px-8">
        <div className="mx-auto flex max-w-6xl items-center justify-between">
          <p className="text-2xl font-bold text-[#35102d]">
            <span className="text-[#ff5149]" aria-hidden="true">
              ♥
            </span>{' '}
            matcha
          </p>
          <nav
            className="flex items-center gap-5 text-sm font-semibold"
            aria-label="Navigation principale"
          >
            <button
              onClick={() => {
                navigate('/messages')
              }}
            >
              Messages
            </button>
            <button
              onClick={() => {
                navigate('/activity')
              }}
            >
              Activité
            </button>
            <button
              onClick={() => {
                navigate('/onboarding')
              }}
            >
              Mon profil
            </button>
            <button
              className={advanced ? '' : 'text-[#d43d37]'}
              onClick={() => {
                navigate('/discover')
              }}
            >
              Découvrir
            </button>
            <button
              className={advanced ? 'text-[#d43d37]' : ''}
              onClick={() => {
                navigate('/search')
              }}
            >
              Rechercher
            </button>
            <button
              onClick={() => {
                navigate('/onboarding')
              }}
            >
              Mon profil
            </button>
            <button onClick={() => void logout()}>Déconnexion</button>
          </nav>
        </div>
      </header>
      <div className="mx-auto max-w-6xl px-4 py-10 sm:px-8">
        <section className="flex flex-wrap items-end justify-between gap-4">
          <div>
            <p className="text-sm font-semibold tracking-[0.18em] text-[#d43d37] uppercase">
              {advanced ? 'Recherche avancée' : 'Suggestions compatibles'}
            </p>
            <h1 className="mt-2 text-4xl font-bold text-[#35102d]">
              {advanced
                ? 'Trouvez des profils selon vos critères'
                : 'Des profils faits pour se rencontrer'}
            </h1>
            <p className="mt-3 max-w-2xl text-sm leading-6 text-[#755f6d]">
              Priorité à votre zone, puis classement transparent selon la
              proximité, les centres d’intérêt communs et la popularité.
            </p>
          </div>
          <p className="rounded-full bg-white px-4 py-2 text-sm shadow-sm">
            {profiles.length} profil{profiles.length > 1 ? 's' : ''} affiché
            {profiles.length > 1 ? 's' : ''}
          </p>
        </section>
        <form
          className="mt-8 rounded-3xl border border-[#efdeda] bg-white p-5 shadow-sm"
          onSubmit={(event) => void applyFilters(event)}
          aria-label="Trier et filtrer les suggestions"
        >
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
            <FilterSelect
              label="Trier par"
              value={filters.sort}
              onChange={(sort) => {
                setFilters({ ...filters, sort })
              }}
            />
            <FilterNumber
              label="Âge minimum"
              value={filters.age_min}
              min="18"
              max="120"
              onChange={(age_min) => {
                setFilters({ ...filters, age_min })
              }}
            />
            {advanced && (
              <label className="text-sm font-semibold">
                Localisation
                <select
                  className="mt-1 w-full rounded-xl border border-[#d8c6cc] px-3 py-2 font-normal"
                  value={filters.location_id}
                  onChange={(event) => {
                    setFilters({ ...filters, location_id: event.target.value })
                  }}
                >
                  <option value="">Toutes les zones</option>
                  {locations.map((location) => (
                    <option value={location.id} key={location.id}>
                      {location.label}
                    </option>
                  ))}
                </select>
              </label>
            )}
            <FilterNumber
              label="Âge maximum"
              value={filters.age_max}
              min="18"
              max="120"
              onChange={(age_max) => {
                setFilters({ ...filters, age_max })
              }}
            />
            <FilterNumber
              label="Distance maximum (km)"
              value={filters.distance_max_km}
              min="0"
              max="20000"
              onChange={(distance_max_km) => {
                setFilters({ ...filters, distance_max_km })
              }}
            />
            <FilterNumber
              label="Popularité minimum"
              value={filters.popularity_min}
              min="0"
              max="100"
              onChange={(popularity_min) => {
                setFilters({ ...filters, popularity_min })
              }}
            />
            <FilterNumber
              label="Popularité maximum"
              value={filters.popularity_max}
              min="0"
              max="100"
              onChange={(popularity_max) => {
                setFilters({ ...filters, popularity_max })
              }}
            />
          </div>
          {availableTags.length > 0 && (
            <fieldset className="mt-4">
              <legend className="text-sm font-semibold">Tags en commun</legend>
              <div className="mt-2 flex flex-wrap gap-3">
                {availableTags.map((tag) => (
                  <label
                    className="flex items-center gap-2 text-sm"
                    key={tag.id}
                  >
                    <input
                      type="checkbox"
                      checked={filters.tag_ids.includes(tag.id)}
                      onChange={() => {
                        const selected = filters.tag_ids.includes(tag.id)
                          ? filters.tag_ids.filter((id) => id !== tag.id)
                          : [...filters.tag_ids, tag.id]
                        setFilters({ ...filters, tag_ids: selected })
                      }}
                    />
                    {tag.name}
                  </label>
                ))}
              </div>
            </fieldset>
          )}
          <div className="mt-4 flex flex-wrap gap-3">
            <button className="rounded-xl bg-[#d43d37] px-5 py-2.5 font-semibold text-white">
              Appliquer
            </button>
            <button
              className="rounded-xl border border-[#d8c6cc] px-5 py-2.5 font-semibold"
              type="button"
              onClick={() => void resetFilters()}
            >
              Réinitialiser
            </button>
          </div>
        </form>
        {error && (
          <div
            className="mt-8 rounded-2xl bg-[#fff0ef] p-4 text-sm text-[#a52e29]"
            role="alert"
          >
            {error}
          </div>
        )}
        {loading && profiles.length === 0 ? (
          <p className="mt-12 text-center" role="status">
            Recherche des profils compatibles…
          </p>
        ) : profiles.length === 0 ? (
          <section className="mt-12 rounded-3xl border border-[#efdeda] bg-white p-10 text-center">
            <h2 className="text-xl font-bold">
              {advanced
                ? 'Aucun profil ne correspond'
                : 'Aucune suggestion pour le moment'}
            </h2>
            <p className="mt-2 text-sm text-[#755f6d]">
              {advanced
                ? 'Élargissez ou réinitialisez vos critères pour obtenir davantage de résultats.'
                : 'Revenez plus tard : les règles de compatibilité et de blocage restent toujours appliquées.'}
            </p>
          </section>
        ) : (
          <section
            className="mt-8 grid gap-6 sm:grid-cols-2 lg:grid-cols-3"
            aria-label="Profils suggérés"
          >
            {profiles.map((profile) => (
              <ProfileCardView profile={profile} key={profile.id} />
            ))}
          </section>
        )}
        {nextCursor && (
          <div className="mx-auto mt-10 max-w-xs">
            <button
              className="w-full rounded-xl border border-[#d43d37] px-5 py-3 font-semibold text-[#d43d37] disabled:opacity-50"
              disabled={loading}
              onClick={() => void loadMore()}
            >
              {loading ? 'Chargement…' : 'Afficher plus de profils'}
            </button>
          </div>
        )}
      </div>
    </main>
  )
}

type DiscoveryResponse = {
  data: ProfileCard[]
  meta: { next_cursor: string | null; count: number }
}

async function loadInitial(advanced: boolean) {
  const [session, page, locations] = await Promise.all([
    requestJson<{ data: { csrf_token: string } }>('/auth/session'),
    requestJson<DiscoveryResponse>(
      advanced ? '/search/profiles' : '/discovery/suggestions',
    ),
    advanced
      ? requestJson<{ data: LocationSuggestion[] }>('/locations?limit=20')
      : Promise.resolve({ data: [] }),
  ])
  return {
    token: session.data.csrf_token,
    page,
    locationOptions: locations.data,
  }
}

type DiscoveryFilters = {
  sort: string
  age_min: string
  age_max: string
  distance_max_km: string
  popularity_min: string
  popularity_max: string
  tag_ids: string[]
  location_id: string
}

const emptyFilters: DiscoveryFilters = {
  sort: 'recommended',
  age_min: '',
  age_max: '',
  distance_max_km: '',
  popularity_min: '',
  popularity_max: '',
  tag_ids: [],
  location_id: '',
}

function discoveryUrl(
  filters: DiscoveryFilters,
  cursor?: string,
  advanced = false,
) {
  const query = new URLSearchParams()
  Object.entries(filters).forEach(([name, value]) => {
    if (Array.isArray(value)) {
      value.forEach((item) => {
        query.append(name, item)
      })
      return
    }
    if (value && !(name === 'sort' && value === 'recommended')) {
      query.set(name, value)
    }
  })
  if (cursor) query.set('cursor', cursor)
  const suffix = query.toString()
  const endpoint = advanced ? '/search/profiles' : '/discovery/suggestions'
  return `${endpoint}${suffix ? `?${suffix}` : ''}`
}

function FilterNumber({
  label,
  value,
  min,
  max,
  onChange,
}: {
  label: string
  value: string
  min: string
  max: string
  onChange: (value: string) => void
}) {
  return (
    <label className="text-sm font-semibold">
      {label}
      <input
        className="mt-1 w-full rounded-xl border border-[#d8c6cc] px-3 py-2 font-normal"
        type="number"
        min={min}
        max={max}
        value={value}
        onChange={(event) => {
          onChange(event.target.value)
        }}
      />
    </label>
  )
}

function FilterSelect({
  label,
  value,
  onChange,
}: {
  label: string
  value: string
  onChange: (value: string) => void
}) {
  return (
    <label className="text-sm font-semibold">
      {label}
      <select
        className="mt-1 w-full rounded-xl border border-[#d8c6cc] px-3 py-2 font-normal"
        value={value}
        onChange={(event) => {
          onChange(event.target.value)
        }}
      >
        <option value="recommended">Recommandé</option>
        <option value="age">Âge</option>
        <option value="distance">Distance</option>
        <option value="popularity">Popularité</option>
        <option value="tags">Tags communs</option>
      </select>
    </label>
  )
}

function ProfileCardView({ profile }: { profile: ProfileCard }) {
  return (
    <article className="overflow-hidden rounded-3xl border border-[#efdeda] bg-white shadow-lg shadow-[#35102d]/5">
      <div className="relative bg-[#f1e5ea]">
        {profile.main_photo ? (
          <img
            className="aspect-[4/3] w-full object-cover"
            src={profile.main_photo.url}
            alt={`Photo principale de ${profile.first_name}`}
          />
        ) : (
          <div className="grid aspect-[4/3] place-items-center text-sm text-[#755f6d]">
            Aucune photo
          </div>
        )}
        <span className="absolute top-4 right-4 rounded-full bg-white/90 px-3 py-1 text-xs font-semibold">
          {profile.presence.online ? '● En ligne' : 'Hors ligne'}
        </span>
      </div>
      <div className="space-y-4 p-5">
        <div className="flex items-start justify-between gap-3">
          <div>
            <h2 className="text-2xl font-bold text-[#35102d]">
              {profile.first_name}, {profile.age}
            </h2>
            <p className="mt-1 text-sm text-[#755f6d]">
              {profile.location.city}
              {profile.location.distance_km === null
                ? ''
                : ` · ${String(profile.location.distance_km)} km`}
            </p>
          </div>
          <span className="rounded-full bg-[#fff0ef] px-3 py-1 text-xs font-bold text-[#d43d37]">
            {profile.popularity}/100
          </span>
        </div>
        <div className="flex flex-wrap gap-2">
          {profile.tags.slice(0, 4).map((tag) => (
            <span
              className="rounded-full bg-[#f7f0f4] px-3 py-1 text-xs"
              key={tag.id}
            >
              {tag.name}
            </span>
          ))}
        </div>
        <p className="text-xs font-medium text-[#755f6d]">
          {profile.location.same_zone ? 'Même zone · ' : ''}
          {profile.common_tags} centre{profile.common_tags > 1 ? 's' : ''}{' '}
          d’intérêt commun{profile.common_tags > 1 ? 's' : ''}
        </p>
        <button
          className="w-full rounded-xl bg-[#d43d37] px-4 py-2.5 font-semibold text-white"
          onClick={() => {
            navigate(`/profiles/${profile.id}`)
          }}
        >
          Voir le profil
        </button>
      </div>
    </article>
  )
}
