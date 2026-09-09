# test_connection.py
import pandas as pd
from sqlalchemy import text
from engine import test_connection
from duckdb_engine import duck
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_all():
    """Test connections and query dim_date."""
    
    print("=" * 70)
    print("🔐 Testing OAuth Connections to BigQuery")
    print("=" * 70)
    
    # 1. Test SQLAlchemy (OAuth)
    print("\n1️⃣ Testing SQLAlchemy BigQuery connection with OAuth...")
    try:
        engine = test_connection()
        print("   ✅ SQLAlchemy with OAuth successful!")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        print("   Make sure you've run: gcloud auth application-default login")
        return
    
    # 2. Test DuckDB and list loaded tables
    print("\n2️⃣ Testing DuckDB connection...")
    try:
        # Get list of tables
        tables_df = duck.execute("SHOW TABLES").df()
        tables_list = tables_df['name'].tolist() if not tables_df.empty else []
        
        print(f"   ✅ DuckDB connected! {len(tables_list)} tables available")
        
        if tables_list:
            print("\n   📋 Available tables:")
            for table in tables_list:
                try:
                    count = duck.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                    print(f"      📊 {table:<25} {count:>8,} rows")
                except Exception as e:
                    print(f"      📊 {table:<25} {'N/A':>8} rows")
        else:
            print("   ⚠️ No tables loaded yet.")
            print("   💡 Run: python quick_start.py first to load data")
            return
    except Exception as e:
        print(f"   ❌ DuckDB error: {e}")
        return
    
    # 3. Query dim_date (if it exists)
    print("\n3️⃣ Querying dim_date (LIMIT 5)...")
    try:
        if 'dim_date' in tables_list:
            result = duck.execute("SELECT * FROM dim_date LIMIT 5").df()
            print(f"   ✅ Query successful! {len(result)} rows returned")
            print("\n   📋 dim_date sample data:")
            print(result.to_string(index=False))
        else:
            print("   ⚠️ dim_date not loaded yet.")
            print("   💡 Run: python quick_start.py first to load data")
    except Exception as e:
        print(f"   ❌ Error querying dim_date: {e}")
    
    print("\n" + "=" * 70)
    print("✅ Connection tests complete!")
    print("=" * 70)


if __name__ == "__main__":
    test_all()
    
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# def test_all():
#     """Test all connections and list available tables."""
    
#     print("=" * 70)
#     print("🔐 Testing OAuth Connections to BigQuery")
#     print("=" * 70)
    
#     # 1. Test SQLAlchemy (OAuth)
#     print("\n1️⃣ Testing SQLAlchemy BigQuery connection with OAuth...")
#     try:
#         engine = test_connection()
#         print("   ✅ SQLAlchemy with OAuth successful!")
#     except Exception as e:
#         print(f"   ❌ Error: {e}")
#         print("   Make sure you've run: gcloud auth application-default login")
#         return
    
#     # 2. Test DuckDB
#     print("\n2️⃣ Testing DuckDB connection...")
#     try:
#         tables = duck.execute("SHOW TABLES").df()
#         print(f"   ✅ DuckDB connected! {len(tables)} tables available")
#     except Exception as e:
#         print(f"   ❌ DuckDB error: {e}")
#         return
    
#     # 3. List available tables
#     print("\n3️⃣ Available tables in DuckDB:")
#     print("   " + "-" * 40)
#     for idx, row in tables.iterrows():
#         try:
#             count = duck.execute(f"SELECT COUNT(*) FROM {row['name']}").fetchone()[0]
#             print(f"   📊 {row['name']:<25} {count:>8,} rows")
#         except:
#             print(f"   📊 {row['name']:<25} {'N/A':>8} rows")
    
#     # 4. Test sample queries
#     print("\n4️⃣ Testing sample queries...")
#     try:
#         result = duck.execute("""
#             SELECT 
#                 COUNT(*) AS total_orders,
#                 SUM(total_order_value) AS total_gmv
#             FROM fact_orders 
#             WHERE total_order_value > 0
#         """).fetchone()
#         print(f"   ✅ Sample query successful!")
#         print(f"      Total orders: {result[0]:,}")
#         print(f"      Total GMV: R$ {result[1]:,.2f}")
#     except Exception as e:
#         print(f"   ❌ Sample query error: {e}")
    
#     # 5. Show table schemas
#     print("\n5️⃣ Table schemas:")
#     sample_tables = ["dim_customer", "fact_orders"]
#     for table in sample_tables:
#         try:
#             df = duck.execute(f"SELECT * FROM {table} LIMIT 1").df()
#             print(f"   📋 {table}: {', '.join(df.columns.tolist())}")
#         except:
#             pass
    
#     print("\n" + "=" * 70)
#     print("✅ All OAuth connections working!")
#     print("=" * 70)

# if __name__ == "__main__":
#     test_all()