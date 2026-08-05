CREATE TABLE likes (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    source_user_id uuid NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    target_user_id uuid NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    is_active boolean NOT NULL DEFAULT true,
    activated_at timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deactivated_at timestamptz,
    created_at timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (source_user_id, target_user_id),
    CHECK (source_user_id <> target_user_id),
    CHECK ((is_active AND deactivated_at IS NULL) OR (NOT is_active AND deactivated_at IS NOT NULL)),
    CHECK (activated_at >= created_at)
);

CREATE INDEX likes_received_active_idx
    ON likes (target_user_id, activated_at DESC, source_user_id) WHERE is_active;

CREATE TABLE matches (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_low_id uuid NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    user_high_id uuid NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    status text NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'ended_unlike', 'ended_block')),
    created_at timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ended_at timestamptz,
    ended_by_user_id uuid REFERENCES accounts(id) ON DELETE CASCADE,
    CHECK (user_low_id < user_high_id),
    CHECK (
        (status = 'active' AND ended_at IS NULL AND ended_by_user_id IS NULL)
        OR (status <> 'active' AND ended_at IS NOT NULL AND ended_by_user_id IS NOT NULL)
    ),
    CHECK (ended_by_user_id IS NULL OR ended_by_user_id IN (user_low_id, user_high_id))
);

CREATE UNIQUE INDEX matches_one_active_pair_idx
    ON matches (user_low_id, user_high_id) WHERE status = 'active';
CREATE INDEX matches_low_active_idx ON matches (user_low_id, created_at DESC, id DESC)
    WHERE status = 'active';
CREATE INDEX matches_high_active_idx ON matches (user_high_id, created_at DESC, id DESC)
    WHERE status = 'active';
