/*
 * This model creates a dimension table for seller data.
 * It generates a unique seller key and geolocation key based on the seller's ID and zip code prefix.
 */
 
 {{ config(
     schema='olist_mart',
     materialized='table'
 ) }}

SELECT
    to_hex(md5(CAST(seller.seller_id AS string))) AS seller_key,
    seller.seller_id,
    seller.seller_zip_code_prefix,
    seller.seller_city,
    seller.seller_state,
    geolocation.geolocation_key
FROM {{ ref('stg_sellers') }} AS seller
LEFT JOIN {{ ref('dim_geolocation') }} AS geolocation
    ON seller.seller_zip_code_prefix = geolocation.zip_code_prefix
 