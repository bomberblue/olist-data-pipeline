# engine.py
from sqlalchemy import create_engine, text
from config import PROJECT_ID, DATASET
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_engine():
    """
    Create SQLAlchemy BigQuery engine using OAuth.
    Uses gcloud CLI credentials from `gcloud auth application-default login`.
    """
    logger.info(f"🔐 Creating BigQuery engine: {PROJECT_ID}/{DATASET}")
    engine = create_engine(f'bigquery://{PROJECT_ID}/{DATASET}')
    return engine

def test_connection():
    """Test BigQuery connection using OAuth."""
    engine = get_engine()
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1")).fetchone()
        logger.info(f"✅ Connected! Result: {result[0]}")
    return engine

# Create global engine
engine = get_engine()
logger.info("✅ Engine ready!")