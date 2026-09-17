import pandas as pd
from sqlalchemy import text


def get_order_vs_aov(engine):
    query = """
    WITH order_totals AS (
        SELECT
            order_key,
            SUM(price + freight_value) AS order_value
        FROM `olist-data-pipeline-507001.olist_mart.fact_order_items`
        GROUP BY order_key
    )

    SELECT
        FORMAT('%04d-%02d', d.year, d.month) AS year_month,
        COUNT(DISTINCT f.order_id) AS orders,
        ROUND(SUM(ot.order_value), 2) AS gmv,
        ROUND(
            SAFE_DIVIDE(
                SUM(ot.order_value),
                COUNT(DISTINCT f.order_id)
            ),
            2
        ) AS avg_order_value
    FROM `olist-data-pipeline-507001.olist_mart.fact_orders` AS f

    JOIN `olist-data-pipeline-507001.olist_mart.dim_date` AS d
        ON f.order_date_key = d.date_key

    LEFT JOIN order_totals AS ot
        ON f.order_key = ot.order_key

    WHERE d.year = 2017
      AND d.month IN (10, 11, 12)

    GROUP BY d.year, d.month
    ORDER BY d.year, d.month
    """

    return pd.read_sql(text(query), con=engine)


def get_november_daily_activity(engine):
    query = """
    SELECT
        d.date_key,
        COUNT(DISTINCT i.order_key) AS order_count,
        ROUND(
            SUM(i.price + i.freight_value),
            2
        ) AS gmv
    FROM `olist-data-pipeline-507001.olist_mart.fact_order_items` AS i

    JOIN `olist-data-pipeline-507001.olist_mart.dim_date` AS d
        ON i.order_date_key = d.date_key

    WHERE d.year = 2017
      AND d.month = 11

    GROUP BY d.date_key
    ORDER BY d.date_key
    """

    return pd.read_sql(text(query), con=engine)


def get_category_spike(engine):
    query = """
    WITH category_monthly AS (
        SELECT
            d.month,
            COALESCE(
                p.product_category_name_english,
                'Unknown'
            ) AS product_category,
            COUNT(*) AS units_sold,
            COUNT(DISTINCT i.order_key) AS order_count,
            SUM(i.price + i.freight_value) AS gmv

        FROM `olist-data-pipeline-507001.olist_mart.fact_order_items` AS i

        JOIN `olist-data-pipeline-507001.olist_mart.dim_date` AS d
            ON i.order_date_key = d.date_key

        LEFT JOIN `olist-data-pipeline-507001.olist_mart.dim_product` AS p
            ON i.product_key = p.product_key

        WHERE d.year = 2017
          AND d.month IN (10, 11)

        GROUP BY d.month, product_category
    ),

    comparison AS (
        SELECT
            product_category,

            SUM(
                CASE WHEN month = 10
                THEN gmv ELSE 0 END
            ) AS oct_gmv,

            SUM(
                CASE WHEN month = 11
                THEN gmv ELSE 0 END
            ) AS nov_gmv,

            SUM(
                CASE WHEN month = 10
                THEN order_count ELSE 0 END
            ) AS oct_orders,

            SUM(
                CASE WHEN month = 11
                THEN order_count ELSE 0 END
            ) AS nov_orders

        FROM category_monthly
        GROUP BY product_category
    ),

    uplift AS (
        SELECT
            *,
            nov_gmv - oct_gmv AS gmv_increase,

            SAFE_MULTIPLY(
                SAFE_DIVIDE(
                    nov_gmv - oct_gmv,
                    oct_gmv
                ),
                100
            ) AS growth_pct

        FROM comparison
    )

    SELECT
        product_category,
        ROUND(oct_gmv, 2) AS oct_gmv,
        ROUND(nov_gmv, 2) AS nov_gmv,
        ROUND(gmv_increase, 2) AS gmv_increase,
        ROUND(growth_pct, 2) AS growth_pct,
        oct_orders,
        nov_orders,

        ROUND(
            100 * SAFE_DIVIDE(
                gmv_increase,
                SUM(gmv_increase) OVER ()
            ),
            2
        ) AS contribution_to_spike_pct

    FROM uplift

    WHERE gmv_increase > 0

    ORDER BY gmv_increase DESC
    """

    return pd.read_sql(text(query), con=engine)
