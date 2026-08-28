import { useEffect, useState } from 'react'
import { io } from 'socket.io-client'

type NotificationEvent = {
  id: string
  type: 'like_received' | 'profile_visited'
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
      {notification.type === 'like_received'
        ? 'Votre profil vient de recevoir un nouveau like.'
        : 'Une personne vient de consulter votre profil.'}
    </div>
  )
}
