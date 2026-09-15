 {{ config(materialized='view') }}
 
SELECT
    order_id,
    customer_id,
    UPPER(TRIM(order_status)) AS order_status,
    SAFE_CAST(order_purchase_timestamp AS timestamp) AS order_purchase_timestamp,
    SAFE_CAST(order_approved_at AS timestamp) AS order_approved_at,
    SAFE_CAST(order_delivered_carrier_date AS timestamp) AS order_delivered_carrier_date,
    SAFE_CAST(order_delivered_customer_date AS timestamp) AS order_delivered_customer_date,
    SAFE_CAST(order_estimated_delivery_date AS timestamp) AS order_estimated_delivery_date
FROM{{ source('olist', 'raw_orders') }}

