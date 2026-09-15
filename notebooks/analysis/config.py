# config.py

import os
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


def _required_env(name):
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


PROJECT_ID = _required_env("PROJECT_ID")
DATASET = _required_env("DATASET")

BQ_LOCATION = os.getenv("BQ_LOCATION") or None

DUCKDB_MEMORY_LIMIT = os.getenv("DUCKDB_MEMORY_LIMIT", "2GB")
DUCKDB_THREADS = int(os.getenv("DUCKDB_THREADS", "4"))

PD_MAX_ROWS = int(os.getenv("PD_MAX_ROWS", "100"))
PD_MAX_COLUMNS = int(os.getenv("PD_MAX_COLUMNS", "30"))

RFM_TOP_CUSTOMERS_LIMIT = int(os.getenv("RFM_TOP_CUSTOMERS_LIMIT", "100"))

OUTPUT_DIR = BASE_DIR / os.getenv("OUTPUT_DIR", "output")


MART_TABLES = (
    "dim_customer",
    "dim_date",
    "dim_geolocation",
    "dim_product",
    "dim_seller",
    "fact_order_items",
    "fact_orders",
    "fact_payments",
    "fact_reviews",
    "fct_customer_rfm",
)