CREATE VIEW current_consents AS
SELECT DISTINCT ON (user_id, purpose)
    user_id,
    purpose,
    policy_version,
    granted,
    occurred_at
FROM consent_events
ORDER BY user_id, purpose, occurred_at DESC, id DESC;

CREATE VIEW profile_completeness AS
SELECT
    profiles.user_id,
    (
        profiles.birth_date <= CURRENT_DATE - INTERVAL '18 years'
        AND profiles.gender IS NOT NULL
        AND profiles.bio IS NOT NULL
        AND EXISTS (SELECT 1 FROM profile_tags WHERE profile_tags.user_id = profiles.user_id)
        AND EXISTS (SELECT 1 FROM user_locations WHERE user_locations.user_id = profiles.user_id)
        AND EXISTS (
            SELECT 1 FROM current_consents
            WHERE current_consents.user_id = profiles.user_id
              AND current_consents.purpose = 'matching_preferences'
              AND current_consents.granted
        )
    ) AS is_complete
FROM profiles;

CREATE VIEW active_matches AS
SELECT id, user_low_id, user_high_id, created_at
FROM matches
WHERE status = 'active';

CREATE VIEW public_profiles AS
SELECT
    profiles.user_id,
    accounts.username,
    profiles.first_name,
    profiles.gender,
    profiles.bio,
    date_part('year', age(CURRENT_DATE, profiles.birth_date))::integer AS age,
    location_catalog.country_code,
    location_catalog.city_name,
    location_catalog.district_name,
    profile_stats.popularity_score,
    profile_stats.last_seen_at
FROM profiles
JOIN accounts ON accounts.id = profiles.user_id
JOIN profile_completeness ON profile_completeness.user_id = profiles.user_id
JOIN user_locations ON user_locations.user_id = profiles.user_id
JOIN location_catalog ON location_catalog.id = user_locations.catalog_location_id
JOIN profile_stats ON profile_stats.user_id = profiles.user_id
WHERE accounts.status = 'active'
  AND profile_completeness.is_complete;

CREATE OR REPLACE FUNCTION recompute_popularity(p_user_id uuid)
RETURNS smallint
LANGUAGE plpgsql
AS $$
DECLARE
    likes_count integer;
    matches_count integer;
    visitors_count integer;
    calculated_score smallint;
BEGIN
    SELECT count(DISTINCT source_user_id)::integer INTO likes_count
    FROM likes
    WHERE target_user_id = p_user_id AND is_active;

    SELECT count(*)::integer INTO matches_count
    FROM matches
    WHERE status = 'active'
      AND p_user_id IN (user_low_id, user_high_id);

    SELECT count(DISTINCT visitor_user_id)::integer INTO visitors_count
    FROM visits
    WHERE visited_user_id = p_user_id
      AND visited_at >= CURRENT_TIMESTAMP - INTERVAL '30 days';

    calculated_score := LEAST(100, GREATEST(0, round(
        50.0 * likes_count / (likes_count + 10.0)
        + 30.0 * matches_count / (matches_count + 5.0)
        + 20.0 * visitors_count / (visitors_count + 25.0)
    )))::smallint;

    INSERT INTO profile_stats (
        user_id, active_likes_count, active_matches_count,
        unique_visitors_30d_count, popularity_score, computed_at
    ) VALUES (
        p_user_id, likes_count, matches_count,
        visitors_count, calculated_score, CURRENT_TIMESTAMP
    )
    ON CONFLICT (user_id) DO UPDATE SET
        active_likes_count = EXCLUDED.active_likes_count,
        active_matches_count = EXCLUDED.active_matches_count,
        unique_visitors_30d_count = EXCLUDED.unique_visitors_30d_count,
        popularity_score = EXCLUDED.popularity_score,
        computed_at = EXCLUDED.computed_at;

    RETURN calculated_score;
END;
$$;
