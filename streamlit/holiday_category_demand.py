import pandas as pd
import plotly.express as px




def get_holiday_category_changes(engine):
    # Get holiday data from BigQuery
    holidays = pd.read_sql(
        """
        SELECT *
        FROM `olist-data-pipeline-507001.olist_staging.stg_holiday_calendar`
        """,
        engine,
    )

    holidays["hol_date"] = pd.to_datetime(
        holidays["hol_date"]
    ).dt.normalize()

    # Create one row per holiday event
    holiday_events = (
        holidays
        .assign(year=holidays["hol_date"].dt.year)
        .groupby(["year", "hol_name"], as_index=False)
        .agg(
            holiday_start=("hol_date", "min"),
            holiday_end=("hol_date", "max"),
        )
    )

    # Calculate number of holiday days
    holiday_events["holiday_days"] = (
        holiday_events["holiday_end"]
        - holiday_events["holiday_start"]
    ).dt.days + 1

    # Get category sales from BigQuery
    category_sales = pd.read_sql(
        """
        SELECT
            oi.order_date_key,
            oi.price,
            oi.freight_value,
            p.product_category_name_english

        FROM `olist-data-pipeline-507001.olist_mart.fact_order_items` oi
        JOIN `olist-data-pipeline-507001.olist_mart.dim_product` p
            ON oi.product_key = p.product_key
        """,
        engine,
    )

    category_sales["gmv"] = (
    category_sales["price"]
    + category_sales["freight_value"]
)
    # Convert YYYYMMDD into a real date
    category_sales["sales_date"] = pd.to_datetime(
        category_sales["order_date_key"].astype(str),
        format="%Y%m%d",
    )

    # Calculate sales around each holiday
    all_holiday_results = []

    for _, holiday in holiday_events.iterrows():

        window_start = (
            holiday["holiday_start"] - pd.Timedelta(days=7)
        )

        window_end = (
            holiday["holiday_end"] + pd.Timedelta(days=7)
        )

        holiday_data = category_sales[
            (category_sales["sales_date"] >= window_start)
            & (category_sales["sales_date"] <= window_end)
        ].copy()

        expected_days = (
            holiday["holiday_end"]
            - holiday["holiday_start"]
        ).days + 15

        days_available = holiday_data["sales_date"].nunique()

        if days_available < expected_days:
            continue

        holiday_data["period"] = "Before"

        holiday_data.loc[
            holiday_data["sales_date"].between(
                holiday["holiday_start"],
                holiday["holiday_end"],
            ),
            "period",
        ] = "Holiday"

        holiday_data.loc[
            holiday_data["sales_date"] > holiday["holiday_end"],
            "period",
        ] = "After"

        result = (
            holiday_data
            .groupby(
                [
                    "product_category_name_english",
                    "period",
                ],
                as_index=False,
            )[ "gmv" ]
            .sum()
        )

        result = (
            result
            .pivot(
                index="product_category_name_english",
                columns="period",
                values="gmv",
            )
            .fillna(0)
            .reset_index()
        )

        result["year"] = holiday["year"]
        result["holiday"] = holiday["hol_name"]
        result["holiday_days"] = holiday["holiday_days"]

        all_holiday_results.append(result)

    # Combine all holidays
    all_holiday_results_df = pd.concat(
        all_holiday_results,
        ignore_index=True,
    )

    # Calculate daily sales
    all_holiday_results_df["Before_daily"] = (
        all_holiday_results_df["Before"] / 7
    )

    all_holiday_results_df["Holiday_daily"] = (
        all_holiday_results_df["Holiday"]
        / all_holiday_results_df["holiday_days"]
    )

    all_holiday_results_df["After_daily"] = (
        all_holiday_results_df["After"] / 7
    )

    # Calculate change from before → holiday
    all_holiday_results_df["holiday_change_pct"] = (
        (
            all_holiday_results_df["Holiday_daily"]
            - all_holiday_results_df["Before_daily"]
        )
        / all_holiday_results_df["Before_daily"]
    ) * 100

    all_holiday_results_df["holiday_change_value"] = (
        all_holiday_results_df["Holiday_daily"]
        - all_holiday_results_df["Before_daily"]
    )

    # Calculate change from holiday → after
    all_holiday_results_df["after_change_value"] = (
        all_holiday_results_df["After_daily"]
        - all_holiday_results_df["Holiday_daily"]
    )

    return all_holiday_results_df


def get_biggest_holiday_changes_2018(
    all_holiday_results_df,
):
    holiday_2018 = all_holiday_results_df[
        all_holiday_results_df["year"] == 2018
    ].copy()

    biggest_holiday_changes_2018 = (
        holiday_2018
        .assign(
            absolute_change=holiday_2018[
                "holiday_change_value"
            ].abs()
        )
        .sort_values(
            "absolute_change",
            ascending=False,
        )
        .head(10)
    )

    return biggest_holiday_changes_2018


def plot_holiday_category_changes_2018(df):
    plot_data = df.sort_values(
        "holiday_change_value"
    ).copy()

    plot_data["holiday_category"] = (
        plot_data["holiday"]
        + " — "
        + plot_data["product_category_name_english"]
    )

    fig = px.bar(
        plot_data,
        x="holiday_change_value",
        y="holiday_category",
        orientation="h",
        title=(
            "Largest Product Category Sales Changes "
            "Around Holidays — 2018"
        ),
        labels={
            "holiday_change_value": "Change in Daily Sales",
            "holiday_category": "Holiday — Product Category",
        },
        hover_data=[
            "holiday",
            "product_category_name_english",
            "Before_daily",
            "Holiday_daily",
            "After_daily",
            "holiday_change_pct",
        ],
    )

    fig.add_vline(
        x=0,
        line_width=1,
    )

    fig.update_layout(
        height=600,
        hovermode="closest",
    )

    return fig


