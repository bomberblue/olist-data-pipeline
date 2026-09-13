# engine.py

import logging

from sqlalchemy import create_engine, text

from config import PROJECT_ID, DATASET, BQ_LOCATION, MART_TABLES


logger = logging.getLogger(__name__)


class BigQueryConnectionError(Exception):
    """Raised when BigQuery connection or table access fails."""
    pass


def get_engine():
    """Create the SQLAlchemy BigQuery engine."""
    try:
        kwargs = {}

        if BQ_LOCATION:
            kwargs["location"] = BQ_LOCATION

        return create_engine(
            f"bigquery://{PROJECT_ID}/{DATASET}",
            **kwargs,
        )

    except Exception as e:
        raise BigQueryConnectionError(
            f"Failed to create BigQuery engine: {e}"
        ) from e


def test_connection(engine):
    """Verify that BigQuery can execute a simple query."""
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1")).scalar()

        if result != 1:
            raise BigQueryConnectionError(
                "BigQuery connection test returned an unexpected result"
            )

        logger.info("BigQuery connection OK")
        return True

    except BigQueryConnectionError:
        raise

    except Exception as e:
        raise BigQueryConnectionError(
            f"BigQuery connection failed: {e}"
        ) from e


def verify_required_tables(engine, required_tables=MART_TABLES):
    """
    Verify expected mart tables using INFORMATION_SCHEMA metadata.
    """
    try:
        sql = f"""
            SELECT table_name
            FROM `{PROJECT_ID}.{DATASET}.INFORMATION_SCHEMA.TABLES`
        """

        with engine.connect() as conn:
            rows = conn.execute(text(sql)).fetchall()

        existing = {row[0] for row in rows}

        missing = [
            table
            for table in required_tables
            if table not in existing
        ]

        if missing:
            raise BigQueryConnectionError(
                "Missing required BigQuery tables: "
                + ", ".join(missing)
            )

        logger.info(
            "All %d required BigQuery tables are available",
            len(required_tables),
        )

        return True

    except BigQueryConnectionError:
        raise

    except Exception as e:
        raise BigQueryConnectionError(
            f"Failed to verify BigQuery tables: {e}"
        ) from e


engine = get_engine()
