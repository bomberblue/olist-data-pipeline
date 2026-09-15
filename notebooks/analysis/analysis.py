# analysis.py
"""
fails with exit code 1 if the BigQuery connection or table validation fails
fails if any required analysis fails or returns no rows
stages all CSVs first
publishes the output directory only after every analysis and export succeeds
preserves/restores the previous successful output if publication fails
returns exit code 0 only on a fully successful run
"""

"""
Run the Olist analytical queries and publish the resulting CSV files safely.

Reliability behaviour:
- BigQuery connection/table validation failures are fatal.
- Any required analysis failure is fatal.
- Empty/None required results are treated as failures.
- Results are first written to a staging directory.
- OUTPUT_DIR is replaced only after every analysis and every CSV export succeeds.
- The process returns exit status 1 on failure and 0 on success.

Current analytical scope:
1. Monthly Sales Trend by Region
2. RFM - Top Customers
3. RFM - Segment Summary
4. Holiday Impact
5. Holiday Impact by Quarter
6. Holiday Daily Metrics by Quarter
7. Holiday Product Category Mix
"""

import logging
import os
import shutil
import sys
import tempfile
import time
import uuid
from pathlib import Path

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
    format=(
        "%(asctime)s | %(levelname)s | "
        "%(name)s | %(message)s"
    ),
)

logger = logging.getLogger(__name__)


pd.set_option("display.max_rows", PD_MAX_ROWS)
pd.set_option("display.max_columns", PD_MAX_COLUMNS)
pd.set_option("display.width", 160)
pd.set_option("display.float_format", "{:,.2f}".format)


ANALYSES = [
    (
        "monthly_sales_trend",
        "1. Monthly Sales Trend by Region",
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
        "4. Holiday Impact",
        holiday_impact,
    ),
    (
        "holiday_impact_by_quarter",
        "5. Holiday Impact by Quarter",
        holiday_impact_by_quarter,
    ),
    (
        "holiday_daily_metrics_by_quarter",
        "6. Holiday Daily Metrics by Quarter",
        holiday_daily_metrics_by_quarter,
    ),
    (
        "holiday_product_category_mix",
        "7. Holiday Product Category Mix",
        holiday_product_category_mix,
    ),
]

EXPECTED_EXPORTS = tuple(
    name
    for name, _, _ in ANALYSES
)


def print_section(title):
    """Print a readable console section heading."""

    print()
    print("=" * 80)
    print(f" {title}")
    print("=" * 80)


def validate_environment():
    """
    Validate the BigQuery connection and required mart tables.

    Any exception is intentionally allowed to propagate to main().
    """

    logger.info("Testing BigQuery connection...")
    test_connection(engine)

    logger.info("Verifying required mart tables...")
    verify_required_tables(engine)

    logger.info(
        "BigQuery connection and mart-table validation succeeded."
    )


def run_analysis():
    """
    Run every required analysis.

    Any required analysis failure is fatal.
    """

    results = {}

    for name, title, func in ANALYSES:
        print_section(title)

        logger.info(
            "Starting required analysis: %s",
            name,
        )

        try:
            df = func()
        except Exception as exc:
            logger.exception(
                "Required analysis failed: %s",
                name,
            )
            raise RuntimeError(
                f"Required analysis failed: {name}"
            ) from exc

        if df is None:
            raise RuntimeError(
                f"Required analysis returned None: {name}"
            )

        if not isinstance(df, pd.DataFrame):
            raise RuntimeError(
                f"Required analysis did not return a DataFrame: {name}"
            )

        if df.empty:
            raise RuntimeError(
                f"Required analysis returned no rows: {name}"
            )

        results[name] = df

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

        logger.info(
            "Completed analysis: %s (%s rows)",
            name,
            f"{len(df):,}",
        )

    missing_results = (
        set(EXPECTED_EXPORTS)
        - set(results)
    )

    if missing_results:
        raise RuntimeError(
            "Required analysis results are missing: "
            + ", ".join(
                sorted(missing_results)
            )
        )

    return results


def stage_results(results):
    """
    Write all CSV files to a temporary staging directory.

    Nothing is published to OUTPUT_DIR until every export succeeds.
    """

    output_dir = Path(OUTPUT_DIR)
    output_parent = output_dir.parent

    output_parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    staging_dir = Path(
        tempfile.mkdtemp(
            prefix=f".{output_dir.name}_staging_",
            dir=str(output_parent),
        )
    )

    logger.info(
        "Created staging directory: %s",
        staging_dir,
    )

    try:
        for name in EXPECTED_EXPORTS:
            if name not in results:
                raise RuntimeError(
                    f"Cannot export missing result: {name}"
                )

            df = results[name]

            if df is None or df.empty:
                raise RuntimeError(
                    f"Cannot export empty result: {name}"
                )

            staged_file = (
                staging_dir
                / f"{name}.csv"
            )

            df.to_csv(
                staged_file,
                index=False,
            )

            if (
                not staged_file.exists()
                or staged_file.stat().st_size == 0
            ):
                raise RuntimeError(
                    f"Staged CSV was not created correctly: {name}"
                )

            check_df = pd.read_csv(
                staged_file,
                nrows=1,
            )

            if list(check_df.columns) != list(df.columns):
                raise RuntimeError(
                    f"Staged CSV column validation failed: {name}"
                )

            logger.info(
                "Staged CSV: %s",
                staged_file,
            )

        staged_csvs = {
            p.name
            for p in staging_dir.glob("*.csv")
        }

        expected_csvs = {
            f"{name}.csv"
            for name in EXPECTED_EXPORTS
        }

        if staged_csvs != expected_csvs:
            raise RuntimeError(
                "Staged output set does not match the expected output set."
            )

        return staging_dir

    except Exception:
        shutil.rmtree(
            staging_dir,
            ignore_errors=True,
        )
        raise


def publish_results(staging_dir):
    """
    Publish the complete staged output set using a directory swap.

    The previous successful OUTPUT_DIR is kept until the new result set
    is complete. If publishing fails, the previous output is restored.

    OUTPUT_DIR should be dedicated to generated analysis artifacts.
    """

    output_dir = Path(OUTPUT_DIR)
    output_parent = output_dir.parent

    backup_dir = (
        output_parent
        / (
            f".{output_dir.name}_backup_"
            f"{uuid.uuid4().hex}"
        )
    )

    old_output_moved = False
    new_output_published = False

    try:
        if output_dir.exists():
            os.replace(
                output_dir,
                backup_dir,
            )
            old_output_moved = True

        os.replace(
            staging_dir,
            output_dir,
        )
        new_output_published = True

        logger.info(
            "Published complete analysis output set: %s",
            output_dir,
        )

    except Exception:
        logger.exception(
            "Failed to publish analysis outputs."
        )

        if (
            new_output_published
            and output_dir.exists()
        ):
            shutil.rmtree(
                output_dir,
                ignore_errors=True,
            )

        if (
            old_output_moved
            and backup_dir.exists()
        ):
            os.replace(
                backup_dir,
                output_dir,
            )

            logger.info(
                "Restored previous successful output directory."
            )

        raise

    else:
        if backup_dir.exists():
            shutil.rmtree(
                backup_dir,
                ignore_errors=True,
            )


def main():
    """
    Run validation, analyses, staging, and publication.

    Returns 0 on success and 1 on failure.
    """

    start_time = time.time()
    staging_dir = None

    print("=" * 80)
    print(" OLIST ANALYSIS")
    print(" BigQuery + SQLAlchemy + Pandas")
    print("=" * 80)

    try:
        validate_environment()

        results = run_analysis()

        staging_dir = stage_results(
            results
        )

        publish_results(
            staging_dir
        )

        # staging_dir has been renamed to OUTPUT_DIR.
        staging_dir = None

    except Exception as exc:
        if (
            staging_dir is not None
            and staging_dir.exists()
        ):
            shutil.rmtree(
                staging_dir,
                ignore_errors=True,
            )

        elapsed = (
            time.time()
            - start_time
        )

        logger.exception(
            "Analysis pipeline failed."
        )

        print()
        print("=" * 80)
        print(" ANALYSIS FAILED")
        print("=" * 80)
        print(f"Reason: {exc}")
        print(
            f"Elapsed time: "
            f"{elapsed:.2f} seconds"
        )

        return 1

    elapsed = (
        time.time()
        - start_time
    )

    print()
    print("=" * 80)
    print(" ANALYSIS COMPLETED SUCCESSFULLY")
    print("=" * 80)

    print(
        f"Elapsed time: "
        f"{elapsed:.2f} seconds"
    )

    print(
        f"Published output directory: "
        f"{OUTPUT_DIR}"
    )

    return 0


if __name__ == "__main__":
    sys.exit(
        main()
    )
