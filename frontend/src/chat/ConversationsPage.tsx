import { useEffect, useRef, useState } from 'react'
import type { SyntheticEvent } from 'react'
import { io } from 'socket.io-client'
import type { Socket } from 'socket.io-client'

import { errorMessage, requestJson } from '../auth/api'
import { navigate } from '../navigation'
import type { Conversation, Message } from './types'

export function ConversationsPage() {
  const [conversations, setConversations] = useState<Conversation[]>([])
  const [selected, setSelected] = useState<Conversation | null>(null)
  const [messages, setMessages] = useState<Message[]>([])
  const [body, setBody] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)
  const socketRef = useRef<Socket | null>(null)
  const selectedIdRef = useRef<string | null>(null)

  useEffect(() => {
    void requestJson<{ data: Conversation[] }>('/conversations')
      .then((response) => {
        setConversations(response.data)
        if (response.data[0]) {
          selectedIdRef.current = response.data[0].id
          setSelected(response.data[0])
        }
      })
      .catch((reason: unknown) => {
        setError(errorMessage(reason))
      })
      .finally(() => {
        setLoading(false)
      })
  }, [])

  useEffect(() => {
    if (!selected) return
    void requestJson<{ data: Message[] }>(
      `/conversations/${selected.id}/messages?limit=50`,
    )
      .then((response) => {
        setMessages([...response.data].reverse())
        const latest = response.data[0]
        if (latest) {
          socketRef.current?.emit('conversation:read', {
            conversation_id: selected.id,
            message_id: latest.id,
          })
        }
      })
      .catch((reason: unknown) => {
        setError(errorMessage(reason))
      })
  }, [selected])

  useEffect(() => {
    const socket = io({
      transports: ['websocket', 'polling'],
      withCredentials: true,
    })
    socketRef.current = socket
    const receive = ({ message }: { message: Message }) => {
      if (message.conversation_id === selectedIdRef.current) {
        setMessages((current) => appendUnique(current, message))
        socket.emit('conversation:read', {
          conversation_id: message.conversation_id,
          message_id: message.id,
        })
      }
    }
    socket.on('message:new', receive)
    socket.on('message:ack', receive)
    socket.on(
      'conversation:updated',
      (event: { conversation_id: string; can_send: boolean }) => {
        setConversations((current) =>
          current.map((item) =>
            item.id === event.conversation_id
              ? { ...item, can_send: event.can_send }
              : item,
          ),
        )
        setSelected((current) =>
          current?.id === event.conversation_id
            ? { ...current, can_send: event.can_send }
            : current,
        )
      },
    )
    return () => {
      socket.disconnect()
      socketRef.current = null
    }
  }, [])

  function submit(event: SyntheticEvent<HTMLFormElement>) {
    event.preventDefault()
    const normalized = body.trim()
    if (!selected || !normalized || !socketRef.current) return
    setError('')
    socketRef.current.emit(
      'message:send',
      {
        conversation_id: selected.id,
        client_message_id: crypto.randomUUID(),
        body: normalized,
      },
      (result: { ok?: boolean; error?: { message?: string } }) => {
        if (!result.ok) {
          setError(result.error?.message ?? 'Message non envoyé.')
        }
      },
    )
    setBody('')
  }

  return (
    <main className="min-h-screen bg-[#fffaf7] text-[#281320]">
      <header className="border-b border-[#efdeda] bg-white px-4 py-4">
        <div className="mx-auto flex max-w-6xl items-center justify-between">
          <button
            className="text-2xl font-bold text-[#35102d]"
            onClick={() => {
              navigate('/discover')
            }}
          >
            <span className="text-[#ff5149]">♥</span> matcha
          </button>
          <button
            className="font-semibold text-[#d43d37]"
            onClick={() => {
              navigate('/discover')
            }}
          >
            Découvrir
          </button>
        </div>
      </header>
      <section className="mx-auto grid min-h-[calc(100vh-65px)] max-w-6xl md:grid-cols-[20rem_1fr]">
        <aside
          className="border-r border-[#efdeda] bg-white p-4"
          aria-label="Conversations"
        >
          <h1 className="mb-4 text-xl font-bold">Messages</h1>
          {conversations.map((item) => (
            <button
              className={`mb-2 w-full rounded-xl p-3 text-left ${selected?.id === item.id ? 'bg-[#ffe8e3]' : 'hover:bg-[#fff4f0]'}`}
              key={item.id}
              onClick={() => {
                selectedIdRef.current = item.id
                setSelected(item)
              }}
            >
              <span className="font-semibold">
                {item.other_user.first_name}
              </span>
              <span className="block truncate text-sm text-[#705964]">
                {item.last_message?.body ?? 'Nouvelle connexion'}
              </span>
              {item.unread_count > 0 && (
                <span className="text-xs font-bold text-[#d43d37]">
                  {item.unread_count} non lu(s)
                </span>
              )}
            </button>
          ))}
          {!loading && conversations.length === 0 && (
            <p>Aucune conversation pour le moment.</p>
          )}
        </aside>
        <div className="flex min-h-[32rem] flex-col p-4 sm:p-6">
          {selected ? (
            <>
              <h2 className="border-b border-[#efdeda] pb-3 text-xl font-bold">
                {selected.other_user.first_name} {selected.other_user.last_name}
              </h2>
              <div
                className="flex flex-1 flex-col justify-end gap-3 overflow-y-auto py-5"
                aria-live="polite"
              >
                {messages.map((message) => (
                  <article
                    className="max-w-[80%] rounded-2xl bg-white px-4 py-3 shadow-sm"
                    key={message.id}
                  >
                    <p className="whitespace-pre-wrap break-words">
                      {message.body}
                    </p>
                    <time
                      className="text-xs text-[#705964]"
                      dateTime={message.created_at}
                    >
                      {new Date(message.created_at).toLocaleString('fr-FR')}
                    </time>
                  </article>
                ))}
              </div>
              {selected.can_send ? (
                <form className="flex gap-2" onSubmit={submit}>
                  <label className="sr-only" htmlFor="message-body">
                    Message
                  </label>
                  <textarea
                    id="message-body"
                    className="min-h-12 flex-1 resize-none rounded-xl border border-[#d8c6cc] px-4 py-3"
                    maxLength={2000}
                    required
                    value={body}
                    onChange={(event) => {
                      setBody(event.target.value)
                    }}
                  />
                  <button
                    className="rounded-xl bg-[#ff5149] px-5 font-bold text-white"
                    type="submit"
                  >
                    Envoyer
                  </button>
                </form>
              ) : (
                <p className="rounded-xl bg-[#f1e7e9] p-3">
                  Cette connexion est terminée. L’historique reste consultable.
                </p>
              )}
              {error && (
                <p
                  className="mt-2 text-sm font-semibold text-red-700"
                  role="alert"
                >
                  {error}
                </p>
              )}
            </>
          ) : (
            <p className="m-auto">Sélectionnez une conversation.</p>
          )}
        </div>
      </section>
    </main>
  )
}

function appendUnique(messages: Message[], message: Message) {
  return messages.some((item) => item.id === message.id)
    ? messages
    : [...messages, message]
}
