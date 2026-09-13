# duckdb_engine.py

"""
Optional DuckDB utility.

DuckDB is not used by the normal analysis workflow.
No BigQuery data is loaded during module import.
"""

import logging
import re

import duckdb
import pandas as pd

from config import (
    PROJECT_ID,
    DATASET,
    DUCKDB_MEMORY_LIMIT,
    DUCKDB_THREADS,
    MART_TABLES,
)
from engine import engine


logger = logging.getLogger(__name__)
_COLUMN_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _validate_table(table):
    if table not in MART_TABLES:
        raise ValueError(
            f"Invalid table '{table}'. "
            f"Allowed tables: {', '.join(MART_TABLES)}"
        )


def _validate_columns(columns):
    if columns is None:
        return

    for column in columns:
        if not _COLUMN_PATTERN.fullmatch(column):
            raise ValueError(f"Invalid column name: {column}")


def get_duckdb():
    """Create an empty in-memory DuckDB connection."""
    duck = duckdb.connect(database=":memory:")
    duck.execute(f"SET memory_limit = '{DUCKDB_MEMORY_LIMIT}'")
    duck.execute(f"SET threads = {int(DUCKDB_THREADS)}")
    return duck


def load_table_to_duckdb(
    duck,
    table,
    columns=None,
    limit=None,
):
    """
    Explicitly copy a selected BigQuery table into DuckDB.
    """
    _validate_table(table)
    _validate_columns(columns)

    if columns:
        column_sql = ", ".join(
            f"`{column}`"
            for column in columns
        )
    else:
        column_sql = "*"

    limit_sql = ""

    if limit is not None:
        limit = int(limit)

        if limit <= 0:
            raise ValueError("limit must be greater than 0")

        limit_sql = f"LIMIT {limit}"

    query = f"""
        SELECT {column_sql}
        FROM `{PROJECT_ID}.{DATASET}.{table}`
        {limit_sql}
    """

    df = pd.read_sql(query, con=engine)
    temp_name = "_duckdb_temp_df"

    try:
        duck.register(temp_name, df)

        duck.execute(
            f"""
            CREATE OR REPLACE TABLE "{table}" AS
            SELECT *
            FROM {temp_name}
            """
        )

    finally:
        try:
            duck.unregister(temp_name)
        except Exception:
            pass

    logger.info(
        "Loaded %s into DuckDB: %,d rows",
        table,
        len(df),
    )

    return len(df)
