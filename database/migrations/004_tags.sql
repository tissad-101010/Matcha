CREATE TABLE tags (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    name text NOT NULL CHECK (length(btrim(name)) BETWEEN 1 AND 50),
    normalized_name text NOT NULL UNIQUE CHECK (
        normalized_name = lower(btrim(normalized_name))
        AND length(normalized_name) BETWEEN 1 AND 50
    ),
    created_by_user_id uuid REFERENCES accounts(id) ON DELETE SET NULL,
    created_at timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX tags_search_idx ON tags USING gin (normalized_name gin_trgm_ops);

CREATE TABLE profile_tags (
    user_id uuid NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    tag_id uuid NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
    created_at timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, tag_id)
);

CREATE INDEX profile_tags_tag_idx ON profile_tags (tag_id, user_id);
