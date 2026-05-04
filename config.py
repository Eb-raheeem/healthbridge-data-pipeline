import os
from dotenv import load_dotenv

load_dotenv()

# --- Database ---
DB_CONFIG = {
    "user":     os.getenv("user"),
    "password": os.getenv("password"),
    "host":     os.getenv("host"),
    "port":     os.getenv("port"),
    "dbname":   os.getenv("dbname"),
}

DATABASE_URL = (
    f"postgresql+psycopg2://{DB_CONFIG['user']}:{DB_CONFIG['password']}"
    f"@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['dbname']}?sslmode=require"
)

# --- AWS ---
AWS_CONFIG = {
    "access_key_id":     os.getenv("ACCESS_KEY"),
    "secret_access_key": os.getenv("SECRET_KEY"),
    "bucket_name":       os.getenv("BUCKET_NAME"),
    "region":            os.getenv("REGION"),
}

# --- Tables to extract ---
# — schema and table name
TABLES = [
    ("prod", "centers"),
    ("prod", "appointments"),
    ("prod", "payments"),
    ("prod", "patients"),
    ("prod", "tests"),
    ("prod", "test_results")
]

# --- S3 paths ---
S3_LANDING_FOLDER = "landing"      # raw CSVs go here
S3_PROCESSED_FOLDER = "processed"  # Parquet files go here
