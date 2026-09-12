 {{ config(materialized='view') }}
 
SELECT
    order_id,
    CAST(order_item_id AS integer) AS order_item_id,
    product_id,
    seller_id,
    CAST(shipping_limit_date AS timestamp) AS shipping_limit_date,
    CAST(price AS numeric) AS price,
    CAST(freight_value AS numeric) AS freight_value
FROM {{ source('olist', 'raw_order_items') }}

