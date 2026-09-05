 {{ config(materialized='view') }}
 
SELECT
    TRIM(product_category_name) ASproduct_category_name,
    TRIM(product_category_name_english) ASproduct_category_name_english
FROM {{ source('olist', 'raw_category_translation') }}
