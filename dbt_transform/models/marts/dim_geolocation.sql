/*
 * This model creates a dimension table for geolocation data.
 */

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
FROM {{ ref('int_geolocation') }}