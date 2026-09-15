# queries.py

"""
Focused Olist analytical queries.

Current analysis period for sales and holiday analyses:
    Jan 2017 through Jun 2018

Analyses:
1. Monthly Sales Trend by Brazilian Customer Region
2. RFM - Top Customers
3. RFM - Segment Summary
4. Holiday Impact
5. Holiday Impact by Quarter
6. Holiday Average Orders / GMV per Day by Quarter
7. Holiday vs Non-Holiday Product Category Mix

Important:
- dim_date.is_holiday is treated as BOOL.
- Query failures are logged and re-raised so analysis.py can fail correctly.
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


# ============================================================
# COMMON QUERY EXECUTION
# ============================================================

def run_query(name, sql):
    """
    Execute BigQuery SQL and return a Pandas DataFrame.

    Any exception is re-raised so the top-level analysis pipeline
    returns a non-zero exit status instead of silently continuing.
    """

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


# ============================================================
# SCHEMA HELPERS
# ============================================================

def _get_table_columns(table_name):
    """Return available column names for a BigQuery mart table."""

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

    return set(
        df["column_name"].tolist()
    )


def _resolve_product_category_column():
    """
    Resolve the product-category field available in dim_product.
    """

    columns = _get_table_columns(
        "dim_product"
    )

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
# 1. MONTHLY SALES TREND BY REGION
# JAN 2017 - JUN 2018
# ============================================================

def monthly_sales_trend():
    """
    Monthly sales trend by Brazilian customer region.

    Region is derived from dim_customer.customer_state.

    order_count includes only orders with a matching order-total value,
    while orders_missing_items is retained as a data-quality measure.

    Analysis period:
        Jan 2017 through Jun 2018.
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
                    'AC', 'AP', 'AM', 'PA', 'RO', 'RR', 'TO'
                )
                    THEN 'North'

                WHEN c.customer_state IN (
                    'AL', 'BA', 'CE', 'MA', 'PB',
                    'PE', 'PI', 'RN', 'SE'
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
                OR (
                    d.year = 2018
                    AND d.month <= 6
                )
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
        "Monthly Sales Trend by Region - Jan 2017 to Jun 2018",
        sql,
    )


# ============================================================
# 2. RFM - TOP CUSTOMERS
# ============================================================

def rfm_analysis(limit=RFM_TOP_CUSTOMERS_LIMIT):
    """Return top customers ranked by RFM monetary value."""

    limit = int(limit)

    if limit <= 0:
        raise ValueError(
            "limit must be greater than 0"
        )

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

        ORDER BY
            r.monetary DESC

        LIMIT {limit}
    """

    return run_query(
        "RFM - Top Customers",
        sql,
    )


# ============================================================
# 3. RFM - SEGMENT SUMMARY
# ============================================================

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

        GROUP BY
            customer_segment

        ORDER BY
            total_revenue DESC
    """

    return run_query(
        "RFM - Segment Summary",
        sql,
    )


# ============================================================
# 4. HOLIDAY IMPACT
# JAN 2017 - JUN 2018
# ============================================================

def holiday_impact():
    """
    Compare Holiday vs Non-Holiday order count, GMV and AOV.

    dim_date.is_holiday is a BOOL column.

    Analysis period:
        Jan 2017 through Jun 2018.
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
            CASE
                WHEN d.is_holiday IS TRUE
                    THEN 'Holiday'
                WHEN d.is_holiday IS FALSE
                    THEN 'Non-Holiday'
            END AS day_type,

            COUNT(
                DISTINCT CASE
                    WHEN ot.total_order_value IS NOT NULL
                    THEN f.order_id
                END
            ) AS order_count,

            ROUND(
                SUM(ot.total_order_value),
                2
            ) AS gmv,

            ROUND(
                AVG(ot.total_order_value),
                2
            ) AS avg_order_value

        FROM `{PROJECT_ID}.{DATASET}.fact_orders` AS f

        LEFT JOIN order_totals AS ot
            ON f.order_key = ot.order_key

        JOIN `{PROJECT_ID}.{DATASET}.dim_date` AS d
            ON f.order_date_key = d.date_key

        WHERE d.is_holiday IS NOT NULL

          AND (
                d.year = 2017
                OR (
                    d.year = 2018
                    AND d.month <= 6
                )
          )

        GROUP BY
            day_type

        ORDER BY
            gmv DESC
    """

    return run_query(
        "Holiday Impact - Jan 2017 to Jun 2018",
        sql,
    )


# ============================================================
# 5. HOLIDAY IMPACT BY QUARTER
# JAN 2017 - JUN 2018
# ============================================================

def holiday_impact_by_quarter():
    """
    Holiday vs Non-Holiday GMV and AOV by quarter.

    Analysis period:
        Jan 2017 through Jun 2018.
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
                WHEN d.is_holiday IS TRUE
                    THEN 'Holiday'
                WHEN d.is_holiday IS FALSE
                    THEN 'Non-Holiday'
            END AS day_type,

            COUNT(
                DISTINCT CASE
                    WHEN ot.total_order_value IS NOT NULL
                    THEN f.order_id
                END
            ) AS order_count,

            ROUND(
                SUM(ot.total_order_value),
                2
            ) AS gmv,

            ROUND(
                AVG(ot.total_order_value),
                2
            ) AS avg_order_value

        FROM `{PROJECT_ID}.{DATASET}.fact_orders` AS f

        LEFT JOIN order_totals AS ot
            ON f.order_key = ot.order_key

        JOIN `{PROJECT_ID}.{DATASET}.dim_date` AS d
            ON f.order_date_key = d.date_key

        WHERE d.is_holiday IS NOT NULL

          AND (
                d.year = 2017
                OR (
                    d.year = 2018
                    AND d.month <= 6
                )
          )

        GROUP BY
            year_quarter,
            day_type

        ORDER BY
            year_quarter,
            day_type
    """

    return run_query(
        "Holiday Impact by Quarter - Jan 2017 to Jun 2018",
        sql,
    )


# ============================================================
# 6. HOLIDAY DAILY NORMALIZED METRICS
# JAN 2017 - JUN 2018
# ============================================================

def holiday_daily_metrics_by_quarter():
    """
    Average orders per calendar day and average GMV per calendar day.

    dim_date is used as the calendar base, so calendar days with zero
    orders remain in the denominator.

    Analysis period:
        Jan 2017 through Jun 2018.
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

                COUNT(
                    DISTINCT CASE
                        WHEN ot.total_order_value IS NOT NULL
                        THEN f.order_id
                    END
                ) AS order_count,

                SUM(
                    ot.total_order_value
                ) AS gmv

            FROM `{PROJECT_ID}.{DATASET}.fact_orders` AS f

            LEFT JOIN order_totals AS ot
                ON f.order_key = ot.order_key

            GROUP BY
                f.order_date_key
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
                    WHEN d.is_holiday IS TRUE
                        THEN 'Holiday'
                    WHEN d.is_holiday IS FALSE
                        THEN 'Non-Holiday'
                END AS day_type

            FROM `{PROJECT_ID}.{DATASET}.dim_date` AS d

            WHERE d.is_holiday IS NOT NULL

              AND (
                    d.year = 2017
                    OR (
                        d.year = 2018
                        AND d.month <= 6
                    )
              )
        )

        SELECT
            c.year_quarter,
            c.day_type,

            COUNT(*) AS day_count,

            SUM(
                COALESCE(
                    o.order_count,
                    0
                )
            ) AS total_orders,

            ROUND(
                SUM(
                    COALESCE(
                        o.gmv,
                        0
                    )
                ),
                2
            ) AS total_gmv,

            ROUND(
                AVG(
                    COALESCE(
                        o.order_count,
                        0
                    )
                ),
                2
            ) AS avg_orders_per_day,

            ROUND(
                AVG(
                    COALESCE(
                        o.gmv,
                        0
                    )
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
        "Holiday Daily Metrics by Quarter - Jan 2017 to Jun 2018",
        sql,
    )


# ============================================================
# 7. HOLIDAY PRODUCT CATEGORY MIX
# JAN 2017 - JUN 2018
# ============================================================

def holiday_product_category_mix(top_n=10):
    """
    Compare Holiday vs Non-Holiday product-category GMV mix.

    Returns top categories by combined GMV and calculates each
    category's percentage share within each day type.

    Analysis period:
        Jan 2017 through Jun 2018.
    """

    top_n = int(top_n)

    if top_n <= 0:
        raise ValueError(
            "top_n must be greater than 0"
        )

    category_column = (
        _resolve_product_category_column()
    )

    sql = f"""
        WITH category_stats AS (
            SELECT
                CASE
                    WHEN d.is_holiday IS TRUE
                        THEN 'Holiday'
                    WHEN d.is_holiday IS FALSE
                        THEN 'Non-Holiday'
                END AS day_type,

                COALESCE(
                    CAST(
                        p.`{category_column}`
                        AS STRING
                    ),
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

            JOIN `{PROJECT_ID}.{DATASET}.fact_orders` AS f
                ON i.order_key = f.order_key

            JOIN `{PROJECT_ID}.{DATASET}.dim_date` AS d
                ON f.order_date_key = d.date_key

            LEFT JOIN `{PROJECT_ID}.{DATASET}.dim_product` AS p
                ON i.product_key = p.product_key

            WHERE d.is_holiday IS NOT NULL

              AND (
                    d.year = 2017
                    OR (
                        d.year = 2018
                        AND d.month <= 6
                    )
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

            GROUP BY
                product_category

            ORDER BY
                combined_gmv DESC

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
        "Holiday Product Category Mix - Jan 2017 to Jun 2018",
        sql,
    )
