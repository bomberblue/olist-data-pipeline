# check_csvs.py

"""
Validate the CSV outputs produced by analysis.py.

Checks:
- OUTPUT_DIR exists.
- Exactly the 7 expected CSV files are present.
- Each CSV is readable.
- Each CSV is non-empty.
- Each CSV contains exactly the expected columns.
- No duplicate column names are present.
- Returns exit status 1 if any validation fails, otherwise 0.
"""

import logging
import sys
from pathlib import Path

import pandas as pd

from config import OUTPUT_DIR


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

logger = logging.getLogger(__name__)


EXPECTED_CSVS = {
    "monthly_sales_trend.csv": [
        "year_month",
        "region",
        "order_count",
        "orders_missing_items",
        "gmv",
        "avg_order_value",
    ],

    "rfm_analysis.csv": [
        "customer_key",
        "customer_unique_id",
        "customer_segment",
        "recency_days",
        "frequency",
        "monetary_value",
        "recency_score",
        "frequency_score",
        "monetary_score",
        "rfm_code",
        "rfm_score",
        "customer_state",
        "customer_city",
    ],

    "rfm_segment_summary.csv": [
        "customer_segment",
        "customer_count",
        "avg_recency_days",
        "avg_frequency",
        "avg_monetary_value",
        "total_revenue",
        "pct_customers",
        "pct_revenue",
    ],

    "holiday_impact.csv": [
        "day_type",
        "order_count",
        "gmv",
        "avg_order_value",
    ],

    "holiday_impact_by_quarter.csv": [
        "year_quarter",
        "day_type",
        "order_count",
        "gmv",
        "avg_order_value",
    ],

    "holiday_daily_metrics_by_quarter.csv": [
        "year_quarter",
        "day_type",
        "day_count",
        "total_orders",
        "total_gmv",
        "avg_orders_per_day",
        "avg_gmv_per_day",
    ],

    "holiday_product_category_mix.csv": [
        "day_type",
        "product_category",
        "units_sold",
        "order_count",
        "gmv",
        "gmv_share_pct",
    ],
}


def validate_csv(file_path: Path, expected_columns):
    """Validate one CSV and return a list of validation errors."""

    errors = []

    try:
        df = pd.read_csv(file_path)
    except Exception as exc:
        return [
            f"{file_path.name}: could not be read: {exc}"
        ]

    if df.empty:
        errors.append(
            f"{file_path.name}: file contains no data rows"
        )

    duplicate_columns = (
        df.columns[
            df.columns.duplicated()
        ].tolist()
    )

    if duplicate_columns:
        errors.append(
            f"{file_path.name}: duplicate columns found: "
            f"{duplicate_columns}"
        )

    actual_columns = list(df.columns)

    if actual_columns != expected_columns:
        missing = [
            col
            for col in expected_columns
            if col not in actual_columns
        ]

        unexpected = [
            col
            for col in actual_columns
            if col not in expected_columns
        ]

        if missing:
            errors.append(
                f"{file_path.name}: missing columns: {missing}"
            )

        if unexpected:
            errors.append(
                f"{file_path.name}: unexpected columns: {unexpected}"
            )

        if not missing and not unexpected:
            errors.append(
                f"{file_path.name}: columns are in the wrong order"
            )

    if not errors:
        logger.info(
            "PASS | %s | %s rows x %s columns",
            file_path.name,
            f"{len(df):,}",
            len(df.columns),
        )

    return errors


def main():
    output_dir = Path(OUTPUT_DIR)

    print("=" * 80)
    print(" OLIST CSV OUTPUT VALIDATION")
    print("=" * 80)

    if not output_dir.exists():
        logger.error(
            "Output directory does not exist: %s",
            output_dir,
        )
        return 1

    expected_files = set(
        EXPECTED_CSVS.keys()
    )

    actual_files = {
        p.name
        for p in output_dir.glob("*.csv")
    }

    errors = []

    missing_files = (
        expected_files
        - actual_files
    )

    unexpected_files = (
        actual_files
        - expected_files
    )

    if missing_files:
        errors.append(
            "Missing expected CSV files: "
            + ", ".join(
                sorted(missing_files)
            )
        )

    if unexpected_files:
        errors.append(
            "Unexpected/stale CSV files found: "
            + ", ".join(
                sorted(unexpected_files)
            )
        )

    for filename, expected_columns in EXPECTED_CSVS.items():
        file_path = (
            output_dir
            / filename
        )

        if not file_path.exists():
            continue

        errors.extend(
            validate_csv(
                file_path,
                expected_columns,
            )
        )

    if errors:
        print()
        print("=" * 80)
        print(" CSV VALIDATION FAILED")
        print("=" * 80)

        for error in errors:
            logger.error(error)

        return 1

    print()
    print("=" * 80)
    print(" CSV VALIDATION PASSED")
    print("=" * 80)
    print(
        f"Validated {len(EXPECTED_CSVS)} CSV files successfully."
    )
    print(
        f"Output directory: {output_dir}"
    )

    return 0


if __name__ == "__main__":
    sys.exit(
        main()
    )
