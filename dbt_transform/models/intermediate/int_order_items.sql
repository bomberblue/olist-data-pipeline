 {{ config(materialized='view') }}
 SELECT
    order_id,
    order_item_id,
    product_id,
    seller_id,
    shipping_limit_date,
    price,
    freight_value,
    price + freight_value as item_total_value
FROM {{ ref('stg_order_items') }}