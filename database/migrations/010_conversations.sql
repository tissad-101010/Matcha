CREATE TABLE conversations (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    match_id uuid NOT NULL UNIQUE REFERENCES matches(id) ON DELETE CASCADE,
    can_send boolean NOT NULL DEFAULT true,
    created_at timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP,
    closed_at timestamptz,
    CHECK ((can_send AND closed_at IS NULL) OR (NOT can_send AND closed_at IS NOT NULL))
);

CREATE TABLE conversation_members (
    conversation_id uuid NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    user_id uuid NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    last_read_message_id uuid,
    hidden_at timestamptz,
    PRIMARY KEY (conversation_id, user_id)
);

CREATE INDEX conversation_members_user_idx
    ON conversation_members (user_id, hidden_at, conversation_id);

CREATE TABLE messages (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id uuid NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    author_user_id uuid NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    client_message_id uuid NOT NULL,
    body text NOT NULL CHECK (length(btrim(body)) BETWEEN 1 AND 2000),
    created_at timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (author_user_id, client_message_id),
    UNIQUE (conversation_id, id)
);

CREATE INDEX messages_cursor_idx ON messages (conversation_id, created_at DESC, id DESC);

ALTER TABLE conversation_members
ADD CONSTRAINT conversation_members_read_message_fk
FOREIGN KEY (conversation_id, last_read_message_id)
REFERENCES messages(conversation_id, id);
