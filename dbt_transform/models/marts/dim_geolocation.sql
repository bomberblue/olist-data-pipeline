WITH geolocation AS 
(
    SELECT *
    FROM {{ ref('stg_geolocation') }}
),

deduplicated AS 
(
    SELECT
        zip_code,
        latitude,
        longitude,
        city,
        state
    FROM geolocation

    QUALIFY ROW_NUMBER() OVER (
        PARTITION BY
            zip_code,
            latitude,
            longitude,
            city,
            state
        ORDER BY zip_code
    ) = 1
)

SELECT
    to_hex(md5(cast(zip_code AS string))) AS geolocation_key,
    zip_code,
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