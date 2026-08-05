CREATE TABLE photos (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id uuid NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    object_key text NOT NULL UNIQUE CHECK (length(object_key) BETWEEN 1 AND 500),
    mime_type text NOT NULL CHECK (mime_type IN ('image/jpeg', 'image/png', 'image/webp')),
    byte_size integer NOT NULL CHECK (byte_size BETWEEN 1 AND 5242880),
    width integer NOT NULL CHECK (width BETWEEN 1 AND 4096),
    height integer NOT NULL CHECK (height BETWEEN 1 AND 4096),
    position smallint NOT NULL CHECK (position BETWEEN 1 AND 5),
    is_main boolean NOT NULL DEFAULT false,
    created_at timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (user_id, position)
);

CREATE UNIQUE INDEX photos_one_main_idx ON photos (user_id) WHERE is_main;

CREATE OR REPLACE FUNCTION enforce_one_main_photo()
RETURNS trigger
LANGUAGE plpgsql
AS $$
DECLARE
    checked_user_id uuid;
BEGIN
    checked_user_id := COALESCE(NEW.user_id, OLD.user_id);
    IF EXISTS (SELECT 1 FROM photos WHERE user_id = checked_user_id)
       AND NOT EXISTS (SELECT 1 FROM photos WHERE user_id = checked_user_id AND is_main) THEN
        RAISE EXCEPTION 'a user with photos must have exactly one main photo';
    END IF;
    RETURN NULL;
END;
$$;

CREATE CONSTRAINT TRIGGER photos_require_main
AFTER INSERT OR UPDATE OR DELETE ON photos
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION enforce_one_main_photo();
