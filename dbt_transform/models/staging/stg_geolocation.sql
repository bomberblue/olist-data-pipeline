 {{ config(materialized='view') }}

SELECT
    CAST(geolocation_zip_code_prefix AS string) AS zip_code,
    CAST(geolocation_lat AS numeric) AS latitude,
    CAST(geolocation_lng AS numeric) AS longitude,
    UPPER(TRIM(geolocation_city)) AS city,
    UPPER(TRIM(geolocation_state)) AS state
FROM {{ source('olist', 'raw_geolocation_dataset') }}
