/*
 * This model creates a dimension table for date data.
 * It generates a range of dates from 2016-01-01 to 2018-12-31 and extracts various date attributes.
 */
  
{{ config(
    schema='olist_mart',
    materialized='table'
) }}

WITH dates AS 
(
    SELECT
        date_day
    FROM UNNEST(
        GENERATE_DATE_ARRAY(
            '2016-01-01',
            '2018-12-31',
             interval 1 DAY
        )
    ) AS date_day
),

holidays AS 
(
    SELECT
        hol_date,
        hol_name,
        hol_type,
        hol_day
    FROM {{ ref('stg_holiday_calendar') }}
)
SELECT
    CAST(
        FORMAT_DATE('%Y%m%d', dates.date_day)
        AS INT64
    ) AS date_key,
    dates.date_day AS date,
    EXTRACT(DAY FROM dates.date_day) AS day,
    format_date('%A', dates.date_day) AS day_of_week,
    EXTRACT(WEEK FROM dates.date_day) AS week,
    EXTRACT(MONTH FROM dates.date_day) AS month,
    FORMAT_DATE('%B', dates.date_day) AS month_name,
    EXTRACT(QUARTER FROM dates.date_day) AS quarter,
    EXTRACT(YEAR FROM dates.date_day) AS year,
    EXTRACT(DAYOFWEEK FROM dates.date_day) IN (1, 7) AS is_weekend,
    CASE
        WHEN LAST_DAY(dates.date_day, MONTH) = dates.date_day
        THEN TRUE
        ELSE FALSE
    END AS is_month_end,

    CASE
        WHEN LAST_DAY(dates.date_day, QUARTER) = dates.date_day
        THEN TRUE
        ELSE FALSE
    END AS is_quarter_end,

    CASE
        WHEN LAST_DAY(dates.date_day, YEAR) = dates.date_day
        THEN TRUE
        ELSE FALSE
    END AS is_year_end,

    CASE
        WHEN holidays.hol_date IS NOT NULL
        THEN TRUE
        ELSE FALSE
    END AS is_holiday,
    holidays.hol_name AS holiday_name,
    holidays.hol_type AS holiday_type,
    holidays.hol_day AS holiday_weekday
FROM dates LEFT JOIN holidays ON dates.date_day = holidays.hol_date

-- SELECT
--     CAST(format_date('%Y%m%d', full_date) AS int64) AS date_key,
--     full_date,
--     extract(dayofweek from full_date) AS day,
--     format_date('%A', full_date) AS day_of_week,
--     extract(week from full_date) AS week,
--     extract(month from full_date) AS month,
--     format_date('%B', full_date) AS month_name,
--     extract(quarter from full_date) AS quarter,
--     extract(year from full_date) AS year,
--     extract(dayofweek from full_date) in (1, 7) AS is_weekend,
--     last_day(full_date, month) = full_date AS is_month_end,
--     full_date = last_day(full_date, quarter) AS is_quarter_end,
--     full_date = last_day(full_date, year) AS is_year_end
-- FROM 
-- (
--     SELECT
--     full_date
--     FROM unnest(
--         generate_date_array(
--             DATE('2016-01-01'),
--             DATE('2018-12-31'),
--             interval 1 DAY
--         )
--     ) AS full_date
-- )