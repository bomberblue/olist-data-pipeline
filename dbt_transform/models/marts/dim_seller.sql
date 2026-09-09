/*
 * This model creates a dimension table for seller data.
 * It generates a unique seller key and geolocation key based on the seller's ID and zip code prefix.
 */
 
 {{ config(
     schema='olist_mart',
     materialized='table'
 ) }}

SELECT
    to_hex(md5(CAST(seller_id AS string))) AS seller_key,
    seller_id,
    seller_zip_code_prefix,
    seller_city,
    seller_state,
    to_hex(md5(CAST(seller_zip_code_prefix AS string))) AS geolocation_key
FROM {{ ref('stg_sellers') }}