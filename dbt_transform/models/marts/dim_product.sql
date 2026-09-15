/*
 * This model creates a dimension table for product data.
 * It joins the product data with category translation data to include English category names.
 */
 
SELECT
    to_hex(md5(cast(product.product_id AS string))) AS product_key,
    product.product_id,
    product.product_category_name,
    category_translation.product_category_name_english AS product_category_name_english,
    product.product_name_length,
    product.product_description_length,
    product.product_photos_qty,
    product.product_weight_g,
    product.product_height_cm,
    product.product_length_cm,
    product.product_width_cm
FROM {{ ref('stg_products') }} product LEFT JOIN {{ ref('stg_category_translation') }} AS category_translation
    ON product.product_category_name = category_translation.product_category_name