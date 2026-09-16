# engine.py

import logging

import pandas as pd
from sqlalchemy import create_engine, text

from config import (
    PROJECT_ID,
    DATASET,
    MART_TABLES,
)


logger = logging.getLogger(__name__)


# ============================================================
# BIGQUERY ENGINE
# ============================================================

engine = create_engine(
    f"bigquery://{PROJECT_ID}/{DATASET}"
)


# ============================================================
# REQUIRED MART TABLES
# ============================================================

REQUIRED_TABLES = MART_TABLES


# ============================================================
# CONNECTION CHECK
# ============================================================

def test_connection(engine):
    """
    Verify that BigQuery can be reached.

    Raises
    ------
    RuntimeError
        If the connection test fails.
    """

    logger.info(
        "Testing BigQuery connection..."
    )

    try:
        with engine.connect() as connection:
            result = connection.execute(
                text("SELECT 1 AS connection_test")
            )

            value = result.scalar()

            if value != 1:
                raise RuntimeError(
                    "Unexpected response from BigQuery "
                    "connection test."
                )

    except Exception as exc:
        logger.exception(
            "BigQuery connection test failed."
        )

        raise RuntimeError(
            "Unable to connect to BigQuery."
        ) from exc

    logger.info(
        "BigQuery connection successful."
    )

    return True


# ============================================================
# REQUIRED TABLE VALIDATION
# ============================================================

def verify_required_tables(engine):
    """
    Verify that all required mart tables exist and can be accessed.

    Validation is performed in two stages:

    1. Check table existence using INFORMATION_SCHEMA.
    2. Execute a lightweight SELECT against every required table
       to confirm that the table is accessible.

    Raises
    ------
    RuntimeError
        If any required table is missing or inaccessible.
    """

    logger.info(
        "Verifying required BigQuery mart tables..."
    )

    # --------------------------------------------------------
    # 1. Check table existence
    # --------------------------------------------------------

    schema_sql = f"""
        SELECT
            table_name

        FROM
            `{PROJECT_ID}.{DATASET}.INFORMATION_SCHEMA.TABLES`

        WHERE
            table_type = 'BASE TABLE'
    """

    try:
        available_df = pd.read_sql(
            text(schema_sql),
            con=engine,
        )

    except Exception as exc:
        logger.exception(
            "Failed to read BigQuery INFORMATION_SCHEMA."
        )

        raise RuntimeError(
            "Unable to verify required BigQuery tables."
        ) from exc

    available_tables = set(
        available_df["table_name"]
        .dropna()
        .astype(str)
    )

    missing_tables = [
        table_name
        for table_name in REQUIRED_TABLES
        if table_name not in available_tables
    ]

    if missing_tables:
        logger.error(
            "Missing required tables: %s",
            ", ".join(missing_tables),
        )

        raise RuntimeError(
            "Required BigQuery tables are missing: "
            + ", ".join(missing_tables)
        )

    # --------------------------------------------------------
    # 2. Confirm that every required table is accessible
    # --------------------------------------------------------

    access_failures = []

    for table_name in REQUIRED_TABLES:

        sql = f"""
            SELECT
                1 AS access_test

            FROM
                `{PROJECT_ID}.{DATASET}.{table_name}`

            LIMIT 1
        """

        try:
            pd.read_sql(
                text(sql),
                con=engine,
            )

            logger.info(
                "Table accessible: %s",
                table_name,
            )

        except Exception as exc:

            logger.exception(
                "Unable to access required table: %s",
                table_name,
            )

            access_failures.append(
                (
                    table_name,
                    str(exc),
                )
            )

    # --------------------------------------------------------
    # 3. Fail the complete validation if any table failed
    # --------------------------------------------------------

    if access_failures:

        failed_names = [
            table_name
            for table_name, _ in access_failures
        ]

        raise RuntimeError(
            "Required BigQuery tables could not be accessed: "
            + ", ".join(failed_names)
        )

    logger.info(
        "All %s required mart tables are available "
        "and accessible.",
        len(REQUIRED_TABLES),
    )

    return True