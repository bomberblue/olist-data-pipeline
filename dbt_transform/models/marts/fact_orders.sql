/*
 * This model creates a fact table for orders.
 * It joins the orders data with customers to include relevant keys and attributes.
 * The fact table includes a unique order key, customer key, order date key, and other relevant attributes.
 * One row per order (order_id)
 * Number of items = Total number of items ordered in the order id
 * Gross Merchandise Value = Sum of prices for all items in the order before any discounts or promotions
 * Total Freight Value = Sum of freight values for all items in the order
 * Order Total Value = Sum of total values for all items in the order
 * Total Payment Value = Sum of payment values for all items in the order
 * Delivery Days = Number of days between order purchase and delivery
 * Estimated Delivery Days = Number of days estimated for delivery
 * Is Late = Flag indicating if the order was delivered late
 * Average Review Score = Average rating given by the customer for the order
 * Review Count = Number of reviews submitted for the order
 * Latest Review Date = Date of the most recent review for the order
 * Customer Type = Type of customer (e.g., new, returning)
 * First Order Timestamp = Timestamp of the customer's first order
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
    orders.order_estimated_delivery_date,
    orders.order_item_count AS number_of_items,
    orders.order_gmv AS Gross_Merchandise_Value,
    orders.total_freight_value,
    orders.order_total_value,
    orders.total_payment_value,
    orders.delivery_days,
    orders.estimated_delivery_days,
    orders.is_late,
    orders.average_review_score,
    orders.review_count,
    orders.latest_review_date,
    orders.customer_type,
    orders.first_order_timestamp
FROM orders
LEFT JOIN customers ON orders.customer_unique_id = customers.customer_unique_id
