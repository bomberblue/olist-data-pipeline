 {{ config(materialized='view') }}

SELECT
    SAFE_CAST(`date` AS DATE) AS hol_date,
    UPPER(TRIM(name)) AS hol_name,
    UPPER(TRIM(type)) AS hol_type,
    UPPER(TRIM(weekday)) AS hol_day
FROM {{ source('olist', 'raw_holidays_2017') }}
UNION ALL
SELECT
    SAFE_CAST(`date` AS DATE) AS hol_date,
    UPPER(TRIM(name)) AS hol_name,
    UPPER(TRIM(type)) AS hol_type,
    UPPER(TRIM(weekday)) AS hol_day
FROM {{ source('olist', 'raw_holidays_2018') }}
