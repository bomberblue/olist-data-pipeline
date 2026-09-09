/*
 * This model creates a dimension table for geolocation data.
 * It deduplicates the data based on zip code prefix, latitude, longitude, city, and state.
 * The region is derived based on the state.
 */

WITH geolocation AS 
(
    SELECT *
    FROM {{ ref('stg_geolocation') }}
),

deduplicated AS 
(
    SELECT
        geolocation_zip_code_prefix,
        latitude,
        longitude,
        city,
        state
    FROM geolocation

    QUALIFY ROW_NUMBER() OVER (
        PARTITION BY
            geolocation_zip_code_prefix,
            latitude,
            longitude,
            city,
            state
        ORDER BY geolocation_zip_code_prefix
    ) = 1
)

SELECT
    to_hex(md5(cast(geolocation_zip_code_prefix AS string))) AS geolocation_key,
    geolocation_zip_code_prefix as zip_code_prefix,
    latitude,
    longitude,
    city,
    state,
    CASE
        WHEN state IN ('AC','AP','AM','PA','RO','RR','TO')
            THEN 'North'
        WHEN state IN ('AL','BA','CE','MA','PB','PE','PI','RN','SE')
            THEN 'Northeast'
        WHEN state IN ('DF','GO','MT','MS')
            THEN 'Central-West'
        WHEN state IN ('ES','MG','RJ','SP')
            THEN 'Southeast'
        WHEN state IN ('PR','RS','SC')
            THEN 'South'
        ELSE 'Unknown'
    END AS region
FROM deduplicated