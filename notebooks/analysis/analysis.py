# analysis.py

"""
Focused Olist analysis runner.

The shared warehouse keeps the full available history.
Holiday-specific analyses are restricted to Jan 2017 through Jun 2018
because holiday classification is available only for that period.
"""

import logging
import time

import pandas as pd

from config import (
    PD_MAX_ROWS,
    PD_MAX_COLUMNS,
    OUTPUT_DIR,
)
from engine import (
    engine,
    test_connection,
    verify_required_tables,
)

from queries import (
    monthly_sales_trend,
    rfm_analysis,
    rfm_segment_summary,
    holiday_impact,
    holiday_impact_by_quarter,
    holiday_daily_metrics_by_quarter,
    holiday_product_category_mix,
)


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

logger = logging.getLogger(__name__)


pd.set_option("display.max_rows", PD_MAX_ROWS)
pd.set_option("display.max_columns", PD_MAX_COLUMNS)
pd.set_option("display.width", 160)
pd.set_option("display.float_format", "{:,.2f}".format)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


ANALYSES = [
    (
        "monthly_sales_trend",
        "1. Monthly Sales Trend",
        monthly_sales_trend,
    ),
    (
        "rfm_analysis",
        "2. RFM - Top Customers",
        rfm_analysis,
    ),
    (
        "rfm_segment_summary",
        "3. RFM - Segment Summary",
        rfm_segment_summary,
    ),
    (
        "holiday_impact",
        "4. Holiday Impact - Jan 2017 to Jun 2018",
        holiday_impact,
    ),
    (
        "holiday_impact_by_quarter",
        "5. Holiday Impact by Quarter",
        holiday_impact_by_quarter,
    ),
    (
        "holiday_daily_metrics_by_quarter",
        "6. Holiday Average Orders / GMV per Day",
        holiday_daily_metrics_by_quarter,
    ),
    (
        "holiday_product_category_mix",
        "7. Holiday vs Non-Holiday Product Category Mix",
        holiday_product_category_mix,
    ),
]


def print_section(title):
    print("\n" + "=" * 80)
    print(f" {title}")
    print("=" * 80)


def run_analysis():
    """Run each analysis once and return a dictionary of DataFrames."""

    start_time = time.time()

    print("=" * 80)
    print(" OLIST ANALYSIS")
    print(" BigQuery + SQLAlchemy + Pandas")
    print("=" * 80)

    print("\nTesting BigQuery connection and mart tables...")

    try:
        test_connection(engine)
        verify_required_tables(engine)

    except Exception as e:
        logger.exception(
            "BigQuery validation failed"
        )
        print(
            f"Validation failed: {e}"
        )
        return {}

    results = {}

    for name, title, func in ANALYSES:
        print_section(title)

        try:
            df = func()
            results[name] = df

            if df is None or df.empty:
                print(
                    "No data returned"
                )
                continue

            print(
                df.to_string(
                    index=False
                )
            )

            print(
                f"\nShape: "
                f"{df.shape[0]} rows × "
                f"{df.shape[1]} columns"
            )

        except Exception as e:
            logger.exception(
                "Error running %s",
                title,
            )
            print(
                f"Error: {e}"
            )

    elapsed = (
        time.time()
        - start_time
    )

    print(
        "\n" + "=" * 80
    )
    print(
        f" Analysis complete in "
        f"{elapsed:.2f} seconds"
    )
    print(
        "=" * 80
    )

    return results


def export_results(results):
    """Export already-computed results without rerunning the queries."""

    if not results:
        print(
            "\nNo results available to export."
        )
        return

    print(
        "\nExporting results to CSV..."
    )

    for name, df in results.items():

        if df is None or df.empty:
            print(
                f"   No data for: {name}"
            )
            continue

        filename = (
            OUTPUT_DIR
            / f"{name}.csv"
        )

        try:
            df.to_csv(
                filename,
                index=False,
            )

            print(
                f"   Saved: {filename}"
            )

        except Exception:
            logger.exception(
                "Error exporting %s",
                name,
            )


if __name__ == "__main__":
    results = run_analysis()
    export_results(results)
