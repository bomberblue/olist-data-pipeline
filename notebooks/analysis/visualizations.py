# visualizations.py

"""
Generate business-facing charts from exported Olist analysis CSV files.

Run analysis.py first.

Charts:
1. Monthly Sales Trend
2. RFM - Top Customers
3. RFM - Segment Summary
4. Holiday Impact
5. Holiday GMV by Quarter
6. Holiday AOV by Quarter
7. Average Orders per Day by Quarter
8. Average GMV per Day by Quarter
9. Holiday vs Non-Holiday Product Category Mix
"""

import logging

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from config import OUTPUT_DIR


logger = logging.getLogger(__name__)


def _read_csv(filename):
    path = OUTPUT_DIR / filename

    if not path.exists():
        raise FileNotFoundError(
            f"{path} not found. Run analysis.py first."
        )

    return pd.read_csv(path)


def _save_figure(filename):
    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    path = OUTPUT_DIR / filename

    plt.tight_layout()

    plt.savefig(
        path,
        dpi=150,
        bbox_inches="tight",
    )

    plt.close()

    logger.info(
        "Saved chart: %s",
        path,
    )


def _add_bar_labels_vertical(
    ax,
    bars,
    fmt="{:,.2f}",
    offset=3,
):
    for bar in bars:
        height = bar.get_height()

        if pd.isna(height):
            continue

        ax.annotate(
            fmt.format(height),
            xy=(
                bar.get_x()
                + bar.get_width() / 2,
                height,
            ),
            xytext=(0, offset),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=8,
        )


def _add_bar_labels_horizontal(
    ax,
    bars,
    fmt="{:,.2f}",
    offset=3,
):
    for bar in bars:
        width = bar.get_width()

        if pd.isna(width):
            continue

        ax.annotate(
            fmt.format(width),
            xy=(
                width,
                bar.get_y()
                + bar.get_height() / 2,
            ),
            xytext=(offset, 0),
            textcoords="offset points",
            ha="left",
            va="center",
            fontsize=8,
        )


def _grouped_quarter_bar(
    df,
    value_col,
    title,
    ylabel,
    filename,
    label_fmt="{:,.2f}",
):
    pivot_df = (
        df.pivot(
            index="year_quarter",
            columns="day_type",
            values=value_col,
        )
        .sort_index()
    )

    quarters = pivot_df.index.tolist()

    holiday_values = (
        pivot_df["Holiday"].to_numpy()
        if "Holiday" in pivot_df.columns
        else np.full(
            len(pivot_df),
            np.nan,
        )
    )

    non_holiday_values = (
        pivot_df["Non-Holiday"].to_numpy()
        if "Non-Holiday" in pivot_df.columns
        else np.full(
            len(pivot_df),
            np.nan,
        )
    )

    x = np.arange(
        len(quarters)
    )

    width = 0.38

    fig, ax = plt.subplots(
        figsize=(11, 6)
    )

    holiday_bars = ax.bar(
        x - width / 2,
        holiday_values,
        width,
        label="Holiday",
    )

    non_holiday_bars = ax.bar(
        x + width / 2,
        non_holiday_values,
        width,
        label="Non-Holiday",
    )

    ax.set_title(
        title
    )

    ax.set_xlabel(
        "Quarter"
    )

    ax.set_ylabel(
        ylabel
    )

    ax.set_xticks(x)

    ax.set_xticklabels(
        quarters,
        rotation=45,
        ha="right",
    )

    ax.legend(
        title="Day Type"
    )

    ax.grid(
        axis="y",
        alpha=0.2,
    )

    _add_bar_labels_vertical(
        ax,
        holiday_bars,
        fmt=label_fmt,
    )

    _add_bar_labels_vertical(
        ax,
        non_holiday_bars,
        fmt=label_fmt,
    )

    _save_figure(
        filename
    )


# ============================================================
# MONTHLY SALES
# ============================================================

def plot_monthly_sales_trend():
    """
    Plot monthly GMV by Brazilian customer region.
    """

    df = _read_csv(
        "monthly_sales_trend.csv"
    )

    if df.empty:
        raise ValueError(
            "monthly_sales_trend.csv contains no rows."
        )

    pivot_df = (
        df.pivot(
            index="year_month",
            columns="region",
            values="gmv",
        )
        .sort_index()
    )

    months = pivot_df.index.tolist()

    x = np.arange(
        len(months)
    )

    fig, ax = plt.subplots(
        figsize=(13, 7)
    )

    for region in pivot_df.columns:

        ax.plot(
            x,
            pivot_df[region],
            marker="o",
            linewidth=2,
            label=region,
        )

    ax.set_title(
        "Monthly Sales Trend by Customer Region\n"
        "Analysis Period: Jan 2017 – Jun 2018"
    )

    ax.set_xlabel(
        "Month"
    )

    ax.set_ylabel(
        "GMV"
    )

    ax.set_xticks(x)

    ax.set_xticklabels(
        months,
        rotation=45,
        ha="right",
    )

    ax.legend(
        title="Region"
    )

    ax.grid(
        axis="y",
        alpha=0.2,
    )

    _save_figure(
        "monthly_sales_trend.png"
    )


# ============================================================
# RFM
# ============================================================

def plot_rfm_top_customers(
    top_n=10,
):
    df = _read_csv(
        "rfm_analysis.csv"
    ).head(top_n)

    labels = (
        df["customer_unique_id"]
        .astype(str)
        .str.slice(0, 12)
    )

    plot_df = pd.DataFrame(
        {
            "customer": labels,
            "monetary_value":
                df["monetary_value"],
        }
    ).sort_values(
        "monetary_value",
        ascending=True,
    )

    fig, ax = plt.subplots(
        figsize=(10, 6)
    )

    bars = ax.barh(
        plot_df["customer"],
        plot_df["monetary_value"],
    )

    ax.set_title(
        f"Top {len(plot_df)} Customers by Monetary Value"
    )

    ax.set_xlabel(
        "Monetary Value"
    )

    ax.set_ylabel(
        "Customer"
    )

    ax.grid(
        axis="x",
        alpha=0.2,
    )

    _add_bar_labels_horizontal(
        ax,
        bars,
    )

    _save_figure(
        "rfm_top_customers.png"
    )


def plot_rfm_segment_summary():
    df = _read_csv(
        "rfm_segment_summary.csv"
    ).sort_values(
        "total_revenue",
        ascending=True,
    )

    fig, ax = plt.subplots(
        figsize=(10, 6)
    )

    bars = ax.barh(
        df["customer_segment"],
        df["total_revenue"],
    )

    ax.set_title(
        "Revenue by RFM Customer Segment"
    )

    ax.set_xlabel(
        "Total Revenue"
    )

    ax.set_ylabel(
        "Customer Segment"
    )

    ax.grid(
        axis="x",
        alpha=0.2,
    )

    _add_bar_labels_horizontal(
        ax,
        bars,
    )

    _save_figure(
        "rfm_segment_summary.png"
    )


# ============================================================
# HOLIDAY OVERALL
# ============================================================

def plot_holiday_impact():
    df = _read_csv(
        "holiday_impact.csv"
    )

    fig, ax = plt.subplots(
        figsize=(7, 5)
    )

    bars = ax.bar(
        df["day_type"],
        df["gmv"],
    )

    ax.set_title(
        "Holiday vs Non-Holiday GMV"
    )

    ax.set_xlabel(
        "Day Type"
    )

    ax.set_ylabel(
        "Total GMV"
    )

    ax.grid(
        axis="y",
        alpha=0.2,
    )

    _add_bar_labels_vertical(
        ax,
        bars,
    )

    _save_figure(
        "holiday_impact.png"
    )


# ============================================================
# HOLIDAY QUARTERLY GMV / AOV
# ============================================================

def plot_holiday_gmv_by_quarter():
    df = _read_csv(
        "holiday_impact_by_quarter.csv"
    )

    _grouped_quarter_bar(
        df=df,
        value_col="gmv",
        title=(
            "Total GMV by Quarter: "
            "Holiday vs Non-Holiday"
        ),
        ylabel="Total GMV",
        filename=(
            "holiday_gmv_by_quarter.png"
        ),
    )


def plot_holiday_aov_by_quarter():
    df = _read_csv(
        "holiday_impact_by_quarter.csv"
    )

    _grouped_quarter_bar(
        df=df,
        value_col="avg_order_value",
        title=(
            "Average Order Value by Quarter: "
            "Holiday vs Non-Holiday"
        ),
        ylabel="Average Order Value",
        filename=(
            "holiday_aov_by_quarter.png"
        ),
    )


# ============================================================
# HOLIDAY NORMALIZED DAILY METRICS
# ============================================================

def plot_holiday_avg_orders_per_day():
    df = _read_csv(
        "holiday_daily_metrics_by_quarter.csv"
    )

    _grouped_quarter_bar(
        df=df,
        value_col="avg_orders_per_day",
        title=(
            "Average Orders per Day by Quarter: "
            "Holiday vs Non-Holiday"
        ),
        ylabel="Average Orders per Day",
        filename=(
            "holiday_avg_orders_per_day.png"
        ),
    )


def plot_holiday_avg_gmv_per_day():
    df = _read_csv(
        "holiday_daily_metrics_by_quarter.csv"
    )

    _grouped_quarter_bar(
        df=df,
        value_col="avg_gmv_per_day",
        title=(
            "Average GMV per Day by Quarter: "
            "Holiday vs Non-Holiday"
        ),
        ylabel="Average GMV per Day",
        filename=(
            "holiday_avg_gmv_per_day.png"
        ),
    )


def plot_holiday_product_category_mix():
    """
    Compare Holiday vs Non-Holiday product category GMV share.
    """

    df = _read_csv(
        "holiday_product_category_mix.csv"
    )

    if df.empty:
        raise ValueError(
            "holiday_product_category_mix.csv contains no rows."
        )

    pivot_df = df.pivot(
        index="product_category",
        columns="day_type",
        values="gmv_share_pct",
    ).fillna(0)

    # Order categories using combined GMV from both groups
    category_order = (
        df.groupby("product_category")["gmv"]
        .sum()
        .sort_values(ascending=True)
        .index
    )

    pivot_df = pivot_df.reindex(
        category_order
    )

    holiday_values = (
        pivot_df["Holiday"].to_numpy()
        if "Holiday" in pivot_df.columns
        else np.zeros(len(pivot_df))
    )

    non_holiday_values = (
        pivot_df["Non-Holiday"].to_numpy()
        if "Non-Holiday" in pivot_df.columns
        else np.zeros(len(pivot_df))
    )

    y = np.arange(
        len(pivot_df)
    )

    height = 0.38

    fig, ax = plt.subplots(
        figsize=(11, 7)
    )

    holiday_bars = ax.barh(
        y - height / 2,
        holiday_values,
        height,
        label="Holiday",
    )

    non_holiday_bars = ax.barh(
        y + height / 2,
        non_holiday_values,
        height,
        label="Non-Holiday",
    )

    ax.set_title(
        "Product Category GMV Mix: Holiday vs Non-Holiday"
    )

    ax.set_xlabel(
        "Share of GMV (%)"
    )

    ax.set_ylabel(
        "Product Category"
    )

    ax.set_yticks(y)

    ax.set_yticklabels(
        pivot_df.index
    )

    ax.legend(
        title="Day Type"
    )

    ax.grid(
        axis="x",
        alpha=0.2,
    )

    _add_bar_labels_horizontal(
        ax,
        holiday_bars,
        fmt="{:,.2f}%",
    )

    _add_bar_labels_horizontal(
        ax,
        non_holiday_bars,
        fmt="{:,.2f}%",
    )

    _save_figure(
        "holiday_product_category_mix.png"
    )


# ============================================================
# GENERATE ALL
# ============================================================

def generate_all_charts():
    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    plot_monthly_sales_trend()
    plot_rfm_top_customers()
    plot_rfm_segment_summary()

    plot_holiday_impact()
    plot_holiday_gmv_by_quarter()
    plot_holiday_aov_by_quarter()

    plot_holiday_avg_orders_per_day()
    plot_holiday_avg_gmv_per_day()
    plot_holiday_product_category_mix()

    print(
        f"Charts saved to: {OUTPUT_DIR}"
    )


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format=(
            "%(asctime)s | %(levelname)s | "
            "%(name)s | %(message)s"
        ),
    )

    generate_all_charts()
