{{ config(materialized='view') }}
 
SELECT
    order_id,
    CAST(payment_sequential AS integer) AS payment_sequential,
    CAST(payment_type AS string) AS payment_type,
    CAST(payment_installments AS integer) AS payment_installments,
    CAST(payment_value AS numeric) AS payment_value
FROM {{ source('olist', 'raw_order_payments_dataset') }}