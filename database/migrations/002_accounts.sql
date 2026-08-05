CREATE TABLE accounts (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    email text NOT NULL CHECK (email = lower(btrim(email)) AND length(email) BETWEEN 3 AND 254),
    pending_email text CHECK (
        pending_email IS NULL
        OR (pending_email = lower(btrim(pending_email)) AND length(pending_email) BETWEEN 3 AND 254)
    ),
    username text NOT NULL CHECK (username = lower(btrim(username)) AND length(username) BETWEEN 3 AND 30),
    password_hash text NOT NULL CHECK (length(password_hash) BETWEEN 20 AND 512),
    status text NOT NULL DEFAULT 'pending_verification' CHECK (
        status IN ('pending_verification', 'active', 'deletion_pending')
    ),
    email_verified_at timestamptz,
    last_login_at timestamptz,
    inactivity_warning_sent_at timestamptz,
    created_at timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK ((status = 'pending_verification') OR email_verified_at IS NOT NULL)
);

CREATE UNIQUE INDEX accounts_email_unique ON accounts (lower(email));
CREATE UNIQUE INDEX accounts_username_unique ON accounts (lower(username));
CREATE UNIQUE INDEX accounts_pending_email_unique
    ON accounts (lower(pending_email)) WHERE pending_email IS NOT NULL;
CREATE INDEX accounts_inactivity_idx ON accounts (last_login_at, created_at)
    WHERE status = 'active';

CREATE TRIGGER accounts_set_updated_at
BEFORE UPDATE ON accounts
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TABLE account_tokens (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id uuid NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    type text NOT NULL CHECK (type IN ('verify_email', 'reset_password', 'confirm_email')),
    token_hash bytea NOT NULL UNIQUE CHECK (octet_length(token_hash) >= 32),
    payload jsonb NOT NULL DEFAULT '{}'::jsonb CHECK (jsonb_typeof(payload) = 'object'),
    expires_at timestamptz NOT NULL,
    consumed_at timestamptz,
    created_at timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (expires_at > created_at),
    CHECK (consumed_at IS NULL OR consumed_at >= created_at)
);

CREATE INDEX account_tokens_lookup_idx
    ON account_tokens (account_id, type, expires_at) WHERE consumed_at IS NULL;
