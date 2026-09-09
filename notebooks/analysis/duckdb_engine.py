# duckdb_engine.py
import duckdb
import pandas as pd
from config import PROJECT_ID, DATASET, DUCKDB_MEMORY_LIMIT, DUCKDB_THREADS
from engine import engine
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_duckdb():
    """
    Create DuckDB connection with all star schema tables.
    Loads data via pandas (which uses OAuth through SQLAlchemy).
    """
    duck = duckdb.connect()
    duck.execute(f"SET memory_limit = '{DUCKDB_MEMORY_LIMIT}'")
    duck.execute(f"SET threads = {DUCKDB_THREADS}")
    
    # All tables in the star schema
    tables = [
        "dim_customer", "dim_product", "dim_seller", "dim_date", "dim_geolocation",
        "fact_orders", "fact_order_items", "fact_reviews", "fact_payments"
    ]
    
    logger.info("📥 Loading star schema tables from BigQuery...")
    
    for table in tables:
        try:
            logger.info(f"   Loading {table}...")
            df = pd.read_sql(f"SELECT * FROM {table}", con=engine)
            duck.register(table, df)
            logger.info(f"   ✅ {table}: {len(df):,} rows")
        except Exception as e:
            logger.error(f"   ❌ Error loading {table}: {e}")
    
    # Show summary
    loaded_tables = duck.execute("SHOW TABLES").df()
    logger.info(f"✅ Loaded {len(loaded_tables)} tables into DuckDB!")
    
    return duck


# Create global DuckDB connection
duck = get_duckdb()
logger.info("✅ DuckDB connection ready!")