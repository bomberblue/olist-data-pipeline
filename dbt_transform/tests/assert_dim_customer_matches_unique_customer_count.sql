-- dim_customer grain is one row per customer_unique_id, not one row per stg_customers row.
-- Fails (returns a row) if the two counts diverge.
WITH dim_count AS (
    SELECT COUNT(*) AS row_count
    FROM {{ ref('dim_customer') }}
),

staging_count AS (
    SELECT COUNT(DISTINCT customer_unique_id) AS row_count
    FROM {{ ref('stg_customers') }}
)

SELECT
    dim_count.row_count AS dim_customer_count,
    staging_count.row_count AS distinct_customer_unique_id_count
FROM dim_count, staging_count
WHERE dim_count.row_count != staging_count.row_count
