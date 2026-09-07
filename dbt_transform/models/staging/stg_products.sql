{{ config(materialized='view') }}

SELECT
    product.product_id,
    product.product_category_name,
    SAFE_CAST(product.product_name_lenght AS integer) AS product_name_length,
    SAFE_CAST(product.product_description_lenght AS integer) AS product_description_length,
    SAFE_CAST(product.product_photos_qty AS integer) AS product_photos_qty,
    SAFE_CAST(product.product_weight_g AS numeric) AS product_weight_g,
    SAFE_CAST(product.product_length_cm AS numeric) AS product_length_cm,
    SAFE_CAST(product.product_height_cm AS numeric) AS product_height_cm,
    SAFE_CAST(product.product_width_cm AS numeric) AS product_width_cm
FROM {{ source('olist', 'raw_products') }} product
