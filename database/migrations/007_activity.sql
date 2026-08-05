CREATE TABLE profile_stats (
    user_id uuid PRIMARY KEY REFERENCES accounts(id) ON DELETE CASCADE,
    active_likes_count integer NOT NULL DEFAULT 0 CHECK (active_likes_count >= 0),
    active_matches_count integer NOT NULL DEFAULT 0 CHECK (active_matches_count >= 0),
    unique_visitors_30d_count integer NOT NULL DEFAULT 0 CHECK (unique_visitors_30d_count >= 0),
    popularity_score smallint NOT NULL DEFAULT 0 CHECK (popularity_score BETWEEN 0 AND 100),
    last_seen_at timestamptz,
    computed_at timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX profile_stats_popularity_idx
    ON profile_stats (popularity_score DESC, user_id);

CREATE TABLE visits (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    visitor_user_id uuid NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    visited_user_id uuid NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    visited_at timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP,
    notification_sent boolean NOT NULL DEFAULT false,
    CHECK (visitor_user_id <> visited_user_id)
);

CREATE INDEX visits_visited_cursor_idx ON visits (visited_user_id, visited_at DESC, id DESC);
CREATE INDEX visits_visitor_recent_idx ON visits (visitor_user_id, visited_at DESC);
