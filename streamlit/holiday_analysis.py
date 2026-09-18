import pandas as pd
from sqlalchemy import text


def get_holiday_impact(engine):

    
   
    query = """
        WITH order_totals AS (
            SELECT
                order_key,
                SUM(price + freight_value) AS total_order_value
            FROM `olist-data-pipeline-507001.olist_mart.fact_order_items`
            GROUP BY order_key
        )

        SELECT
            CASE
                WHEN d.is_holiday= TRUE
                    THEN 'Holiday'
                WHEN d.is_holiday= FALSE
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

        FROM `olist-data-pipeline-507001.olist_mart.fact_orders` AS f

        LEFT JOIN order_totals AS ot
            ON f.order_key = ot.order_key

        JOIN `olist-data-pipeline-507001.olist_mart.dim_date` AS d
            ON f.order_date_key = d.date_key

        WHERE d.is_holiday IN (TRUE, FALSE)

        AND (
    (d.year = 2017 AND d.month >= 1)
    OR
    (d.year = 2018 AND d.month <= 6)
)

        GROUP BY day_type

        ORDER BY gmv DESC
    """

    return pd.read_sql(text(query), engine)

def get_holiday_impact_by_quarter(engine):
        query = """
        WITH order_totals AS (
            SELECT
                order_key,
                SUM(price + freight_value) AS total_order_value
            FROM `olist-data-pipeline-507001.olist_mart.fact_order_items`
            GROUP BY order_key
        )

        SELECT
            CONCAT(
                CAST(d.year AS STRING),
                '-Q',
                CAST(
                    CASE
                        WHEN d.month BETWEEN 1 AND 3 THEN 1
                        WHEN d.month BETWEEN 4 AND 6 THEN 2
                        WHEN d.month BETWEEN 7 AND 9 THEN 3
                        WHEN d.month BETWEEN 10 AND 12 THEN 4
                    END AS STRING
                )
            ) AS year_quarter,

            CASE
                WHEN d.is_holiday = TRUE
                    THEN 'Holiday'
                WHEN d.is_holiday = FALSE
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

        FROM `olist-data-pipeline-507001.olist_mart.fact_orders` AS f

        LEFT JOIN order_totals AS ot
            ON f.order_key = ot.order_key

        JOIN `olist-data-pipeline-507001.olist_mart.dim_date` AS d
            ON f.order_date_key = d.date_key

        WHERE d.is_holiday IN (TRUE, FALSE)

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

        return pd.read_sql(text(query), engine)

def get_holiday_daily_metrics_by_quarter(engine):
    query = """
        WITH order_totals AS (
            SELECT
                order_key,
                SUM(price + freight_value) AS total_order_value
            FROM `olist-data-pipeline-507001.olist_mart.fact_order_items`
            GROUP BY order_key
        ),

        orders_by_day AS (
            SELECT
                f.order_date_key,
                COUNT(DISTINCT f.order_id) AS order_count,
                SUM(ot.total_order_value) AS gmv
            FROM `olist-data-pipeline-507001.olist_mart.fact_orders` AS f

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
                            WHEN d.month BETWEEN 1 AND 3 THEN 1
                            WHEN d.month BETWEEN 4 AND 6 THEN 2
                            WHEN d.month BETWEEN 7 AND 9 THEN 3
                            WHEN d.month BETWEEN 10 AND 12 THEN 4
                        END AS STRING
                    )
                ) AS year_quarter,

                CASE
                    WHEN d.is_holiday = TRUE
                        THEN 'Holiday'
                    WHEN d.is_holiday = FALSE
                        THEN 'Non-Holiday'
                END AS day_type

            FROM `olist-data-pipeline-507001.olist_mart.dim_date` AS d

            WHERE d.is_holiday IN (TRUE, FALSE)

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

    return pd.read_sql(text(query), engine)
def get_holiday_product_category_mix(engine, top_n=10):
    query = f"""
        WITH category_sales AS (
            SELECT
                CASE
                    WHEN d.is_holiday = TRUE
                        THEN 'Holiday'
                    WHEN d.is_holiday = FALSE
                        THEN 'Non-Holiday'
                END AS day_type,

                COALESCE(
                    p.product_category_name_english,
                    'Unknown'
                ) AS product_category,

                COUNT(*) AS units_sold,

                COUNT(DISTINCT i.order_key) AS order_count,

                SUM(
                    i.price + i.freight_value
                ) AS gmv

            FROM `olist-data-pipeline-507001.olist_mart.fact_order_items` AS i

            JOIN `olist-data-pipeline-507001.olist_mart.dim_product` AS p
                ON i.product_key = p.product_key

            JOIN `olist-data-pipeline-507001.olist_mart.dim_date` AS d
                ON i.order_date_key = d.date_key

            WHERE d.is_holiday IN (TRUE, FALSE)

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

                100 * SAFE_DIVIDE(
                    gmv,
                    SUM(gmv) OVER (
                        PARTITION BY day_type
                    )
                ) AS gmv_share_pct

            FROM category_sales
        ),

        top_categories AS (
            SELECT
                product_category

            FROM category_sales

            WHERE product_category != 'Unknown'

            GROUP BY product_category

            ORDER BY SUM(gmv) DESC

            LIMIT {top_n}
        )

        SELECT
            cs.day_type,
            cs.product_category,
            cs.units_sold,
            cs.order_count,

            ROUND(
                cs.gmv,
                2
            ) AS gmv,

            ROUND(
                cs.gmv_share_pct,
                2
            ) AS gmv_share_pct

        FROM category_share AS cs

        JOIN top_categories AS tc
            ON cs.product_category = tc.product_category

        ORDER BY
            cs.product_category,
            cs.day_type
    """

    return pd.read_sql(text(query), engine)

if __name__ == "__main__":


    from sqlalchemy import create_engine

    engine = create_engine(
        "bigquery://olist-data-pipeline-507001"
    )

    df = get_holiday_product_category_mix(engine)

    print(df)

#Black friday analysis

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

    GROUP BY
        d.year,
        d.month

    ORDER BY
        d.year,
        d.month
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

    GROUP BY
        d.date_key

    ORDER BY
        d.date_key
    """

    return pd.read_sql(text(query), con=engine)



