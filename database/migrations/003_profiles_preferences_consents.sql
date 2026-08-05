CREATE TABLE profiles (
    user_id uuid PRIMARY KEY REFERENCES accounts(id) ON DELETE CASCADE,
    first_name text NOT NULL CHECK (length(btrim(first_name)) BETWEEN 1 AND 80),
    last_name text NOT NULL CHECK (length(btrim(last_name)) BETWEEN 1 AND 80),
    birth_date date NOT NULL CHECK (birth_date <= CURRENT_DATE),
    gender text CHECK (gender IN ('man', 'woman', 'non_binary')),
    bio text CHECK (bio IS NULL OR length(btrim(bio)) BETWEEN 1 AND 1000),
    created_at timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TRIGGER profiles_set_updated_at
BEFORE UPDATE ON profiles
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TABLE user_preferences (
    user_id uuid NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    desired_gender text NOT NULL CHECK (desired_gender IN ('man', 'woman', 'non_binary')),
    created_at timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, desired_gender)
);

CREATE TABLE consent_events (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id uuid NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    purpose text NOT NULL CHECK (purpose IN ('matching_preferences', 'gps_location')),
    policy_version text NOT NULL CHECK (length(btrim(policy_version)) BETWEEN 1 AND 40),
    granted boolean NOT NULL,
    occurred_at timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX consent_events_current_idx
    ON consent_events (user_id, purpose, occurred_at DESC, id DESC);
