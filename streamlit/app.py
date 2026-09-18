import streamlit as st
from sqlalchemy import create_engine


from holiday_category_demand import (
    get_holiday_category_changes,
    get_biggest_holiday_changes_2018,
    plot_holiday_category_changes_2018,
)


from holiday_analysis import (
    get_holiday_daily_metrics_by_quarter,  
)


from november_spike import (
    get_order_vs_aov,
    get_november_daily_activity,
    get_category_spike,
)


from category_analysis import (
    get_category_sales,
    add_half_year,
    get_half_year_revenue,
    get_top_10_each_month,
    get_category_frequency,
    get_category_summary,
    get_2018_category_revenue,
    get_top_10_each_month_2018,
    get_category_frequency_2018,
    get_category_summary_2018,
    get_2017_jan_june_category_revenue,
    get_2018_jan_june_category_revenue,
    compare_category_revenue,
    get_category_revenue_changes,
    plot_category_revenue_changes,
    get_monthly_region_sales,
    add_brazil_region,
    plot_2017_category_consistency_combined,
    plot_2018_category_consistency,
)


from rfm_analysis import (
    get_rfm_data,
    get_rfm_segment_summary,
    get_top_customers,
    plot_rfm_segment_summary,
    plot_rfm_top_customers,
)


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Olist Business Dashboard",
    layout="wide",
)


st.title("Olist Business Dashboard")


st.info(
    """
    **Data Coverage & Methodology**

    - Data is sourced from **BigQuery**.
    - Queries are executed using **SQLAlchemy** and data is processed using **pandas**.
    - The standard project workflow is run before analysis to ensure the required data tables are available.
    - **Latest purchase date:** October 17, 2018
    - **Latest delivered order:** August 2018
    - For overall general sales analysis, **2018 period ends in June for better comparison**.
    - **2016 observations are excluded because the year is incomplete.**

    **Revenue Metric**

    - **GMV (Gross Merchandise Value) is used as the revenue proxy.**
    - GMV is calculated as: `SUM(price + freight_value)`
    - This represents the recorded product value together with associated freight charges.
    - **Profit is not calculated**, as the dataset does not contain sufficient cost information to determine product and operating costs.

    **Overall Business Question:**  

    **What drives Olist's revenue, when do important changes occur, which
    products and regions contribute to those changes, and which customers
    generate the most value?**

    This supports better inventory, fulfilment, logistics, staffing, marketing,
    and customer-retention decisions."


    """
)


engine = create_engine(
    "bigquery://olist-data-pipeline-507001"
)


# ============================================================
# CREATE TABS
# ============================================================

category_tab, november_tab, holiday_tab, customer_tab = st.tabs(
    [
        "Category & Regional Trends",
        "Nov 2017 Spike Analysis",
        "Holiday Trend",
        "Customer Analysis",
    ]
)


# ============================================================
# TAB 1 — CATEGORY & REGIONAL TRENDS
# ============================================================

with category_tab:

    st.header("Category Performance & Sales Revenue Trends")

    st.write(
        "Explore product category performance and revenue trends "
        "across Olist's marketplace."
    )

    # --------------------------------------------------------
    # PRODUCT CATEGORY ANALYSIS
    # --------------------------------------------------------

    st.subheader("Revenue Drivers: Product Categories")


    category_sales_2017_monthly = get_category_sales(engine, 2017)


    category_revenue_2017_jan_june = (
        get_2017_jan_june_category_revenue(
            category_sales_2017_monthly
        )
    )


    category_sales_2017_monthly = add_half_year(
        category_sales_2017_monthly
    )


    half_year_revenue_2017 = get_half_year_revenue(
        category_sales_2017_monthly
    )


    top_10_each_month_2017 = get_top_10_each_month(
        category_sales_2017_monthly
    )


    category_frequency_2017 = get_category_frequency(
        top_10_each_month_2017
    )


    category_summary_2017 = get_category_summary(
        half_year_revenue_2017,
        category_frequency_2017,
    )


    category_sales_2018_monthly = get_category_sales(engine, 2018)

    # Keep January-June 2018 for the comparison

    category_sales_2018_jan_june = category_sales_2018_monthly[
        category_sales_2018_monthly["month"] <= 6
    ].copy()


    category_revenue_2018 = get_2018_category_revenue(
        category_sales_2018_jan_june
    )


    category_revenue_2018_jan_june = (
        get_2018_jan_june_category_revenue(
            category_sales_2018_jan_june
        )
    )


    category_revenue_comparison = compare_category_revenue(
        category_revenue_2017_jan_june,
        category_revenue_2018_jan_june,
    )


    comparison_chart_data = get_category_revenue_changes(
        category_revenue_comparison
    )


    top_10_each_month_2018 = get_top_10_each_month_2018(
        category_sales_2018_jan_june
    )


    category_frequency_2018 = get_category_frequency_2018(
        top_10_each_month_2018
    )


    category_summary_2018 = get_category_summary_2018(
        category_revenue_2018,
        category_frequency_2018,
    )


    fig = plot_2017_category_consistency_combined(
        category_summary_2017
    )


    st.plotly_chart(
        fig,
        use_container_width=True
    )



    fig_2018 = plot_2018_category_consistency(
        category_summary_2018
    )


    st.plotly_chart(
        fig_2018,
        use_container_width=True
    )


    fig_comparison = plot_category_revenue_changes(
        comparison_chart_data
    )


    st.plotly_chart(
        fig_comparison,
        use_container_width=True
    )


    st.info(
        """
        **Insight:**

        Watches & Gifts, Health & Beauty, and Bed & Bath Table
        consistently appeared among the Top 10 categories by monthly frequency
        in 2017 and generated relatively high total revenue.

        These three categories also maintained a strong Top 10 presence in
        2018 (January-June) and were among the categories with the highest
        total revenue.

        Comparing January-June 2017 with January-June 2018, they also recorded
        some of the largest revenue increases. Growth was concentrated in several major categories, 
        while the largest declines were relatively small in absolute value

        Therefore, their combination of consistent Top 10 presence, high
        revenue contribution, and strong revenue growth identifies them as
        important contributors to overall category performance.

        This helps with inventory planning, order fufilment and resources.
        """
    )


    st.subheader("Revenue Drivers: Regional Trends")


    st.markdown(
        """
        Examine how sales are distributed across Brazil's regions and how
        regional revenue changes over time.

        **Monthly Sales Trend by Customer Region**

        The monthly sales analysis groups Brazilian states into five geographic regions:

        - **Southeast**
        - **South**
        - **Northeast**
        - **Central-West**
        - **North**
        """
    )


    monthly_region_sales = get_monthly_region_sales(engine)


    monthly_region_sales = add_brazil_region(
        monthly_region_sales
    )


    region_chart_data = monthly_region_sales.pivot(
        index="month",
        columns="region",
        values="gmv"
    )


    st.line_chart(region_chart_data)


    st.info(
        """
        **Insight:**

        The Southeast was the dominant sales region throughout
        the analysis period. The South and Northeast formed the second tier,
        while the Central-West and North contributed smaller monthly GMV.

        A notable sales spike occurred across all five regions in November
        2017. This suggests that the increase was not isolated to a single
        geographic region.

        The next analysis therefore examines whether the November spike was
        driven by higher order volume, changes in Average Order Value, a
        concentration of sales on a small number of high-activity days, or
        specific product categories.
        """
    )


# ============================================================
# TAB 2 — NOVEMBER 2017 SALES SPIKE
# ============================================================

with november_tab:

    st.header("November 2017 Sales Spike")


    st.write(
        "We investigate the sharp increase in sales observed in November 2017 "
        "to determine whether it was driven mainly by order volume, "
        "customer spending, daily activity, or specific product categories."
    )


    # --------------------------------------------------------
    # ORDER VOLUME VS AOV
    # --------------------------------------------------------


    st.subheader("Order Volume vs Average Order Value")


    st.write(
        "We compare October, November and December 2017 to distinguish "
        "a volume-driven sales increase from an AOV-driven increase."
    )


    order_vs_aov = get_order_vs_aov(engine)


    st.dataframe(
        order_vs_aov,
        use_container_width=True,
    )


    st.write("**Monthly Orders**")


    st.bar_chart(
        order_vs_aov.set_index("year_month")["orders"]
    )


    st.write("**Monthly Average Order Value (AOV)**")


    st.bar_chart(
        order_vs_aov.set_index("year_month")["avg_order_value"]
    )

    oct_rows = order_vs_aov.loc[
        order_vs_aov["year_month"] == "2017-10"
    ]

    nov_rows = order_vs_aov.loc[
        order_vs_aov["year_month"] == "2017-11"
    ]

    if not oct_rows.empty and not nov_rows.empty:

        oct_row = oct_rows.iloc[0]

        nov_row = nov_rows.iloc[0]

        oct_to_nov_orders_pct = (
            (nov_row["orders"] / oct_row["orders"]) - 1
        ) * 100

        oct_to_nov_gmv_pct = (
            (nov_row["gmv"] / oct_row["gmv"]) - 1
        ) * 100

        oct_to_nov_aov_pct = (
            (nov_row["avg_order_value"] /
             oct_row["avg_order_value"]) - 1
        ) * 100

        st.write("**October → November change**")

        col1, col2, col3 = st.columns(3)

        col1.metric(
            "Order Growth",
            f"{oct_to_nov_orders_pct:.1f}%",
        )

        col2.metric(
            "GMV Growth",
            f"{oct_to_nov_gmv_pct:.1f}%",
        )

        col3.metric(
            "AOV Change",
            f"{oct_to_nov_aov_pct:.1f}%",
        )

        st.info(
            """
            **Insight:**
             November 2017 was primarily volume-driven. Orders
            increased sharply from October to November, while GMV also
            increased strongly. Average Order Value decreased rather than
            increased.
            Therefore, the November spike was mainly associated with more
            orders being placed, rather than customers spending more per
            transaction.
            """
        )

    else:

        st.warning(
            "October or November 2017 data is unavailable, "
            "so the October → November comparison cannot be calculated."
        )

    # --------------------------------------------------------
    # DAILY ACTIVITY
    # --------------------------------------------------------


    st.subheader("Daily Activity During November 2017")


    st.write(
        "We examine daily GMV during November 2017 to determine whether "
        "the monthly increase was spread evenly across the month or "
        "concentrated around specific dates."
    )


    nov_daily = get_november_daily_activity(engine)

    st.line_chart(
        nov_daily.set_index("date_key")["gmv"]
    )


    if not nov_daily.empty:

        peak = nov_daily.loc[
            nov_daily["gmv"].idxmax()
        ]


        st.write(
            f"**Peak date:** {int(peak['date_key'])}"
        )


        col1, col2 = st.columns(2)


        col1.metric(
            "Peak Orders",
            f"{int(peak['order_count']):,}",
        )


        col2.metric(
            "Peak GMV",
            f"{peak['gmv']:,.2f}",
        )


        st.info(
            f"""
            **Insight:**

            The daily drill-down identifies **{int(peak['date_key'])}** as the dominant peak.
            The increase is therefore not spread evenly throughout November; a
            substantial part of the monthly increase is concentrated around a
            short event period.

            This pattern is consistent with an event-driven shopping surge.

            The analysis demonstrates the event pattern from the transaction data;
            causal attribution should be stated carefully unless external
            promotional data is also introduced.
            """
        )

    else:

        st.warning(
            "No November daily data is available, so the peak cannot be calculated."
        )
    
    # --------------------------------------------------------
    # CATEGORY CONTRIBUTION
    # --------------------------------------------------------


    st.subheader(
        "Product Categories Responsible for the October → November Increase"
    )


    st.write(
        "We compare October and November GMV by product category "
        "to identify which categories contributed most to the increase."
    )


    category_spike = get_category_spike(engine)


    top10 = (
        category_spike
        .head(10)
        .sort_values(
            "gmv_increase",
            ascending=True,
        )
    )


    st.bar_chart(
        top10.set_index("product_category")["gmv_increase"]
    )


    st.write("**Top 10 Category Contributions**")


    st.dataframe(
        top10[
            [
                "product_category",
                "gmv_increase",
                "growth_pct",
                "contribution_to_spike_pct",
            ]
        ],
        use_container_width=True,
    )


    st.info(
        """
        **Insight:** 
        
        The November increase is broad-based rather than being
        caused by a single category. The largest contributors include
        bed_bath_table, health_beauty, furniture_decor, watches_gifts,
        toys, and computers_accessories.


        For businesses, identifying these higher activity periods and popular product categories can support **inventory planning, order fulfilment capacity,
        staffing, and logistics preparation** around major shopping events especially surrounding the days of a holiday.

        """
    )


# ============================================================
# TAB 3 — HOLIDAY TREND
# ============================================================

with holiday_tab:

    st.header("Holiday Sales Impact")


    st.write(
        "Having established the main geographical and product revenue-driving "
        "categories, we now examine whether holiday periods change overall "
        "sales activity and product mix."
    )


    st.write(
        "We compare holiday and non-holiday days from January 2017 to June 2018 "
        "to understand whether customer purchasing behaviour changes during holidays."
    )


    # --------------------------------------------------------
    # AVERAGE HOLIDAY ACTIVITY
    # --------------------------------------------------------


    st.subheader("Average Holiday Activity")


    st.write(
        "Because there are many more non-holiday days than holiday days, "
        "total GMV and order counts alone may not provide a fair comparison. "
        "We therefore compare average orders and GMV per day."
    )


    holiday_daily_df = get_holiday_daily_metrics_by_quarter(engine)


    st.write("**Average Orders per Day**")


    st.bar_chart(
        holiday_daily_df.pivot(
            index="year_quarter",
            columns="day_type",
            values="avg_orders_per_day",
        )
    )


    st.write("**Average GMV per Day**")


    st.bar_chart(
        holiday_daily_df.pivot(
            index="year_quarter",
            columns="day_type",
            values="avg_gmv_per_day",
        )
    )


    st.info(
        """
        **Finding:** Holiday days generally record fewer orders per day and
        lower GMV per day than non-holiday days. This suggests that the lower
        total holiday GMV is not simply due to having fewer holiday dates;
        daily sales activity is also generally lower.
        """
    )


    # --------------------------------------------------------
    # HOLIDAY CATEGORY DEMAND
    # --------------------------------------------------------


    st.subheader("Holiday Product-Category Behaviour")


    st.write(
        "Overall holiday demand is generally lower than non-holiday demand. "
        "We therefore examine whether holidays nevertheless change the "
        "composition and timing of category-level purchases."
    )


    with st.expander("Analysis Approach"):


        st.markdown(
            """
            - **7 days before + holiday period + 7 days after:** provides
              broader context around each holiday rather than examining the
              holiday date alone.

            - **Complete observation window:** a holiday is analysed only when
              the full **Before → Holiday → After** window is available.

            - **Absolute change:** used to avoid misleading or unusually large
              percentage changes caused by categories with very small baseline
              values.
            """
        )


    all_holiday_results_df = get_holiday_category_changes(
        engine
    )


    biggest_holiday_changes_2018 = (
        get_biggest_holiday_changes_2018(
            all_holiday_results_df
        )
    )

    fig = plot_holiday_category_changes_2018(
        biggest_holiday_changes_2018
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
    )

    st.info(
        """
        **Insight:**

        Holiday periods generally show lower average daily sales activity than
        non-holiday days. However, the category-level analysis shows that
        holiday periods can still create noticeable changes in demand for
        specific product categories.

        This suggests that holiday planning should focus not only on overall
        sales volume, but also on **category-specific demand patterns**.
        Identifying categories with the largest changes can support inventory
        planning, product availability, fulfilment capacity, and promotional
        planning around holiday periods.
        """
    )
 
# ============================================================
# TAB 4 — CUSTOMER ANALYSIS
# ============================================================

with customer_tab:

    st.header("Customer Value & Retention — RFM")


    st.write(
        "After identifying the products and periods driving revenue, "
        "we next examine the customers behind that revenue. "
        "RFM segmentation helps identify high-value customers, "
        "recent customers, and customers who may require re-engagement."
    )


    rfm_df = get_rfm_data(engine)
   
    unmatched = rfm_df["customer_unique_id"].isna().sum()
    
   

    segments = sorted(
        rfm_df["customer_segment"]
        .dropna()
        .unique()
    )


    selected_segments = st.multiselect(
        "Filter by Customer Segment",
        options=segments,
        default=segments,
    )


    filtered_rfm = rfm_df[
        rfm_df["customer_segment"].isin(selected_segments)
    ].copy()


    total_customers = (
        filtered_rfm["customer_key"].nunique()
    )


    total_revenue = (
        filtered_rfm["monetary_value"].sum()
    )


    average_customer_value = (
        filtered_rfm["monetary_value"].mean()
    )


    col1, col2, col3 = st.columns(3)


    col1.metric(
        "Customers",
        f"{total_customers:,}",
    )


    col2.metric(
        "Total Revenue",
        f"${total_revenue:,.2f}",
    )


    col3.metric(
        "Average Customer Value",
        f"${average_customer_value:,.2f}",
    )


    # --------------------------------------------------------
    # RFM SEGMENT PERFORMANCE
    # --------------------------------------------------------


    st.subheader("RFM Segment Performance")


    segment_metric = st.selectbox(
        "Compare segments by",
        [
            "Revenue",
            "Customer Count",
            "Average Customer Value",
        ],
    )


    if segment_metric == "Revenue":

        metric_column = "total_revenue"


    elif segment_metric == "Customer Count":

        metric_column = "customer_count"


    else:

        metric_column = "average_customer_value"


    segment_df = get_rfm_segment_summary(
        filtered_rfm
    )


    fig = plot_rfm_segment_summary(
        segment_df,
        metric=metric_column,
    )


    st.plotly_chart(
        fig,
        use_container_width=True
    )


    # --------------------------------------------------------
    # TOP CUSTOMERS
    # --------------------------------------------------------


    st.subheader("Top Customers")

    


    top_n = st.slider(
        "Number of customers",
        min_value=5,
        max_value=50,
        value=10,
        step=5,
    )


    customer_metric = st.selectbox(
        "Rank customers by",
        [
            "Monetary Value",
            "Purchase Frequency",
            "Recency",
        ],
    )


    if customer_metric == "Monetary Value":

        metric_column = "monetary_value"


    elif customer_metric == "Purchase Frequency":

        metric_column = "frequency"


    else:

        metric_column = "recency_days"


    top_customers_df = get_top_customers(
        filtered_rfm,
        top_n=top_n,
        metric=metric_column,
    )


    fig = plot_rfm_top_customers(
        filtered_rfm,
        top_n=top_n,
        metric=metric_column,
    )


    st.plotly_chart(
        fig,
        use_container_width=True
    )

    st.subheader("RFM Score Guide")
    
    st.markdown("""
    | Dimension     | Score 1       | Score 2    | Score 3   | Score 4      | Score 5      |
    |---------------|---------------|------------|-----------|--------------|--------------|
    | **Recency**   | Least recent  |            | Average   |              | Most recent  |
    | **Frequency** | 1 order       | 2 orders   | 3 orders  | 4+ orders    | —            |
    | **Monetary**  | Lowest 20%    | 20–40%     | 40–60%    | 60–80%       | Highest 20%  |
    """)

    st.subheader("Customer Details")


    st.dataframe(
        top_customers_df,
        use_container_width=True,
        hide_index=True,
    )


    st.info(
    """
    **Insight:**

    
     It allows for important retention opportunities as it highlights which coustomer groups are most valuable. 
     
     **Big Spenders** represent customers whose continued engagement can protect a significant source of revenue, while **Needs Attention** and **Lost Customers** indicate customers who have previously generated value but may require re-engagement.
     Therefore, the RFM analysis suggests that customer retention should focus not only on acquiring new customers, but also on protecting existing high-value customers and attempting to reactivate previously valuable customers.
    """
)