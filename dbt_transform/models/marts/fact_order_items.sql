with order_items as (

    select *
    from {{ ref('int_order_items') }}

),

orders as (

    select
        order_id,
        order_purchase_timestamp

    from {{ ref('stg_orders') }}

),

products as (

    select
        product_key,
        product_id

    from {{ ref('dim_product') }}

),

sellers as 
(
    select
        seller_key,
        seller_id
    from {{ ref('dim_seller') }}
)

SELECT
    to_hex(md5(concat(cast(order_items.order_id as string),'-',cast(order_items.order_item_id as string)))) as order_item_key,
    to_hex(md5(cast(order_items.order_id as string))) as order_key,
    products.product_key,
    sellers.seller_key,
    cast(
        format_date(
            '%Y%m%d',
            date(orders.order_purchase_timestamp)
        ) as int64
    ) as order_date_key,
    order_items.order_item_id,
    order_items.product_id,
    order_items.seller_id,
    order_items.price,
    order_items.freight_value,
    order_items.shipping_limit_date
FROM order_items INNER JOIN orders ON order_items.order_id = orders.order_id
INNER JOIN products ON order_items.product_id = products.product_id
INNER JOIN sellers ON order_items.seller_id = sellers.seller_id