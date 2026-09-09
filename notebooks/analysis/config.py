# config.py
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# GCP Configuration (OAuth)
PROJECT_ID = os.getenv("PROJECT_ID")
DATASET = os.getenv("DATASET")

# Validate required environment variables
if not PROJECT_ID:
    raise ValueError("PROJECT_ID not set in .env file")
if not DATASET:
    raise ValueError("DATASET not set in .env file")

# DuckDB Configuration
DUCKDB_MEMORY_LIMIT = os.getenv("DUCKDB_MEMORY_LIMIT", "4GB")
DUCKDB_THREADS = int(os.getenv("DUCKDB_THREADS", "4"))

# Pandas Display Options
PD_MAX_ROWS = int(os.getenv("PD_MAX_ROWS", "100"))
PD_MAX_COLUMNS = int(os.getenv("PD_MAX_COLUMNS", "20"))

# Print configuration on import (optional)
print(f"✅ Configuration loaded:")
print(f"   📊 Project: {PROJECT_ID}")
print(f"   📁 Dataset: {DATASET}")
print(f"   🦆 DuckDB Memory: {DUCKDB_MEMORY_LIMIT}")
print(f"   🧵 DuckDB Threads: {DUCKDB_THREADS}")