import { useEffect, useState } from 'react'
import { io } from 'socket.io-client'

import { errorMessage, requestJson } from '../auth/api'
import { navigate } from '../navigation'

type NotificationType =
  | 'like_received'
  | 'profile_visited'
  | 'match_created'
  | 'message_received'
  | 'match_ended'

type NotificationEvent = {
  id: string
  type: NotificationType
  actor_user_id: string
  created_at: string
}

type NotificationItem = {
  id: string
  type: NotificationType
  actor: { id: string; username: string; first_name: string }
  conversation_id: string | null
  read_at: string | null
  created_at: string
}

export function RealtimeNotifications({ enabled }: { enabled: boolean }) {
  const [notification, setNotification] = useState<NotificationEvent | null>(
    null,
  )
  const [items, setItems] = useState<NotificationItem[]>([])
  const [unreadCount, setUnreadCount] = useState(0)
  const [csrfToken, setCsrfToken] = useState('')
  const [open, setOpen] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!enabled) return
    const socket = io({
      transports: ['websocket', 'polling'],
      withCredentials: true,
    })
    socket.on('notification.created', (event: NotificationEvent) => {
      setNotification(event)
      setUnreadCount((current) => current + 1)
    })
    socket.on('relationship.updated', (event: unknown) => {
      window.dispatchEvent(
        new CustomEvent('matcha:relationship-updated', { detail: event }),
      )
    })
    return () => {
      socket.disconnect()
    }
  }, [enabled])

  async function loadCenter() {
    try {
      const [session, notifications, count] = await Promise.all([
        requestJson<{ data: { csrf_token: string } }>('/auth/session'),
        requestJson<{ data: NotificationItem[] }>('/notifications'),
        requestJson<{ data: { unread_count: number } }>(
          '/notifications/unread-count',
        ),
      ])
      setCsrfToken(session.data.csrf_token)
      setItems(notifications.data)
      setUnreadCount(count.data.unread_count)
      setOpen(true)
    } catch (reason) {
      setError(errorMessage(reason))
    }
  }

  async function markAllRead() {
    try {
      await requestJson('/notifications/read-all', 'POST', undefined, csrfToken)
      setUnreadCount(0)
      setItems((current) =>
        current.map((item) => ({
          ...item,
          read_at: item.read_at ?? new Date().toISOString(),
        })),
      )
    } catch (reason) {
      setError(errorMessage(reason))
    }
  }

  if (!enabled) return null
  return (
    <div className="fixed right-4 top-4 z-50">
      <button
        aria-expanded={open}
        aria-label={`Notifications, ${String(unreadCount)} non lues`}
        className="rounded-full bg-[#35102d] px-4 py-3 font-bold text-white shadow-xl"
        onClick={() => {
          if (open) setOpen(false)
          else void loadCenter()
        }}
      >
        🔔 {unreadCount > 0 && <span>{unreadCount}</span>}
      </button>
      {notification && !open && (
        <div
          className="mt-2 max-w-sm rounded-xl bg-[#35102d] px-5 py-4 text-sm font-semibold text-white shadow-xl"
          role="status"
        >
          {notificationLabel(notification.type)}
        </div>
      )}
      {open && (
        <section
          className="mt-2 max-h-[70vh] w-[min(24rem,calc(100vw-2rem))] overflow-y-auto rounded-2xl bg-white p-4 shadow-2xl"
          aria-label="Centre de notifications"
        >
          <div className="mb-3 flex items-center justify-between gap-3">
            <h2 className="text-lg font-bold">Notifications</h2>
            <button
              className="text-sm font-semibold text-[#d43d37]"
              disabled={unreadCount === 0}
              onClick={() => void markAllRead()}
            >
              Tout marquer comme lu
            </button>
          </div>
          {items.map((item) => (
            <article
              className={`border-t border-[#efdeda] py-3 text-sm ${item.read_at ? 'opacity-65' : 'font-semibold'}`}
              key={item.id}
            >
              <button
                className="text-left"
                onClick={() => {
                  setOpen(false)
                  navigate(
                    item.type === 'message_received' && item.conversation_id
                      ? '/messages'
                      : `/profiles/${item.actor.id}`,
                  )
                }}
              >
                {notificationLabel(item.type, item.actor.first_name)}
              </button>
              <time
                className="text-xs text-[#705964]"
                dateTime={item.created_at}
              >
                {new Date(item.created_at).toLocaleString('fr-FR')}
              </time>
            </article>
          ))}
          {items.length === 0 && (
            <p className="text-sm">Aucune notification.</p>
          )}
          {error && (
            <p className="mt-2 text-sm text-red-700" role="alert">
              {error}
            </p>
          )}
        </section>
      )}
    </div>
  )
}

function notificationLabel(type: NotificationType, actor?: string) {
  if (!actor) {
    if (type === 'like_received')
      return 'Votre profil vient de recevoir un nouveau like.'
    if (type === 'profile_visited')
      return 'Une personne vient de consulter votre profil.'
    if (type === 'match_created') return 'Vous avez une nouvelle connexion.'
    if (type === 'message_received') return 'Vous avez reçu un nouveau message.'
    return 'Une connexion vient de se terminer.'
  }
  if (type === 'like_received') return `${actor} aime votre profil.`
  if (type === 'profile_visited') return `${actor} a consulté votre profil.`
  if (type === 'match_created') return `Nouvelle connexion avec ${actor}.`
  if (type === 'message_received') return `Nouveau message de ${actor}.`
  return `Votre connexion avec ${actor} est terminée.`
}
