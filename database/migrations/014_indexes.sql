CREATE INDEX profiles_gender_birth_idx ON profiles (gender, birth_date, user_id);
CREATE INDEX photos_owner_created_idx ON photos (user_id, created_at, id);
CREATE INDEX matches_history_low_idx ON matches (user_low_id, created_at DESC, id DESC);
CREATE INDEX matches_history_high_idx ON matches (user_high_id, created_at DESC, id DESC);
CREATE INDEX conversations_created_idx ON conversations (created_at DESC, id DESC);
CREATE INDEX reports_reporter_idx ON reports (reporter_user_id, created_at DESC, id DESC);

-- Supports geographic pre-filtering before the exact Haversine calculation.
CREATE INDEX user_locations_coordinates_idx
    ON user_locations (reduced_latitude, reduced_longitude, user_id);
