import pandas as pd
import plotly.express as px


def get_category_sales_2017(engine):

    query = """
    SELECT
      EXTRACT(MONTH FROM o.order_purchase_timestamp) AS month,
      p.product_category_name_english,
      SUM(oi.price + oi.freight_value) AS total_sales_value
    FROM `olist-data-pipeline-507001.olist_mart.fact_order_items` oi
    JOIN `olist-data-pipeline-507001.olist_mart.fact_orders` o
      ON oi.order_key = o.order_key
    JOIN `olist-data-pipeline-507001.olist_mart.dim_product` p
      ON oi.product_id = p.product_id
    WHERE o.order_status = 'DELIVERED'
      AND EXTRACT(YEAR FROM o.order_purchase_timestamp) = 2017
    GROUP BY
      month,
      p.product_category_name_english
    ORDER BY
      month,
      total_sales_value DESC
    """

    return pd.read_sql(query, engine)


def get_category_sales_2018(engine):
    
    query = """
    SELECT
      EXTRACT(MONTH FROM o.order_purchase_timestamp) AS month,
      p.product_category_name_english,
      SUM(oi.price + oi.freight_value) AS total_sales_value
    FROM `olist-data-pipeline-507001.olist_mart.fact_order_items` oi
    JOIN `olist-data-pipeline-507001.olist_mart.fact_orders` o
      ON oi.order_key = o.order_key
    JOIN `olist-data-pipeline-507001.olist_mart.dim_product` p
      ON oi.product_id = p.product_id
    WHERE o.order_status = 'DELIVERED'
      AND EXTRACT(YEAR FROM o.order_purchase_timestamp) = 2018
    GROUP BY
      month,
      p.product_category_name_english
    ORDER BY
      month,
      total_sales_value DESC
    """

    return pd.read_sql(query, engine)

def get_monthly_region_sales(engine):
    query = """
    SELECT
      FORMAT_DATE(
        "%Y-%m",
        DATE(o.order_purchase_timestamp)
      ) AS month,
      c.customer_state,
      SUM(oi.price + oi.freight_value) AS gmv
    FROM `olist-data-pipeline-507001.olist_mart.fact_order_items` oi
    JOIN `olist-data-pipeline-507001.olist_mart.fact_orders` o
      ON oi.order_key = o.order_key
    JOIN `olist-data-pipeline-507001.olist_mart.dim_customer` c
      ON o.customer_key = c.customer_key
    WHERE o.order_status = 'DELIVERED'
      AND EXTRACT(YEAR FROM o.order_purchase_timestamp) IN (2017, 2018)
    GROUP BY
      month,
      c.customer_state
    ORDER BY
      month,
      gmv DESC
    """

    return pd.read_sql(query, engine)

def add_brazil_region(df):
    region_map = {
        "AC": "North",
        "AP": "North",
        "AM": "North",
        "PA": "North",
        "RO": "North",
        "RR": "North",
        "TO": "North",
        "AL": "Northeast",
        "BA": "Northeast",
        "CE": "Northeast",
        "MA": "Northeast",
        "PB": "Northeast",
        "PE": "Northeast",
        "PI": "Northeast",
        "RN": "Northeast",
        "SE": "Northeast",
        "DF": "Central-West",
        "GO": "Central-West",
        "MT": "Central-West",
        "MS": "Central-West",
        "ES": "Southeast",
        "MG": "Southeast",
        "RJ": "Southeast",
        "SP": "Southeast",
        "PR": "South",
        "RS": "South",
        "SC": "South",
    }

    df["region"] = df["customer_state"].map(region_map)

    return (
        df.groupby(["month", "region"], as_index=False)["gmv"]
        .sum()
    )


def add_half_year(df):

    df["half_year"] = (
        df["month"]
        .apply(lambda x: "H1 (Jan-Jun)" if x <= 6 else "H2 (Jul-Dec)")
    )

    return df


def get_half_year_revenue(df):

    return (
        df
        .groupby(
            ["half_year", "product_category_name_english"],
            as_index=False
        )
        .agg(
            total_revenue=("total_sales_value", "sum")
        )
    )


def get_top_10_each_month(df):

    return (
        df
        .sort_values(
            ["month", "total_sales_value"],
            ascending=[True, False]
        )
        .groupby("month")
        .head(10)
    )


def get_category_frequency(df):

    return (
        df
        .groupby(
            ["half_year", "product_category_name_english"]
        )
        .size()
        .reset_index(name="top_10_months")
    )


def get_category_summary(revenue_df, frequency_df):

    summary = (
        revenue_df
        .merge(
            frequency_df,
            on=["half_year", "product_category_name_english"],
            how="left"
        )
    )

    summary["top_10_months"] = (
        summary["top_10_months"]
        .fillna(0)
        .astype(int)
    )

    return summary

def plot_2017_category_consistency(category_summary, half_year):
    import plotly.express as px

    df = category_summary[category_summary["half_year"] == half_year]

    fig = px.scatter(
        df,
        x="top_10_months",
        y="total_revenue",
        hover_name="product_category_name_english",
        title=f"2017 Category Consistency — {half_year}",
        labels={
            "top_10_months": "Number of Months in Top 10",
            "total_revenue": "Total Revenue",
        },
    )

    return fig

def plot_2017_category_consistency_combined(category_summary):
    import plotly.express as px

    fig = px.scatter(
        category_summary,
        x="top_10_months",
        y="total_revenue",
        color="half_year",
        hover_name="product_category_name_english",
        title="2017 Category Consistency — H1 vs H2",
        labels={
            "top_10_months": "Number of Months in Top 10",
            "total_revenue": "Total Revenue",
            "half_year": "Period",
        },
    )

    return fig


def get_2018_category_revenue(df):

    return (
        df
        .groupby(
            "product_category_name_english",
            as_index=False
        )
        .agg(
            total_revenue=("total_sales_value", "sum")
        )
    )


def get_top_10_each_month_2018(df):

    return (
        df
        .sort_values(
            ["month", "total_sales_value"],
            ascending=[True, False]
        )
        .groupby("month")
        .head(10)
    )


def get_category_frequency_2018(df):

    return (
        df
        .groupby("product_category_name_english")
        .size()
        .reset_index(name="top_10_months")
        .sort_values("top_10_months", ascending=False)
    )


def get_category_summary_2018(revenue_df, frequency_df):

    return revenue_df.merge(
        frequency_df,
        on="product_category_name_english",
        how="left"
    )

def get_2018_jan_june_category_revenue(df):

    df = df[df["month"] <= 6]

    return (
        df
        .groupby(
            "product_category_name_english",
            as_index=False
        )
        .agg(
            total_revenue=("total_sales_value", "sum")
        )
    )
def plot_2018_category_consistency(df):

    fig = px.scatter(
        df,
        x="top_10_months",
        y="total_revenue",
        hover_name="product_category_name_english",
        hover_data={
            "top_10_months": True,
            "total_revenue": ":,.2f",
            "product_category_name_english": False
        },
        labels={
            "top_10_months": "Number of Months in Top 10",
            "total_revenue": "Total Revenue"
        },
        title="2018 Category Revenue vs Top-10 Consistency — Jan-June"
    )

    return fig

def compare_category_revenue(category_revenue_2017_jan_june, category_revenue_2018):

    comparison = (
        category_revenue_2017_jan_june
        .merge(
            category_revenue_2018,
            on="product_category_name_english",
            how="outer",
            suffixes=("_2017", "_2018")
        )
        .fillna(0)
    )

    return comparison

def get_category_revenue_changes(comparison_df):

    comparison_df = comparison_df.copy()

    comparison_df["revenue_change"] = (
        comparison_df["total_revenue_2018"]
        - comparison_df["total_revenue_2017"]
    )

    top_increases = (
        comparison_df
        .sort_values("revenue_change", ascending=False)
        .head(5)
    )

    top_decreases = (
        comparison_df
        .sort_values("revenue_change", ascending=True)
        .head(5)
    )

    return pd.concat([
        top_increases,
        top_decreases
    ])

def plot_category_revenue_changes(df):

    fig = px.bar(
        df.sort_values("revenue_change"),
        x="revenue_change",
        y="product_category_name_english",
        orientation="h",
        labels={
            "revenue_change": "Revenue Change (2018 Jan-June - 2017 Jan-June)",
            "product_category_name_english": "Product Category"
        },
        title="Biggest Category Revenue Changes: 2017 vs 2018"
    )

    return fig

def get_2017_jan_june_category_revenue(df):

    df = df[df["month"] <= 6]

    return (
        df
        .groupby(
            "product_category_name_english",
            as_index=False
        )
        .agg(
            total_revenue=("total_sales_value", "sum")
        )
    )

