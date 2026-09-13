# check_csvs.py

"""Validate expected analysis CSV outputs."""

import sys

import pandas as pd

from config import OUTPUT_DIR


EXPECTED_FILES = {
    "monthly_sales_trend.csv": {
        "year_month",
        "region",
        "order_count",
        "orders_missing_items",
        "gmv",
        "avg_order_value",
    },

    "rfm_analysis.csv": {
        "customer_unique_id",
        "customer_segment",
        "recency_days",
        "frequency",
        "monetary_value",
        "rfm_score",
    },

    "rfm_segment_summary.csv": {
        "customer_segment",
        "customer_count",
        "avg_recency_days",
        "avg_frequency",
        "avg_monetary_value",
        "total_revenue",
        "pct_customers",
        "pct_revenue",
    },

    "holiday_impact.csv": {
        "day_type",
        "order_count",
        "gmv",
        "avg_order_value",
    },

    "holiday_impact_by_quarter.csv": {
        "year_quarter",
        "day_type",
        "order_count",
        "gmv",
        "avg_order_value",
    },

    "holiday_daily_metrics_by_quarter.csv": {
        "year_quarter",
        "day_type",
        "day_count",
        "total_orders",
        "total_gmv",
        "avg_orders_per_day",
        "avg_gmv_per_day",
    },

    "holiday_product_category_mix.csv": {
        "day_type",
        "product_category",
        "units_sold",
        "order_count",
        "gmv",
        "gmv_share_pct",
    },
}


def validate_csv(
    filename,
    required_columns,
):
    path = (
        OUTPUT_DIR
        / filename
    )

    if not path.exists():
        return (
            False,
            f"Missing file: {path}",
        )

    try:
        df = pd.read_csv(
            path
        )

    except Exception as e:
        return (
            False,
            f"Could not read {path}: {e}",
        )

    if df.empty:
        return (
            False,
            f"CSV is empty: {path}",
        )

    missing = (
        required_columns
        - set(df.columns)
    )

    if missing:
        return (
            False,
            f"{filename} missing columns: "
            + ", ".join(
                sorted(missing)
            ),
        )

    return (
        True,
        f"{filename}: OK "
        f"({len(df):,} rows)",
    )


def main():
    print(
        "Checking analysis CSV outputs...\n"
    )

    failed = False

    for filename, columns in EXPECTED_FILES.items():

        ok, message = validate_csv(
            filename,
            columns,
        )

        print(
            f"{'PASS' if ok else 'FAIL'} - {message}"
        )

        if not ok:
            failed = True

    if failed:
        sys.exit(1)

    print(
        "\nAll analysis CSVs passed validation."
    )


if __name__ == "__main__":
    main()
