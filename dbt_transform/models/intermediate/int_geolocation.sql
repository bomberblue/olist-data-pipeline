/*
 * It deduplicates the data based on zip code prefix, latitude, longitude, city, and state.
 * The region is derived based on the state.
 */

{{ config(materialized='view') }}

SELECT
    geolocation_zip_code_prefix,
    latitude,
    longitude,
    city,
    state
FROM {{ ref('stg_geolocation') }}
QUALIFY ROW_NUMBER() OVER (
    PARTITION BY
        geolocation_zip_code_prefix,
        latitude,
        longitude,
        city,
        state
    ORDER BY geolocation_zip_code_prefix
) = 1

