CREATE TABLE deletion_jobs (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id uuid NOT NULL,
    object_keys text[] NOT NULL CHECK (cardinality(object_keys) > 0),
    status text NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'failed')),
    attempt_count integer NOT NULL DEFAULT 0 CHECK (attempt_count >= 0),
    next_attempt_at timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX deletion_jobs_due_idx ON deletion_jobs (next_attempt_at, id)
    WHERE status IN ('pending', 'failed');

CREATE OR REPLACE FUNCTION purge_expired_visits()
RETURNS bigint
LANGUAGE plpgsql
AS $$
DECLARE
    deleted_count bigint;
BEGIN
    DELETE FROM visits WHERE visited_at < CURRENT_TIMESTAMP - INTERVAL '90 days';
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$;
