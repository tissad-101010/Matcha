import { useEffect, useState } from 'react'

import { errorMessage, requestJson } from '../auth/api'
import { navigate } from '../navigation'

type ActivityProfile = {
  id: string
  first_name: string
  age: number
  popularity: number
  location: { city: string; district: string | null }
  main_photo: { id: string; url: string } | null
}

type VisitorItem = { visitor: ActivityProfile; visited_at: string }
type LikeItem = { user: ActivityProfile; liked_at: string }

export function ActivityPage() {
  const [tab, setTab] = useState<'visitors' | 'likes'>('visitors')
  const [visitors, setVisitors] = useState<VisitorItem[]>([])
  const [likes, setLikes] = useState<LikeItem[]>([])
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    void Promise.all([
      requestJson<{ data: VisitorItem[] }>('/me/visitors?period=30'),
      requestJson<{ data: LikeItem[] }>('/me/likes-received'),
    ])
      .then(([visitResponse, likeResponse]) => {
        setVisitors(visitResponse.data)
        setLikes(likeResponse.data)
      })
      .catch((reason: unknown) => {
        setError(errorMessage(reason))
      })
      .finally(() => {
        setLoading(false)
      })
  }, [])

  const entries =
    tab === 'visitors'
      ? visitors.map((item) => ({
          profile: item.visitor,
          date: item.visited_at,
        }))
      : likes.map((item) => ({ profile: item.user, date: item.liked_at }))

  return (
    <main className="min-h-screen bg-[#fffaf7] px-4 py-8 text-[#281320]">
      <div className="mx-auto max-w-4xl">
        <header className="mb-8 flex items-center justify-between">
          <h1 className="text-3xl font-bold">Mon activité</h1>
          <button
            className="font-semibold text-[#d43d37]"
            onClick={() => {
              navigate('/discover')
            }}
          >
            Retour à la découverte
          </button>
        </header>
        <div
          className="mb-6 flex gap-2"
          role="tablist"
          aria-label="Historique personnel"
        >
          <Tab
            active={tab === 'visitors'}
            label="Visites reçues"
            onClick={() => {
              setTab('visitors')
            }}
          />
          <Tab
            active={tab === 'likes'}
            label="Likes reçus"
            onClick={() => {
              setTab('likes')
            }}
          />
        </div>
        {loading && <p>Chargement de votre activité…</p>}
        {error && (
          <p className="text-red-700" role="alert">
            {error}
          </p>
        )}
        <div className="grid gap-4 sm:grid-cols-2">
          {entries.map(({ profile, date }, index) => (
            <button
              className="flex items-center gap-4 rounded-2xl bg-white p-4 text-left shadow-sm"
              key={`${profile.id}-${date}-${String(index)}`}
              onClick={() => {
                navigate(`/profiles/${profile.id}`)
              }}
            >
              {profile.main_photo ? (
                <img
                  className="h-16 w-16 rounded-full object-cover"
                  src={profile.main_photo.url}
                  alt=""
                />
              ) : (
                <span
                  className="grid h-16 w-16 place-items-center rounded-full bg-[#ffe8e3] text-2xl"
                  aria-hidden="true"
                >
                  ♥
                </span>
              )}
              <span>
                <strong>
                  {profile.first_name}, {profile.age}
                </strong>
                <span className="block text-sm text-[#705964]">
                  {profile.location.city} · Popularité {profile.popularity}/100
                </span>
                <time className="block text-xs text-[#705964]" dateTime={date}>
                  {new Date(date).toLocaleString('fr-FR')}
                </time>
              </span>
            </button>
          ))}
        </div>
        {!loading && entries.length === 0 && (
          <p>Aucune activité dans cette liste.</p>
        )}
      </div>
    </main>
  )
}

function Tab({
  active,
  label,
  onClick,
}: {
  active: boolean
  label: string
  onClick: () => void
}) {
  return (
    <button
      aria-selected={active}
      className={`rounded-full px-5 py-2 font-semibold ${active ? 'bg-[#35102d] text-white' : 'bg-white'}`}
      onClick={onClick}
      role="tab"
    >
      {label}
    </button>
  )
}
