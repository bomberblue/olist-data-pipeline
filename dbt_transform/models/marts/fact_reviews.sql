WITH reviews AS 
(
    SELECT *
    FROM {{ ref('stg_order_reviews') }}
),

orders AS 
(
    SELECT
        order_id,
        customer_unique_id
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
    to_hex(md5(concat(cast(reviews.review_id as string),'-', cast(reviews.order_id  as string)))) as review_order_key,
    to_hex(md5(cast(reviews.review_id as string))) as review_key,
    to_hex(md5(cast(reviews.order_id as string))) as order_key,
    customers.customer_key,
    cast(format_date('%Y%m%d', date(reviews.review_creation_date)) as int64) as review_date_key,
    reviews.review_id,
    reviews.review_score,
    reviews.review_comment_title,
    reviews.review_comment_message,
    reviews.review_creation_date,
    reviews.review_answer_timestamp
FROM reviews LEFT JOIN orders ON reviews.order_id = orders.order_id
LEFT JOIN customers ON orders.customer_unique_id = customers.customer_unique_id