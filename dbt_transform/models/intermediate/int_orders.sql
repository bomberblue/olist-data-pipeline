 {{ config(materialized='view') }}
 
 WITH orders AS 
(
    SELECT
        *
    FROM {{ ref('stg_orders') }}
),

order_items AS 
(
    SELECT
        order_id,
        COUNT(*) AS order_item_count,
        SUM(price) AS order_gmv,
        SUM(freight_value) AS total_freight_value,
        SUM(item_total_value) AS order_total_value
    FROM {{ ref('int_order_items') }}
    GROUP BY order_id
),

order_payments AS 
(
    SELECT
        *
    FROM {{ ref('int_order_payments') }}
),

order_reviews AS 
(
    SELECT *
    FROM {{ ref('int_order_reviews') }}
),

customer_orders AS 
(
    SELECT *
    FROM {{ ref('int_customer_orders') }}
),

final AS 
(
    SELECT
        orders.order_id,
        orders.customer_id,
        customer_orders.customer_unique_id,
        orders.order_status,
        orders.order_purchase_timestamp,
        orders.order_approved_at,
        orders.order_delivered_carrier_date,
        orders.order_delivered_customer_date,
        orders.order_estimated_delivery_date,
        order_items.order_item_count,
        order_items.order_gmv,
        order_items.total_freight_value,
        order_items.order_total_value,
        order_payments.total_payment_value,
        order_payments.payment_count,
        order_payments.max_payment_installments,
        order_reviews.average_review_score,
        order_reviews.review_count,
        order_reviews.latest_review_date,
        customer_orders.first_order_timestamp,
        customer_orders.customer_order_number,
        CASE
            WHEN customer_orders.customer_order_number = 1
                THEN 'new'
            WHEN customer_orders.customer_order_number > 1
                THEN 'returning'
            ELSE 'unknown'
        END AS customer_type,

        date_diff(
            DATE(orders.order_delivered_customer_date),
            DATE(orders.order_purchase_timestamp),
            day
        ) AS delivery_days,

        date_diff(
            DATE(orders.order_estimated_delivery_date),
            DATE(orders.order_purchase_timestamp),
            DAY
        ) AS estimated_delivery_days,

        CASE
            WHEN orders.order_delivered_customer_date
                 > orders.order_estimated_delivery_date
                THEN true
            WHEN orders.order_delivered_customer_date IS NULL
                THEN null
            ELSE false
        END AS is_late
 FROM orders
    INNER JOIN  order_items
        ON orders.order_id = order_items.order_id
    INNER JOIN order_payments
        ON orders.order_id = order_payments.order_id
    INNER JOIN customer_orders
        ON orders.order_id = customer_orders.order_id
    INNER JOIN  order_reviews
        ON orders.order_id = order_reviews.order_id
)

SELECT *
FROM final