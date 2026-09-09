
/*
 * This model creates a dimension table for customer data.
 * - staging customer data into a deduplicated customer dimension, 
 * - adds the customer's first purchase date, 
 * - generates a unique customer key and geolocation key based on the customer's ID and zip code prefix for connecting customers to orders and geolocation.
 * - One row per unique customer ID is retained, with the earliest customer ID being selected in case of duplicates.
 */
 
 {{ config(
     schema='olist_mart',
     materialized='table'
 ) }}

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
)

SELECT
    to_hex(md5(cast(customers.customer_unique_id AS string))) AS customer_key,
    customers.customer_id,
    customers.customer_unique_id,
    customers.customer_zip_code_prefix,
    customers.customer_city,
    customers.customer_state,
    date(first_orders.first_order_timestamp) AS customer_first_order_date,
    to_hex(md5(cast(customers.customer_zip_code_prefix AS string))) AS geolocation_key
FROM customers
LEFT JOIN first_orders
    ON customers.customer_unique_id = first_orders.customer_unique_id
QUALIFY ROW_NUMBER() OVER (
    PARTITION BY customers.customer_unique_id
    ORDER BY customers.customer_id
) = 1