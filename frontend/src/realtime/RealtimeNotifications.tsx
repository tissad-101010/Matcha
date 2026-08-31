import { useEffect, useState } from 'react'
import { io } from 'socket.io-client'

type NotificationEvent = {
  id: string
  type:
    | 'like_received'
    | 'profile_visited'
    | 'match_created'
    | 'message_received'
    | 'match_ended'
  actor_user_id: string
  created_at: string
}

export function RealtimeNotifications({ enabled }: { enabled: boolean }) {
  const [notification, setNotification] = useState<NotificationEvent | null>(
    null,
  )

  useEffect(() => {
    if (!enabled) return
    const socket = io({
      transports: ['websocket', 'polling'],
      withCredentials: true,
    })
    socket.on('notification.created', (event: NotificationEvent) => {
      setNotification(event)
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

  if (!notification) return null
  return (
    <div
      className="fixed right-4 top-4 z-50 max-w-sm rounded-xl bg-[#35102d] px-5 py-4 text-sm font-semibold text-white shadow-xl"
      role="status"
    >
      {notificationLabel(notification.type)}
    </div>
  )
}

function notificationLabel(type: NotificationEvent['type']) {
  if (type === 'like_received')
    return 'Votre profil vient de recevoir un nouveau like.'
  if (type === 'profile_visited')
    return 'Une personne vient de consulter votre profil.'
  if (type === 'match_created') return 'Vous avez une nouvelle connexion.'
  if (type === 'message_received') return 'Vous avez reçu un nouveau message.'
  return 'Une connexion vient de se terminer.'
}
