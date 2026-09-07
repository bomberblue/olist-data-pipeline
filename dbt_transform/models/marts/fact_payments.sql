WITH payments AS 
(
    SELECT *
    FROM {{ ref('stg_order_payments') }}

),

orders AS 
(
    SELECT
        order_id,
        customer_unique_id,
        order_purchase_timestamp
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
    to_hex(md5(concat(cast(payments.order_id as string),'-', cast(payments.payment_sequential as string)))) as payment_key,
    to_hex(md5(cast(payments.order_id as string))) as order_key,
    customers.customer_key,
    safe_cast(format_date('%Y%m%d', date(orders.order_purchase_timestamp)) as int64) as payment_date_key,
    payments.payment_sequential,
    payments.payment_type,
    payments.payment_installments,
    payments.payment_value
FROM payments LEFT JOIN orders ON payments.order_id = orders.order_id
LEFT JOIN customers ON orders.customer_unique_id = customers.customer_unique_id