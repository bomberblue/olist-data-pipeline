/*
 * This model creates a fact table for orders.
 * It joins the orders data with customers to include relevant keys and attributes.
 * The fact table includes a unique order key, customer key, order date key, and other relevant attributes.
 * One row per order (order_id)
 */

WITH orders AS 
(
    SELECT *
    FROM {{ ref('int_orders') }}
),

customers AS 
(
    SELECT
        customer_key,
        customer_unique_id
    FROM {{ ref('dim_customer') }}

)

SELECT
    to_hex(md5(cast(orders.order_id AS string))) AS order_key,
    orders.order_id,
    customers.customer_key,
    cast(format_date('%Y%m%d',date(orders.order_purchase_timestamp)) AS int64) AS order_date_key,
    orders.order_status,
    orders.order_purchase_timestamp,
    orders.order_approved_at,
    orders.order_delivered_carrier_date,
    orders.order_delivered_customer_date,
    orders.order_estimated_delivery_date
FROM orders
LEFT JOIN customers ON orders.customer_unique_id = customers.customer_unique_id
