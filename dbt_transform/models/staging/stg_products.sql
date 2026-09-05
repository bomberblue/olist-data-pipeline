{{ config(materialized='view') }}

SELECT
    product_id,
    product_category_name,
    CAST(product_name_lenght AS integer) AS product_name_length,
    CAST(product_description_lenght AS integer) AS product_description_length,
    CAST(product_photos_qty AS integer) AS product_photos_count,
    CAST(product_weight_g AS numeric) AS product_weight_g,
    CAST(product_length_cm AS numeric) AS product_length_cm,
    CAST(product_height_cm AS numeric) AS product_height_cm,
    CAST(product_width_cm AS numeric) AS product_width_cm
FROM {{ source('olist', 'raw_products') }}