CREATE TABLE blocks (
    blocker_user_id uuid NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    blocked_user_id uuid NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    created_at timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (blocker_user_id, blocked_user_id),
    CHECK (blocker_user_id <> blocked_user_id)
);

CREATE INDEX blocks_reverse_idx ON blocks (blocked_user_id, blocker_user_id);

CREATE TABLE reports (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    reporter_user_id uuid NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    reported_user_id uuid NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    reason text NOT NULL CHECK (
        reason IN ('fake_profile', 'inappropriate_content', 'harassment', 'spam', 'underage', 'other')
    ),
    description text CHECK (description IS NULL OR length(btrim(description)) BETWEEN 1 AND 1000),
    created_at timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (reporter_user_id <> reported_user_id)
);

CREATE INDEX reports_reported_idx ON reports (reported_user_id, created_at DESC, id DESC);
