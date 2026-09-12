# queries.py
import pandas as pd
from duckdb_engine import duck
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# =====================================================
# DIMENSION TABLES
# =====================================================

def get_dim_customer(limit=5):
    """Get sample data from dim_customer."""
    logger.info("👤 Loading dim_customer...")
    return duck.execute(f"SELECT * FROM dim_customer LIMIT {limit}").df()


def get_dim_product(limit=5):
    """Get sample data from dim_product."""
    logger.info("🏷️ Loading dim_product...")
    return duck.execute(f"SELECT * FROM dim_product LIMIT {limit}").df()


def get_dim_seller(limit=5):
    """Get sample data from dim_seller."""
    logger.info("🏪 Loading dim_seller...")
    return duck.execute(f"SELECT * FROM dim_seller LIMIT {limit}").df()


def get_dim_date(limit=5):
    """Get sample data from dim_date."""
    logger.info("📅 Loading dim_date...")
    return duck.execute(f"SELECT * FROM dim_date LIMIT {limit}").df()


def get_dim_geolocation(limit=5):
    """Get sample data from dim_geolocation."""
    logger.info("🗺️ Loading dim_geolocation...")
    return duck.execute(f"SELECT * FROM dim_geolocation LIMIT {limit}").df()


# =====================================================
# FACT TABLES
# =====================================================

def get_fact_orders(limit=5):
    """Get sample data from fact_orders."""
    logger.info("📊 Loading fact_orders...")
    return duck.execute(f"SELECT * FROM fact_orders LIMIT {limit}").df()


def get_fact_order_items(limit=5):
    """Get sample data from fact_order_items."""
    logger.info("🛒 Loading fact_order_items...")
    return duck.execute(f"SELECT * FROM fact_order_items LIMIT {limit}").df()


def get_fact_reviews(limit=5):
    """Get sample data from fact_reviews."""
    logger.info("⭐ Loading fact_reviews...")
    return duck.execute(f"SELECT * FROM fact_reviews LIMIT {limit}").df()


def get_fact_payments(limit=5):
    """Get sample data from fact_payments."""
    logger.info("💳 Loading fact_payments...")
    return duck.execute(f"SELECT * FROM fact_payments LIMIT {limit}").df()


# =====================================================
# ALL TABLES (Combined)
# =====================================================

def get_all_tables(limit=5):
    """
    Get sample data from ALL tables.
    Returns a dictionary with table names as keys and DataFrames as values.
    """
    logger.info("📥 Loading ALL tables...")
    
    tables = {
        'dim_customer': get_dim_customer(limit),
        'dim_product': get_dim_product(limit),
        'dim_seller': get_dim_seller(limit),
        'dim_date': get_dim_date(limit),
        'dim_geolocation': get_dim_geolocation(limit),
        'fact_orders': get_fact_orders(limit),
        'fact_order_items': get_fact_order_items(limit),
        'fact_reviews': get_fact_reviews(limit),
        'fact_payments': get_fact_payments(limit)
    }
    
    return tables


def get_table_row_counts():
    """Get row counts for all tables."""
    logger.info("📊 Getting row counts for all tables...")
    
    tables = [
        "dim_customer", "dim_product", "dim_seller", "dim_date", "dim_geolocation",
        "fact_orders", "fact_order_items", "fact_reviews", "fact_payments"
    ]
    
    counts = {}
    for table in tables:
        try:
            count = duck.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            counts[table] = count
        except Exception as e:
            counts[table] = f"Error: {e}"
    
    return counts