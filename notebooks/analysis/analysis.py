# analysis.py
"""
Simplified analysis runner for Olist star schema.
Loads and previews all dimension and fact tables.
"""

import pandas as pd
import time
import logging
from config import PD_MAX_ROWS, PD_MAX_COLUMNS
from engine import test_connection
from duckdb_engine import duck
from queries import *

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set pandas display options
pd.set_option('display.max_rows', PD_MAX_ROWS)
pd.set_option('display.max_columns', PD_MAX_COLUMNS)
pd.set_option('display.width', 120)
pd.set_option('display.float_format', '{:,.2f}'.format)


def print_section(title):
    """Print a formatted section header."""
    print("\n" + "=" * 80)
    print(f"📊 {title}")
    print("=" * 80)


def print_table_preview(df, table_name, limit=5):
    """Print a formatted table preview."""
    if df.empty:
        print(f"   ⚠️ {table_name} is empty")
        return
    
    print(f"\n   📋 First {limit} rows from {table_name}:")
    print("-" * 60)
    print(df.to_string(index=False))
    print(f"\n   📊 Shape: {df.shape[0]} rows × {df.shape[1]} columns")
    print(f"   📋 Columns: {', '.join(df.columns.tolist())}")


def run_analysis():
    """Load and preview all tables."""
    
    start_time = time.time()
    
    print("=" * 80)
    print("📊 OLIST STAR SCHEMA - TABLE PREVIEW")
    print("🔐 Using OAuth Authentication")
    print("=" * 80)
    
    # Test connection
    print("\n🔌 Testing BigQuery Connection with OAuth...")
    try:
        test_connection()
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print("   Make sure you've run: gcloud auth application-default login")
        return
    
    # =====================================================
    # DIMENSION TABLES
    # =====================================================
    print_section("DIMENSION TABLES")
    
    dimensions = [
        ("dim_customer", get_dim_customer),
        ("dim_product", get_dim_product),
        ("dim_seller", get_dim_seller),
        ("dim_date", get_dim_date),
        ("dim_geolocation", get_dim_geolocation)
    ]
    
    for name, func in dimensions:
        print(f"\n📋 TABLE: {name.upper()}")
        print("-" * 60)
        try:
            df = func(limit=5)
            print_table_preview(df, name, limit=5)
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    # =====================================================
    # FACT TABLES
    # =====================================================
    print_section("FACT TABLES")
    
    facts = [
        ("fact_orders", get_fact_orders),
        ("fact_order_items", get_fact_order_items),
        ("fact_reviews", get_fact_reviews),
        ("fact_payments", get_fact_payments)
    ]
    
    for name, func in facts:
        print(f"\n📋 TABLE: {name.upper()}")
        print("-" * 60)
        try:
            df = func(limit=5)
            print_table_preview(df, name, limit=5)
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    # =====================================================
    # ROW COUNTS SUMMARY
    # =====================================================
    print_section("ROW COUNTS SUMMARY")
    
    try:
        counts = get_table_row_counts()
        print("\n   📊 Table row counts:")
        print("-" * 50)
        for table, count in counts.items():
            print(f"      📊 {table:<25} {count:>10,}")
    except Exception as e:
        print(f"   ❌ Error getting row counts: {e}")
    
    elapsed = time.time() - start_time
    print("\n" + "=" * 80)
    print(f"✅ Analysis Complete! Time: {elapsed:.2f} seconds")
    print("=" * 80)


def export_results():
    """Export all table previews to CSV files."""
    print("\n📁 Exporting table previews to CSV...")
    
    import os
    os.makedirs("output", exist_ok=True)
    
    tables = {
        'dim_customer': get_dim_customer,
        'dim_product': get_dim_product,
        'dim_seller': get_dim_seller,
        'dim_date': get_dim_date,
        'dim_geolocation': get_dim_geolocation,
        'fact_orders': get_fact_orders,
        'fact_order_items': get_fact_order_items,
        'fact_reviews': get_fact_reviews,
        'fact_payments': get_fact_payments
    }
    
    for name, func in tables.items():
        try:
            df = func(limit=100)  # Export 100 rows for preview
            if df is not None and not df.empty:
                filename = f"output/{name}_preview.csv"
                df.to_csv(filename, index=False)
                print(f"  ✅ Saved: {filename}")
            else:
                print(f"  ⚠️ No data for: {name}")
        except Exception as e:
            print(f"  ❌ Error exporting {name}: {e}")
    
    # Export row counts
    try:
        counts = get_table_row_counts()
        counts_df = pd.DataFrame(list(counts.items()), columns=['table', 'row_count'])
        counts_df.to_csv("output/table_row_counts.csv", index=False)
        print(f"  ✅ Saved: output/table_row_counts.csv")
    except Exception as e:
        print(f"  ❌ Error exporting row counts: {e}")


if __name__ == "__main__":
    # Run analysis
    run_analysis()
    
    # Export results
    export_results()