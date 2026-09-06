{{ config(
    schema='olist_mart',
    materialized='table'
) }}

SELECT
    CAST(format_date('%Y%m%d', full_date) AS int64) AS date_key,
    full_date,
    format_date('%A', full_date) AS day_of_week,
    extract(dayofweek from full_date) AS day_of_week_num,
    extract(week from full_date) AS week,
    extract(month from full_date) AS month,
    format_date('%B', full_date) AS month_name,
    extract(quarter from full_date) AS quarter,
    extract(year from full_date) AS year,
    extract(dayofweek from full_date) in (1, 7) AS is_weekend,
    last_day(full_date, month) = full_date AS is_month_end,
    full_date = last_day(full_date, quarter) AS is_quarter_end,
    full_date = last_day(full_date, year) AS is_year_end
FROM 
(
    SELECT
    full_date
    FROM unnest(
        generate_date_array(
            DATE('2016-01-01'),
            DATE('2018-12-31'),
            interval 1 DAY
        )
    ) AS full_date
)