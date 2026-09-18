import pandas as pd
import plotly.express as px


def get_rfm_data(engine):
    query = """
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
        r.rfm_total_score AS rfm_score
    FROM `olist-data-pipeline-507001.olist_mart.fct_customer_rfm` AS r
    LEFT JOIN `olist-data-pipeline-507001.olist_mart.dim_customer` AS c
        ON r.customer_key = c.customer_key
    ORDER BY r.monetary DESC
    """

    return pd.read_sql(query, con=engine)


def get_rfm_segment_summary(rfm_df):

    segment_df = (
        rfm_df
        .groupby("customer_segment", as_index=False)
        .agg(
            total_revenue=("monetary_value", "sum"),
            customer_count=("customer_unique_id", "nunique"),
            average_customer_value=("monetary_value", "mean"),
        )
        .sort_values("total_revenue", ascending=True)
    )

    segment_df["total_revenue"] = (
        segment_df["total_revenue"].round(2)
    )

    segment_df["average_customer_value"] = (
        segment_df["average_customer_value"].round(2)
    )

    return segment_df


def get_top_customers(
    rfm_df,
    top_n=10,
    metric="monetary_value",
):

    columns = [
        "customer_unique_id",
        "customer_segment",
        "recency_days",
        "frequency",
        "monetary_value",
        "rfm_score",
    ]

    ascending = metric == "recency_days"

    return (
        rfm_df[columns]
        .sort_values(metric, ascending=ascending)
        .head(top_n)
        .copy()
    )


def plot_rfm_segment_summary(
    rfm_segment_df,
    metric="total_revenue",
):

    df = rfm_segment_df.copy()

    if metric == "total_revenue":
        title = "Revenue by RFM Customer Segment"
        x_label = "Total Revenue"

    elif metric == "customer_count":
        title = "Customers by RFM Segment"
        x_label = "Number of Customers"

    else:
        title = "Average Customer Value by RFM Segment"
        x_label = "Average Customer Value"

    fig = px.bar(
        df,
        x=metric,
        y="customer_segment",
        orientation="h",
        title=title,
        labels={
            metric: x_label,
            "customer_segment": "Customer Segment",
        },
    )

    fig.update_layout(
        height=500,
        yaxis={"categoryorder": "total ascending"},
        hovermode="closest",
    )

    return fig


def plot_rfm_top_customers(
    rfm_df,
    top_n=10,
    metric="monetary_value",
):

    ascending = metric == "recency_days"

    df = (
        rfm_df
        .sort_values(metric, ascending=ascending)
        .head(top_n)
        .copy()
    )

    df["customer"] = (
        df["customer_unique_id"]
        .astype(str)
        .str.slice(0, 12)
    )

    if metric == "monetary_value":
        title = f"Top {len(df)} Customers by Monetary Value"
        x_label = "Monetary Value"

    elif metric == "frequency":
        title = f"Top {len(df)} Customers by Purchase Frequency"
        x_label = "Purchase Frequency"

    else:
        title = f"Most Recent {len(df)} Customers"
        x_label = "Recency (Days)"

    fig = px.bar(
        df,
        x=metric,
        y="customer",
        orientation="h",
        title=title,
        labels={
            metric: x_label,
            "customer": "Customer",
        },
        hover_data=[
            "customer_segment",
            "recency_days",
            "frequency",
            "monetary_value",
            "rfm_score",
        ],
    )

    fig.update_layout(
        height=500,
        hovermode="closest",
    )

    return fig

