SELECT
    to_hex(md5(CAST(seller_id AS string))) AS seller_key,
    seller_id,
    seller_zip_code,
    seller_city,
    seller_state,
    to_hex(md5(CAST(seller_zip_code AS string))) AS geolocation_key
FROM {{ ref('stg_sellers') }}