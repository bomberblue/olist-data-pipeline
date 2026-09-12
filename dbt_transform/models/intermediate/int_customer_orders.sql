 {{ config(materialized='view') }}

 SELECT
    *,
    MIN(order_purchase_timestamp)
    OVER (PARTITION BY customer_unique_id) AS first_order_timestamp,
    ROW_NUMBER()
    OVER (PARTITION BY customer_unique_id
        ORDER BY order_purchase_timestamp, order_id) AS customer_order_number
    FROM 
    (
        SELECT
        orders.order_id,
        orders.customer_id,
        customers.customer_unique_id,
        orders.order_purchase_timestamp,
        orders.order_status
        FROM {{ ref('stg_orders')}} orders LEFT JOIN {{ ref('stg_customers') }} customers
        ON orders.customer_id = customers.customer_id
    )

