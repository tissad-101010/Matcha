import { useEffect, useState } from 'react'

import { errorMessage, requestJson } from '../auth/api'
import { navigate } from '../navigation'
import type { ProfileCard } from './types'

export function DiscoveryPage() {
  const [profiles, setProfiles] = useState<ProfileCard[]>([])
  const [csrfToken, setCsrfToken] = useState('')
  const [nextCursor, setNextCursor] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    void loadInitial()
      .then(({ token, page }) => {
        setCsrfToken(token)
        setProfiles(page.data)
        setNextCursor(page.meta.next_cursor)
      })
      .catch((reason: unknown) => {
        setError(errorMessage(reason))
      })
      .finally(() => {
        setLoading(false)
      })
  }, [])

  async function loadMore() {
    if (!nextCursor) return
    setLoading(true)
    try {
      const page = await requestJson<DiscoveryResponse>(
        `/discovery/suggestions?cursor=${encodeURIComponent(nextCursor)}`,
      )
      setProfiles((current) => [...current, ...page.data])
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
            <span className="text-[#d43d37]">Découvrir</span>
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
              Suggestions compatibles
            </p>
            <h1 className="mt-2 text-4xl font-bold text-[#35102d]">
              Des profils faits pour se rencontrer
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
              Aucune suggestion pour le moment
            </h2>
            <p className="mt-2 text-sm text-[#755f6d]">
              Revenez plus tard : les règles de compatibilité et de blocage
              restent toujours appliquées.
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

async function loadInitial() {
  const [session, page] = await Promise.all([
    requestJson<{ data: { csrf_token: string } }>('/auth/session'),
    requestJson<DiscoveryResponse>('/discovery/suggestions'),
  ])
  return { token: session.data.csrf_token, page }
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
      </div>
    </article>
  )
}
