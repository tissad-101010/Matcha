CREATE TABLE location_catalog (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    country_code char(2) NOT NULL CHECK (country_code = upper(country_code)),
    city_name text NOT NULL CHECK (length(btrim(city_name)) BETWEEN 1 AND 120),
    district_name text CHECK (district_name IS NULL OR length(btrim(district_name)) BETWEEN 1 AND 120),
    normalized_label text NOT NULL UNIQUE CHECK (
        normalized_label = lower(btrim(normalized_label))
        AND length(normalized_label) BETWEEN 1 AND 250
    ),
    centroid_latitude double precision NOT NULL CHECK (centroid_latitude BETWEEN -90 AND 90),
    centroid_longitude double precision NOT NULL CHECK (centroid_longitude BETWEEN -180 AND 180)
);

CREATE INDEX location_catalog_search_idx
    ON location_catalog USING gin (normalized_label gin_trgm_ops);

CREATE TABLE user_locations (
    user_id uuid PRIMARY KEY REFERENCES accounts(id) ON DELETE CASCADE,
    catalog_location_id uuid NOT NULL REFERENCES location_catalog(id) ON DELETE RESTRICT,
    source text NOT NULL CHECK (source IN ('manual', 'gps_reduced')),
    reduced_latitude double precision NOT NULL CHECK (reduced_latitude BETWEEN -90 AND 90),
    reduced_longitude double precision NOT NULL CHECK (reduced_longitude BETWEEN -180 AND 180),
    updated_at timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX user_locations_catalog_idx ON user_locations (catalog_location_id, user_id);
