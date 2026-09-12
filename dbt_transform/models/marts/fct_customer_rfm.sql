/*
 * The RFM analysis is a marketing technique used to quantitatively rank and group customers based on their purchasing behavior.
 * It helps businesses identify their most valuable customers and tailor marketing strategies accordingly.
 * The RFM model is based on three key metrics:
 * - Recency: How recently a customer has made a purchase.
 * - Frequency: How often a customer makes a purchase.
 * - Monetary: How much money a customer spends on purchases.

 * This model creates a fact table for customer RFM (Recency, Frequency, Monetary) analysis.
 * It calculates the last order date, frequency of orders, and monetary value for each customer.
 * It also assigns RFM scores and segments customers based on their RFM values.
 * One row per unique customer ID
 */

/*
 * Join the order fact table to get Recency and Frequency
 */
WITH orders AS 
(
    SELECT        
        order_key,
        customer_key,
        order_id,
        order_status,
        order_purchase_timestamp
    FROM {{ ref('fact_orders') }}
),

/*
 * Join the order items fact table to get the price and freight value for each order.
 * This allows for the calculation of the monetary value for each customer.
 * Only include relevant columns from the order items fact table.
 */
order_items AS 
(
    SELECT        
        order_key,
        price,
        freight_value
    FROM {{ ref('fact_order_items') }}
),

/*
 * Calculate the last order date and frequency of orders for each customer.
 * Exclude canceled and unavailable orders from the calculations.
 * Group by customer_key to get one row per customer.
 * Use MAX to get the latest order date and COUNT(DISTINCT) to get the frequency of unique orders.
 */
customer_orders AS 
(
    SELECT
        customer_key,
        max(date(order_purchase_timestamp)) AS last_order_date,
        count(distinct order_id) AS frequency
    FROM orders
    WHERE upper(order_status) NOT IN(
        'CANCELED',
        'UNAVAILABLE'
    )
    GROUP BY customer_key
),

/*
 * Calculate the monetary value for each customer.
 * Exclude canceled and unavailable orders from the calculations.
 * Group by customer_key to get one row per customer.
 * Use SUM to get the total monetary value spent by the customer.
 */
 customer_monetary AS 
 (
    SELECT
        orders.customer_key,
        -- GMV = product price only
        sum(order_items.price) as monetary_value
    FROM orders INNER JOIN order_items ON orders.order_key = order_items.order_key
    WHERE UPPER(orders.order_status) NOT IN (
        'CANCELED',
        'UNAVAILABLE'
    )
    GROUP BY orders.customer_key
),

/*
 * Combine the customer orders and monetary value data.
 * Join with the customer dimension to get the customer_unique_id.
 * Use COALESCE to handle cases where a customer may not have any monetary value (e.g., no completed orders).
 * This ensures that all customers are included in the final RFM analysis, even if they have no monetary value.
 */
base AS 
(
    SELECT
        customer_orders.customer_key,
        customers.customer_unique_id,
        customer_orders.last_order_date,
        customer_orders.frequency,
        coalesce(customer_monetary.monetary_value, 0) AS monetary_value
    FROM customer_orders
    LEFT JOIN customer_monetary ON customer_orders.customer_key = customer_monetary.customer_key
    LEFT JOIN {{ ref('dim_customer') }} AS customers ON customer_orders.customer_key = customers.customer_key
),

/*
 * Calculate the recency in days for each customer.
 * Recency is defined as the number of days since the customer's last order.
 * Use MAX to get the latest order date and calculate the difference from the current date.
 * This provides a measure of how recently a customer has made a purchase.
 */
recency AS 
(
    SELECT
        *,
        date_diff(
            (SELECT MAX(last_order_date)
             FROM customer_orders),
            last_order_date,
            day
        ) as recency_days
    FROM base
),
/*
 * Assign RFM scores to each customer based on their recency, frequency, and monetary values.
 * Use NTILE to divide the customers into 5 equal groups for each RFM metric.
 * Higher scores indicate better performance (e.g., more recent, more frequent, higher monetary value).
 * This allows for segmentation of customers based on their RFM scores.
 */
scored AS 
(
    SELECT
        *,
        -- Lower recency is better
        ntile(5) over (
            order by recency_days desc
        ) as recency_score,

        -- Higher frequency is better
        ntile(5) over (
            order by frequency asc
        ) as frequency_score,

        -- Higher monetary value is better
        ntile(5) over (
            order by monetary_value asc
        ) as monetary_score

    FROM recency
)

/*
 * Final selection of customer RFM data.
 * Include customer_key, customer_unique_id, last_order_date, recency_days, frequency, monetary_value, and RFM scores.
 * Concatenate the RFM scores to create a combined RFM score for each customer.
 * Assign customer segments based on their RFM scores using CASE statements.
 * This provides a comprehensive view of each customer's behavior and value to the business.
 */

SELECT    customer_key,
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