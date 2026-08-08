ALTER TABLE photos DROP CONSTRAINT photos_user_id_position_key;

ALTER TABLE photos
    ADD CONSTRAINT photos_user_position_unique
    UNIQUE (user_id, position)
    DEFERRABLE INITIALLY DEFERRED;
