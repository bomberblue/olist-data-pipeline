 {{ config(materialized='view') }}

 SELECT
    *,
    MIN(
        CASE WHEN is_qualifying_order THEN order_purchase_timestamp END
    ) OVER (PARTITION BY customer_unique_id) AS first_order_timestamp,
    CASE
        WHEN is_qualifying_order
            THEN ROW_NUMBER() OVER (
                PARTITION BY customer_unique_id, is_qualifying_order
                ORDER BY order_purchase_timestamp, order_id
            )
    END AS customer_order_number
    FROM
    (
        SELECT
        orders.order_id,
        orders.customer_id,
        customers.customer_unique_id,
        orders.order_purchase_timestamp,
        orders.order_status,
        orders.order_status NOT IN ('CANCELED', 'UNAVAILABLE') AS is_qualifying_order,
        customers.customer_zip_code_prefix,
        customers.customer_city,
        customers.customer_state
        FROM {{ ref('stg_orders')}} orders LEFT JOIN {{ ref('stg_customers') }} customers
        ON orders.customer_id = customers.customer_id
    )

