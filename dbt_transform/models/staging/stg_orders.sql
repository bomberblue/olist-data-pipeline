 {{ config(materialized='view') }}
 
SELECT
    order_id,
    customer_id,
    UPPER(TRIM(order_status)) AS order_status,
    CAST(order_purchase_timestamp AS timestamp) AS order_purchase_timestamp,
    CAST(order_approved_at AS timestamp) AS order_approved_at,
    CAST(order_delivered_carrier_date AS timestamp) AS order_delivered_carrier_date,
    CAST(order_delivered_customer_date AS timestamp) AS order_delivered_customer_date,
    CAST(order_estimated_delivery_date AS timestamp) AS order_estimated_delivery_date
FROM{{ source('olist', 'raw_orders') }}
