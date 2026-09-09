/*
 * This model creates a fact table for order items.
 * It joins the order items data with orders, products, and sellers to include relevant keys and attributes.
 * The fact table includes a unique order item key, order key, product key, seller key, order date key, and other relevant attributes.
 * One row per order item (order_id + order_item_id)
 */
 
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
FROM order_items LEFT JOIN orders ON order_items.order_id = orders.order_id
LEFT JOIN products ON order_items.product_id = products.product_id
LEFT JOIN sellers ON order_items.seller_id = sellers.seller_id