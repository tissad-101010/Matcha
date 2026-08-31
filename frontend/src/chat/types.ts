export type Message = {
  id: string
  conversation_id: string
  author_id: string
  body: string
  created_at: string
}

export type Conversation = {
  id: string
  match_id: string
  other_user: {
    id: string
    username: string
    first_name: string
    last_name: string
    main_photo_id: string | null
  }
  can_send: boolean
  read_only_reason: 'unlike' | null
  last_message: Message | null
  unread_count: number
  updated_at: string
}
