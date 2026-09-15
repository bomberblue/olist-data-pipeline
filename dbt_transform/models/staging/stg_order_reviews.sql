{{ config(materialized='view') }}
 
SELECT
    review_id,
    order_id,
    CAST(review_score AS integer) AS review_score,
    TRIM(review_comment_title) AS review_comment_title,
    TRIM(review_comment_message) AS review_comment_message,
    CAST(review_creation_date AS timestamp) AS review_creation_date,
    cast(review_answer_timestamp AS timestamp) AS review_answer_timestamp
FROM {{ source('olist', 'raw_order_reviews_dataset') }}
