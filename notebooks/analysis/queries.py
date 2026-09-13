# queries.py

"""
Focused Olist analytical queries.

Analyses:
1. Monthly Sales Trend
2. RFM - Top Customers
3. RFM - Segment Summary
4. Holiday Impact
5. Holiday Impact by Quarter
6. Holiday Average Orders / GMV per Day by Quarter
7. Holiday vs Non-Holiday Product Category Mix
"""

import logging
import time

import pandas as pd
from sqlalchemy import text

from config import (
    PROJECT_ID,
    DATASET,
    RFM_TOP_CUSTOMERS_LIMIT,
)
from engine import engine


logger = logging.getLogger(__name__)


HOLIDAY_START_DATE = "2017-01-01"
HOLIDAY_END_DATE_EXCLUSIVE = "2018-07-01"


def run_query(name, sql):
    """Execute BigQuery SQL and return a Pandas DataFrame."""

    start = time.time()

    try:
        df = pd.read_sql(
            text(sql),
            con=engine,
        )

        elapsed = time.time() - start

        logger.info(
            "%s completed: %s rows in %.2f seconds",
            name,
            f"{len(df):,}",
            elapsed,
        )

        return df

    except Exception:
        logger.exception(
            "Query failed: %s",
            name,
        )
        raise


def _get_table_columns(table_name):
    """Return the available column names for a BigQuery mart table."""

    sql = f"""
        SELECT column_name
        FROM `{PROJECT_ID}.{DATASET}.INFORMATION_SCHEMA.COLUMNS`
        WHERE table_name = '{table_name}'
        ORDER BY ordinal_position
    """

    df = pd.read_sql(
        text(sql),
        con=engine,
    )

    return set(df["column_name"].tolist())


def _resolve_product_category_column():
    """
    Resolve the product-category column in dim_product.

    This avoids hard-coding one category column name when different
    dbt models may use slightly different naming conventions.
    """

    columns = _get_table_columns("dim_product")

    candidates = (
        "product_category_name_english",
        "product_category_name",
        "category_name",
        "product_category",
        "category",
    )

    for column in candidates:
        if column in columns:
            return column

    raise ValueError(
        "No supported product category column was found in dim_product. "
        f"Available columns: {sorted(columns)}"
    )


# ============================================================
# MONTHLY SALES TREND - FULL AVAILABLE DATA
# ============================================================

def monthly_sales_trend():
    """
    Monthly sales trend by Brazilian customer region.

    Region is derived from dim_customer.customer_state.
    Analysis period: Jan 2017 through Jun 2018.
    """

    sql = f"""
        WITH order_totals AS (
            SELECT
                order_key,
                SUM(price + freight_value) AS total_order_value
            FROM `{PROJECT_ID}.{DATASET}.fact_order_items`
            GROUP BY order_key
        )

        SELECT
            FORMAT(
                '%04d-%02d',
                d.year,
                d.month
            ) AS year_month,

            CASE
                WHEN c.customer_state IN (
                    'AC', 'AP', 'AM', 'PA',
                    'RO', 'RR', 'TO'
                )
                    THEN 'North'

                WHEN c.customer_state IN (
                    'AL', 'BA', 'CE', 'MA',
                    'PB', 'PE', 'PI', 'RN', 'SE'
                )
                    THEN 'Northeast'

                WHEN c.customer_state IN (
                    'DF', 'GO', 'MT', 'MS'
                )
                    THEN 'Central-West'

                WHEN c.customer_state IN (
                    'ES', 'MG', 'RJ', 'SP'
                )
                    THEN 'Southeast'

                WHEN c.customer_state IN (
                    'PR', 'RS', 'SC'
                )
                    THEN 'South'

                ELSE 'Unknown'
            END AS region,
            
            COUNT(
                DISTINCT CASE
                WHEN ot.total_order_value IS NOT NULL
                THEN f.order_id
                END
            ) AS order_count,

            COUNT(
                 DISTINCT CASE
                 WHEN ot.total_order_value IS NULL
                 THEN f.order_id
                 END
            ) AS orders_missing_items,

            ROUND(
                 SUM(ot.total_order_value),
                 2
             ) AS gmv,

            ROUND(
                AVG(ot.total_order_value),
                2
            ) AS avg_order_value

        FROM `{PROJECT_ID}.{DATASET}.fact_orders` AS f

        JOIN `{PROJECT_ID}.{DATASET}.dim_date` AS d
            ON f.order_date_key = d.date_key

        LEFT JOIN `{PROJECT_ID}.{DATASET}.dim_customer` AS c
            ON f.customer_key = c.customer_key

        LEFT JOIN order_totals AS ot
            ON f.order_key = ot.order_key

        WHERE d.year IS NOT NULL
          AND d.month IS NOT NULL
          AND (
                d.year = 2017
                OR
                (d.year = 2018 AND d.month <= 6)
          )

        GROUP BY
            d.year,
            d.month,
            region

        ORDER BY
            d.year,
            d.month,
            region
    """

    return run_query(
        "Monthly Sales Trend by Region",
        sql,
    )

# ============================================================
# RFM ANALYSES - FULL AVAILABLE DATA
# ============================================================

def rfm_analysis(limit=RFM_TOP_CUSTOMERS_LIMIT):
    """Top customers by RFM monetary value."""

    limit = int(limit)

    if limit <= 0:
        raise ValueError("limit must be greater than 0")

    sql = f"""
        SELECT
            r.customer_key,
            c.customer_unique_id,
            r.customer_segment,

            r.recency AS recency_days,
            r.frequency,
            r.monetary AS monetary_value,

            r.recency_score,
            r.frequency_score,
            r.monetary_score,

            r.rfm_code,
            r.rfm_total_score AS rfm_score,

            c.customer_state,
            c.customer_city

        FROM `{PROJECT_ID}.{DATASET}.fct_customer_rfm` AS r

        LEFT JOIN `{PROJECT_ID}.{DATASET}.dim_customer` AS c
            ON r.customer_key = c.customer_key

        ORDER BY r.monetary DESC

        LIMIT {limit}
    """

    return run_query(
        "RFM - Top Customers",
        sql,
    )


def rfm_segment_summary():
    """Summary statistics by RFM customer segment."""

    sql = f"""
        SELECT
            customer_segment,

            COUNT(*) AS customer_count,

            ROUND(
                AVG(recency),
                1
            ) AS avg_recency_days,

            ROUND(
                AVG(frequency),
                2
            ) AS avg_frequency,

            ROUND(
                AVG(monetary),
                2
            ) AS avg_monetary_value,

            ROUND(
                SUM(monetary),
                2
            ) AS total_revenue,

            ROUND(
                SAFE_DIVIDE(
                    100.0 * COUNT(*),
                    SUM(COUNT(*)) OVER ()
                ),
                2
            ) AS pct_customers,

            ROUND(
                SAFE_DIVIDE(
                    100.0 * SUM(monetary),
                    SUM(SUM(monetary)) OVER ()
                ),
                2
            ) AS pct_revenue

        FROM `{PROJECT_ID}.{DATASET}.fct_customer_rfm`

        WHERE customer_segment IS NOT NULL

        GROUP BY customer_segment

        ORDER BY total_revenue DESC
    """

    return run_query(
        "RFM - Segment Summary",
        sql,
    )


# ============================================================
# HOLIDAY IMPACT - Jan 2017 TO Jun 2018
# ============================================================

def holiday_impact():
    """Holiday vs non-holiday impact from Jan 2017 through Jun 2018."""

    sql = f"""
        WITH order_totals AS (
            SELECT
                order_key,
                SUM(price + freight_value) AS total_order_value
            FROM `{PROJECT_ID}.{DATASET}.fact_order_items`
            GROUP BY order_key
        )

        SELECT
            CASE
                WHEN UPPER(TRIM(d.is_holiday)) = 'TRUE'
                    THEN 'Holiday'
                WHEN UPPER(TRIM(d.is_holiday)) = 'FALSE'
                    THEN 'Non-Holiday'
            END AS day_type,

            COUNT(DISTINCT f.order_id) AS order_count,

            ROUND(
                SUM(ot.total_order_value),
                2
            ) AS gmv,

            ROUND(
                SAFE_DIVIDE(
                    SUM(ot.total_order_value),
                    COUNT(DISTINCT f.order_id)
                ),
                2
            ) AS avg_order_value

        FROM `{PROJECT_ID}.{DATASET}.fact_orders` AS f

        LEFT JOIN order_totals AS ot
            ON f.order_key = ot.order_key

        JOIN `{PROJECT_ID}.{DATASET}.dim_date` AS d
            ON f.order_date_key = d.date_key

        WHERE UPPER(TRIM(d.is_holiday))
              IN ('TRUE', 'FALSE')

          AND (
                (d.year = 2017 AND d.month >= 1)
                OR
                (d.year = 2018 AND d.month <= 6)
          )

        GROUP BY day_type

        ORDER BY gmv DESC
    """

    return run_query(
        "Holiday Impact - Jan 2017 to Jun 2018",
        sql,
    )


def holiday_impact_by_quarter():
    """Holiday vs non-holiday GMV and AOV by quarter."""

    sql = f"""
        WITH order_totals AS (
            SELECT
                order_key,
                SUM(price + freight_value) AS total_order_value
            FROM `{PROJECT_ID}.{DATASET}.fact_order_items`
            GROUP BY order_key
        )

        SELECT
            CONCAT(
                CAST(d.year AS STRING),
                '-Q',
                CAST(
                    CASE
                        WHEN d.month IN (1, 2, 3) THEN 1
                        WHEN d.month IN (4, 5, 6) THEN 2
                        WHEN d.month IN (7, 8, 9) THEN 3
                        ELSE 4
                    END AS STRING
                )
            ) AS year_quarter,

            CASE
                WHEN UPPER(TRIM(d.is_holiday)) = 'TRUE'
                    THEN 'Holiday'
                WHEN UPPER(TRIM(d.is_holiday)) = 'FALSE'
                    THEN 'Non-Holiday'
            END AS day_type,

            COUNT(DISTINCT f.order_id) AS order_count,

            ROUND(
                SUM(ot.total_order_value),
                2
            ) AS gmv,

            ROUND(
                SAFE_DIVIDE(
                    SUM(ot.total_order_value),
                    COUNT(DISTINCT f.order_id)
                ),
                2
            ) AS avg_order_value

        FROM `{PROJECT_ID}.{DATASET}.fact_orders` AS f

        LEFT JOIN order_totals AS ot
            ON f.order_key = ot.order_key

        JOIN `{PROJECT_ID}.{DATASET}.dim_date` AS d
            ON f.order_date_key = d.date_key

        WHERE UPPER(TRIM(d.is_holiday))
              IN ('TRUE', 'FALSE')

          AND (
                (d.year = 2017 AND d.month >= 1)
                OR
                (d.year = 2018 AND d.month <= 6)
          )

        GROUP BY
            year_quarter,
            day_type

        ORDER BY
            year_quarter,
            day_type
    """

    return run_query(
        "Holiday Impact by Quarter",
        sql,
    )


# ============================================================
# HOLIDAY DAILY NORMALIZED METRICS
# ============================================================

def holiday_daily_metrics_by_quarter():
    """
    Average orders per calendar day and average GMV per calendar day.

    Calendar dates from dim_date are used as the base so days with zero
    orders are still included in the denominator.
    """

    sql = f"""
        WITH order_totals AS (
            SELECT
                order_key,
                SUM(price + freight_value) AS total_order_value
            FROM `{PROJECT_ID}.{DATASET}.fact_order_items`
            GROUP BY order_key
        ),

        orders_by_day AS (
            SELECT
                f.order_date_key,
                COUNT(DISTINCT f.order_id) AS order_count,
                SUM(ot.total_order_value) AS gmv
            FROM `{PROJECT_ID}.{DATASET}.fact_orders` AS f
            LEFT JOIN order_totals AS ot
                ON f.order_key = ot.order_key
            GROUP BY f.order_date_key
        ),

        calendar_days AS (
            SELECT
                d.date_key,
                d.year,
                d.month,

                CONCAT(
                    CAST(d.year AS STRING),
                    '-Q',
                    CAST(
                        CASE
                            WHEN d.month IN (1, 2, 3) THEN 1
                            WHEN d.month IN (4, 5, 6) THEN 2
                            WHEN d.month IN (7, 8, 9) THEN 3
                            ELSE 4
                        END AS STRING
                    )
                ) AS year_quarter,

                CASE
                    WHEN UPPER(TRIM(d.is_holiday)) = 'TRUE'
                        THEN 'Holiday'
                    WHEN UPPER(TRIM(d.is_holiday)) = 'FALSE'
                        THEN 'Non-Holiday'
                END AS day_type

            FROM `{PROJECT_ID}.{DATASET}.dim_date` AS d

            WHERE UPPER(TRIM(d.is_holiday))
                  IN ('TRUE', 'FALSE')

              AND (
                    (d.year = 2017 AND d.month >= 1)
                     OR
                    (d.year = 2018 AND d.month <= 6)
              )
        )

        SELECT
            c.year_quarter,
            c.day_type,

            COUNT(*) AS day_count,

            SUM(
                COALESCE(o.order_count, 0)
            ) AS total_orders,

            ROUND(
                SUM(
                    COALESCE(o.gmv, 0)
                ),
                2
            ) AS total_gmv,

            ROUND(
                AVG(
                    COALESCE(o.order_count, 0)
                ),
                2
            ) AS avg_orders_per_day,

            ROUND(
                AVG(
                    COALESCE(o.gmv, 0)
                ),
                2
            ) AS avg_gmv_per_day

        FROM calendar_days AS c

        LEFT JOIN orders_by_day AS o
            ON c.date_key = o.order_date_key

        GROUP BY
            c.year_quarter,
            c.day_type

        ORDER BY
            c.year_quarter,
            c.day_type
    """

    return run_query(
        "Holiday Daily Metrics by Quarter",
        sql,
    )


# ============================================================
# HOLIDAY PRODUCT CATEGORY MIX
# ============================================================

def holiday_product_category_mix(top_n=10):
    """
    Compare the product-category GMV mix for Holiday vs Non-Holiday.

    Returns the top categories by combined GMV and calculates each
    category's percentage share within Holiday and Non-Holiday sales.
    """

    top_n = int(top_n)

    if top_n <= 0:
        raise ValueError("top_n must be greater than 0")

    category_column = _resolve_product_category_column()

    sql = f"""
        WITH category_stats AS (
            SELECT
                CASE
                    WHEN UPPER(TRIM(d.is_holiday)) = 'TRUE'
                        THEN 'Holiday'
                    WHEN UPPER(TRIM(d.is_holiday)) = 'FALSE'
                        THEN 'Non-Holiday'
                END AS day_type,

                COALESCE(
                    CAST(p.`{category_column}` AS STRING),
                    'Unknown'
                ) AS product_category,

                COUNT(*) AS units_sold,
                COUNT(DISTINCT i.order_key) AS order_count,

                SUM(
                    i.price + i.freight_value
                ) AS gmv

            FROM `{PROJECT_ID}.{DATASET}.fact_order_items` AS i

            JOIN `{PROJECT_ID}.{DATASET}.fact_orders` AS f
                ON i.order_key = f.order_key

            JOIN `{PROJECT_ID}.{DATASET}.dim_date` AS d
                ON f.order_date_key = d.date_key

            LEFT JOIN `{PROJECT_ID}.{DATASET}.dim_product` AS p
                ON i.product_key = p.product_key

            WHERE UPPER(TRIM(d.is_holiday))
                  IN ('TRUE', 'FALSE')

              AND (
                    (d.year = 2017 AND d.month >= 1)
                    OR
                    (d.year = 2018 AND d.month <= 6)
              )

            GROUP BY
                day_type,
                product_category
        ),

        scored AS (
            SELECT
                day_type,
                product_category,
                units_sold,
                order_count,
                gmv,

                100.0 * SAFE_DIVIDE(
                    gmv,
                    SUM(gmv) OVER (
                        PARTITION BY day_type
                    )
                ) AS gmv_share_pct

            FROM category_stats
        ),

        top_categories AS (
            SELECT
                product_category,
                SUM(gmv) AS combined_gmv
            FROM category_stats
            GROUP BY product_category
            ORDER BY combined_gmv DESC
            LIMIT {top_n}
        )

        SELECT
            s.day_type,
            s.product_category,
            s.units_sold,
            s.order_count,

            ROUND(
                s.gmv,
                2
            ) AS gmv,

            ROUND(
                s.gmv_share_pct,
                2
            ) AS gmv_share_pct

        FROM scored AS s

        JOIN top_categories AS t
            ON s.product_category = t.product_category

        ORDER BY
            t.combined_gmv DESC,
            s.day_type
    """

    return run_query(
        "Holiday Product Category Mix",
        sql,
    )


# HOLIDAY VS NON-HOLIDAY PRODUCT CATEGORY MIX

def holiday_product_category_mix(top_n=10):
    """
    Compare product-category sales mix between Holiday and Non-Holiday days.

    Period:
        January 2017 through June 2018.

    The comparison uses GMV share (%) rather than only absolute GMV,
    because there are many more non-holiday days than holiday days.
    """

    top_n = int(top_n)

    if top_n <= 0:
        raise ValueError("top_n must be greater than 0")

    sql = f"""
        WITH category_sales AS (
            SELECT
                CASE
                    WHEN UPPER(TRIM(d.is_holiday)) = 'TRUE'
                        THEN 'Holiday'
                    WHEN UPPER(TRIM(d.is_holiday)) = 'FALSE'
                        THEN 'Non-Holiday'
                END AS day_type,

                COALESCE(
                    p.product_category_name_english,
                    'Unknown'
                ) AS product_category,

                COUNT(*) AS units_sold,

                COUNT(
                    DISTINCT i.order_key
                ) AS order_count,

                SUM(
                    i.price + i.freight_value
                ) AS gmv

            FROM `{PROJECT_ID}.{DATASET}.fact_order_items` AS i

            JOIN `{PROJECT_ID}.{DATASET}.dim_product` AS p
                ON i.product_key = p.product_key

            JOIN `{PROJECT_ID}.{DATASET}.dim_date` AS d
                ON i.order_date_key = d.date_key

            WHERE UPPER(TRIM(d.is_holiday))
                  IN ('TRUE', 'FALSE')

              AND (
                    (d.year = 2017 AND d.month >= 1)
                    OR
                    (d.year = 2018 AND d.month <= 6)
              )

            GROUP BY
                day_type,
                product_category
        ),

        category_share AS (
            SELECT
                day_type,
                product_category,
                units_sold,
                order_count,
                gmv,

                100.0 * SAFE_DIVIDE(
                    gmv,
                    SUM(gmv) OVER (
                        PARTITION BY day_type
                    )
                ) AS gmv_share_pct

            FROM category_sales
        ),

        top_categories AS (
            SELECT
                product_category,
                SUM(gmv) AS combined_gmv

            FROM category_sales

            WHERE product_category != 'Unknown'

            GROUP BY product_category

            ORDER BY combined_gmv DESC

            LIMIT {top_n}
        )

        SELECT
            s.day_type,
            s.product_category,
            s.units_sold,
            s.order_count,

            ROUND(
                s.gmv,
                2
            ) AS gmv,

            ROUND(
                s.gmv_share_pct,
                2
            ) AS gmv_share_pct

        FROM category_share AS s

        JOIN top_categories AS t
            ON s.product_category = t.product_category

        ORDER BY
            t.combined_gmv DESC,
            s.day_type
    """

    return run_query(
        "Holiday Product Category Mix",
        sql,
    )