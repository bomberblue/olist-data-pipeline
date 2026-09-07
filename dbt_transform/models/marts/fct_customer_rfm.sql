with orders as (

    select
        order_key,
        customer_key,
        order_id,
        order_status,
        order_purchase_timestamp

    from {{ ref('fact_orders') }}

),

order_items as (

    select
        order_key,
        price,
        freight_value

    from {{ ref('fact_order_items') }}

),

customer_orders as (

    select
        customer_key,

        max(date(order_purchase_timestamp)) as last_order_date,

        count(distinct order_id) as frequency

    from orders

    where order_status not in ('canceled', 'unavailable')

    group by customer_key

),

customer_monetary as (

    select

        orders.customer_key,

        sum(order_items.price + order_items.freight_value)
            as monetary_value

    from orders

    inner join order_items
        on orders.order_key = order_items.order_key

    where orders.order_status not in ('canceled', 'unavailable')

    group by orders.customer_key

),

base as (

    select

        customer_orders.customer_key,

        customers.customer_unique_id,

        customer_orders.last_order_date,

        customer_orders.frequency,

        coalesce(
            customer_monetary.monetary_value,
            0
        ) as monetary_value

    from customer_orders

    left join customer_monetary
        on customer_orders.customer_key =
           customer_monetary.customer_key

    left join {{ ref('dim_customer') }} customers
        on customer_orders.customer_key =
           customers.customer_key

),

recency as (

    select

        *,

        date_diff(
            max(date(order_purchase_timestamp)),
            last_order_date,
            day
        ) as recency_days

    from base

),

scored as (

    select

        *,

        ntile(5) over (
            order by recency_days desc
        ) as recency_score,

        ntile(5) over (
            order by frequency
        ) as frequency_score,

        ntile(5) over (
            order by monetary_value
        ) as monetary_score

    from recency

)

select

    customer_key,

    customer_unique_id,

    last_order_date,

    recency_days,

    frequency,

    monetary_value,

    recency_score,

    frequency_score,

    monetary_score,

    concat(
        cast(recency_score as string),
        cast(frequency_score as string),
        cast(monetary_score as string)
    ) as rfm_score,

    case

        when recency_score >= 4
             and frequency_score >= 4
             and monetary_score >= 4
            then 'Champions'

        when recency_score >= 3
             and frequency_score >= 3
            then 'Loyal Customers'

        when recency_score >= 4
             and frequency_score <= 2
            then 'New Customers'

        when recency_score <= 2
             and frequency_score >= 3
            then 'At Risk'

        when recency_score <= 2
             and frequency_score <= 2
            then 'Lost Customers'

        else 'Potential Loyalists'

    end as customer_segment

from scored