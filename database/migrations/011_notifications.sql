CREATE TABLE notifications (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    recipient_user_id uuid NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    actor_user_id uuid NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    type text NOT NULL CHECK (
        type IN ('like_received', 'profile_visited', 'match_created', 'message_received', 'match_ended')
    ),
    match_id uuid REFERENCES matches(id) ON DELETE CASCADE,
    conversation_id uuid REFERENCES conversations(id) ON DELETE CASCADE,
    message_id uuid REFERENCES messages(id) ON DELETE CASCADE,
    visit_id uuid REFERENCES visits(id) ON DELETE CASCADE,
    read_at timestamptz,
    created_at timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (recipient_user_id <> actor_user_id),
    CHECK (read_at IS NULL OR read_at >= created_at),
    CHECK (
        (type = 'like_received' AND match_id IS NULL AND conversation_id IS NULL AND message_id IS NULL AND visit_id IS NULL)
        OR (type = 'profile_visited' AND visit_id IS NOT NULL AND match_id IS NULL AND conversation_id IS NULL AND message_id IS NULL)
        OR (type IN ('match_created', 'match_ended') AND match_id IS NOT NULL AND conversation_id IS NULL AND message_id IS NULL AND visit_id IS NULL)
        OR (type = 'message_received' AND conversation_id IS NOT NULL AND message_id IS NOT NULL AND visit_id IS NULL)
    )
);

CREATE INDEX notifications_unread_cursor_idx
    ON notifications (recipient_user_id, created_at DESC, id DESC) WHERE read_at IS NULL;
CREATE INDEX notifications_all_cursor_idx
    ON notifications (recipient_user_id, created_at DESC, id DESC);
