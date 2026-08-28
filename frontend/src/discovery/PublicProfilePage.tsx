import { useEffect, useState } from 'react'

import { errorMessage, requestJson } from '../auth/api'
import { navigate } from '../navigation'
import type { PublicProfile } from './types'

export function PublicProfilePage({ profileId }: { profileId: string }) {
  const [profile, setProfile] = useState<PublicProfile | null>(null)
  const [csrfToken, setCsrfToken] = useState('')
  const [error, setError] = useState('')
  const [interactionPending, setInteractionPending] = useState(false)

  useEffect(() => {
    void Promise.all([
      requestJson<{ data: PublicProfile }>(`/profiles/${profileId}`),
      requestJson<{ data: { csrf_token: string } }>('/auth/session'),
    ])
      .then(([profileResponse, session]) => {
        setProfile(profileResponse.data)
        setCsrfToken(session.data.csrf_token)
      })
      .catch((reason: unknown) => {
        setError(errorMessage(reason))
      })
  }, [profileId])

  async function logout() {
    await requestJson('/auth/logout', 'POST', undefined, csrfToken)
    navigate('/')
  }

  async function toggleLike() {
    if (!profile) return
    setInteractionPending(true)
    setError('')
    try {
      const response = await requestJson<{
        data: {
          liked: boolean
          matched: boolean
          match_id: string | null
          match_created?: boolean
        }
      }>(
        `/profiles/${profile.id}/like`,
        profile.viewer_state.liked_by_me ? 'DELETE' : 'POST',
        undefined,
        csrfToken,
      )
      setProfile({
        ...profile,
        viewer_state: {
          ...profile.viewer_state,
          liked_by_me: response.data.liked,
          matched: response.data.matched,
          match_id: response.data.match_id,
          can_message: response.data.matched,
        },
      })
    } catch (reason: unknown) {
      setError(errorMessage(reason))
    } finally {
      setInteractionPending(false)
    }
  }

  return (
    <main className="min-h-screen bg-[#fffaf7] text-[#281320]">
      <header className="border-b border-[#efdeda] bg-white px-4 py-4 sm:px-8">
        <nav
          className="mx-auto flex max-w-6xl items-center justify-between"
          aria-label="Navigation principale"
        >
          <button
            className="font-semibold text-[#d43d37]"
            onClick={() => {
              navigate('/discover')
            }}
          >
            ← Retour à la découverte
          </button>
          <button
            className="text-sm font-semibold"
            onClick={() => void logout()}
          >
            Déconnexion
          </button>
        </nav>
      </header>
      {error ? (
        <div
          className="mx-auto mt-10 max-w-3xl rounded-2xl bg-[#fff0ef] p-5 text-[#a52e29]"
          role="alert"
        >
          {error}
        </div>
      ) : !profile ? (
        <p className="mt-16 text-center" role="status">
          Chargement du profil…
        </p>
      ) : (
        <article className="mx-auto grid max-w-6xl gap-8 px-4 py-10 sm:px-8 lg:grid-cols-[1.15fr_0.85fr]">
          <section aria-label={`Photos de ${profile.first_name}`}>
            <div className="grid gap-4 sm:grid-cols-2">
              {profile.photos.map((photo, index) => (
                <img
                  className={`w-full rounded-3xl object-cover ${index === 0 ? 'sm:col-span-2 aspect-[16/10]' : 'aspect-square'}`}
                  src={photo.url}
                  alt={`Photo ${String(index + 1)} de ${profile.first_name}`}
                  key={photo.id}
                />
              ))}
            </div>
          </section>
          <section className="rounded-3xl border border-[#efdeda] bg-white p-7 shadow-lg shadow-[#35102d]/5">
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className="text-sm text-[#755f6d]">@{profile.username}</p>
                <h1 className="mt-1 text-4xl font-bold text-[#35102d]">
                  {profile.first_name} {profile.last_name}, {profile.age}
                </h1>
                <p className="mt-2 text-sm text-[#755f6d]">
                  {profile.location.city}
                  {profile.location.district
                    ? ` — ${profile.location.district}`
                    : ''}
                </p>
              </div>
              <span className="rounded-full bg-[#fff0ef] px-3 py-1 text-sm font-bold text-[#d43d37]">
                {profile.popularity}/100
              </span>
            </div>
            <p className="mt-5 text-sm font-semibold">
              {profile.presence.online
                ? '● En ligne'
                : lastSeenLabel(profile.presence.last_seen_at)}
            </p>
            <p className="mt-6 leading-7 text-[#493440]">{profile.bio}</p>
            <dl className="mt-6 grid gap-4 text-sm sm:grid-cols-2">
              <div>
                <dt className="font-semibold">Genre</dt>
                <dd>{genderLabel(profile.gender)}</dd>
              </div>
              <div>
                <dt className="font-semibold">Recherche</dt>
                <dd>
                  {profile.desired_genders.map(genderLabel).join(', ') ||
                    'Tous les genres'}
                </dd>
              </div>
            </dl>
            <div className="mt-6 flex flex-wrap gap-2">
              {profile.tags.map((tag) => (
                <span
                  className="rounded-full bg-[#f7f0f4] px-3 py-1 text-sm"
                  key={tag.id}
                >
                  {tag.name}
                </span>
              ))}
            </div>
            <div className="mt-7 rounded-2xl bg-[#fffaf7] p-4 text-sm">
              {profile.viewer_state.matched
                ? 'Vous êtes connectés.'
                : profile.viewer_state.likes_me
                  ? `${profile.first_name} vous a déjà liké.`
                  : profile.viewer_state.liked_by_me
                    ? 'Vous avez déjà liké ce profil.'
                    : 'Aucune interaction pour le moment.'}
            </div>
            <button
              className="mt-4 w-full rounded-xl bg-[#d43d37] px-5 py-3 font-bold text-white disabled:cursor-not-allowed disabled:opacity-50"
              disabled={
                interactionPending ||
                (!profile.viewer_state.liked_by_me &&
                  !profile.viewer_state.can_like)
              }
              onClick={() => void toggleLike()}
            >
              {interactionPending
                ? 'Mise à jour…'
                : profile.viewer_state.matched
                  ? 'Se déconnecter'
                  : profile.viewer_state.liked_by_me
                    ? 'Retirer mon like'
                    : 'Liker la photo de profil'}
            </button>
            {!profile.viewer_state.can_like &&
            !profile.viewer_state.liked_by_me ? (
              <p className="mt-2 text-sm text-[#755f6d]">
                Ajoutez une photo principale à votre profil pour pouvoir liker.
              </p>
            ) : null}
          </section>
        </article>
      )}
    </main>
  )
}

function genderLabel(gender: PublicProfile['gender']) {
  return { man: 'Homme', woman: 'Femme', non_binary: 'Non-binaire' }[gender]
}

function lastSeenLabel(value: string | null) {
  if (!value) return 'Hors ligne'
  return `Vu·e le ${new Intl.DateTimeFormat('fr-FR', { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(value))}`
}
