{{ config(materialized='view') }}

SELECT
    seller_id,
    CAST(seller_zip_code_prefix AS string) AS seller_zip_code,
    UPPER(TRIM(seller_city)) AS seller_city,
    UPPER(TRIM(seller_state)) AS seller_state
FROM {{ source('olist', 'raw_sellers') }}
