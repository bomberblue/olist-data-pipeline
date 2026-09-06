{{ config(materialized='view') }}
 
SELECT
    order_id,
    AVG(review_score) AS average_review_score,
    COUNT(*) AS review_count,
    MAX(review_creation_date) AS latest_review_date
FROM {{ ref('stg_order_reviews') }}
GROUP BY order_id
