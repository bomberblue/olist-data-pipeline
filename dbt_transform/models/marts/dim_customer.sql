/*
 * This model creates a dimension table for customer data.
 * - staging customer data into a deduplicated customer dimension, 
 * - adds the customer's first purchase date, 
 * - generates a unique customer key and geolocation key based on the customer's ID and zip code prefix for connecting customers to orders and geolocation.
 * - One row per unique customer ID is retained, with the latest customer ID being selected in case of duplicates.
 */
 WITH customers AS 
(
    SELECT *
    FROM {{ ref('stg_customers') }}
),

customer_orders AS 
(
    SELECT *
    FROM {{ ref('int_customer_orders') }}
),

first_orders AS 
(
    SELECT
        customer_unique_id,
        MIN(order_purchase_timestamp) AS first_order_timestamp
    FROM customer_orders
    GROUP BY customer_unique_id
),

last_orders_geolocation AS 
(
    SELECT
        customer_unique_id,
        customer_id,
        customer_zip_code_prefix,
        customer_city,
        customer_state
    FROM customer_orders
    QUALIFY ROW_NUMBER() OVER (
        PARTITION BY customer_unique_id
        ORDER BY order_purchase_timestamp DESC, order_id DESC
    ) = 1
),

unique_customers AS
(
    SELECT
        customer_unique_id
    FROM customers
    GROUP BY customer_unique_id
)

SELECT
    to_hex(md5(CAST(customers.customer_unique_id AS string))) AS customer_key,
    last_orders_geolocation.customer_id AS customer_id,
    customers.customer_unique_id,

    last_orders_geolocation.customer_zip_code_prefix
        AS customer_zip_code_prefix,

    last_orders_geolocation.customer_city
        AS customer_city,

    last_orders_geolocation.customer_state
        AS customer_state,

    DATE(first_orders.first_order_timestamp)
        AS customer_first_order_date,

    geolocation.geolocation_key

FROM unique_customers AS customers

LEFT JOIN first_orders
    ON customers.customer_unique_id =
       first_orders.customer_unique_id

LEFT JOIN last_orders_geolocation
    ON customers.customer_unique_id =
       last_orders_geolocation.customer_unique_id

LEFT JOIN {{ ref('dim_geolocation') }} AS geolocation
    ON last_orders_geolocation.customer_zip_code_prefix =
       geolocation.zip_code_prefix