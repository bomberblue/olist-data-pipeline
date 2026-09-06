 {{ config(materialized='view') }}
 
 SELECT
        customer_id,
        customer_unique_id,
        CAST(customer_zip_code_prefix AS string) AS customer_zip_code,
        UPPER(TRIM(customer_city)) AS customer_city,
        UPPER(TRIM(customer_state)) AS customer_state
FROM {{ source('olist', 'raw_customers') }}
