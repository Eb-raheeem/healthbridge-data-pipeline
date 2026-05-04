import sys  # noqa: E402
import os  # noqa: E402
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # noqa: E402

import pandas as pd
from sqlalchemy import create_engine, text
from config import DATABASE_URL


def get_engine():
    """Create a SQLAlchemy engine."""
    try:
        engine = create_engine(DATABASE_URL)
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))  # Test the connection
# print("Successfully connected to the database.")
        return engine
    except Exception as e:
        print(f"Error creating engine: {e}")
        raise


# extract data from the database

def extract_table(engine, schema, table):
    """Extract data from the specified schema and table."""
    try:
        query = f"SELECT * FROM {schema}.{table}"
        print(f"Extracting {schema}.{table}...")
        df = pd.read_sql(query, engine)
        print(f"Successfully extracted data from {schema}.{table}.")
        return df
    except Exception as e:
        print(f"Error extracting data: {e}")
        raise
