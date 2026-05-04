import sys  # noqa: E402
import os  # noqa: E402
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # noqa: E402

from config import AWS_CONFIG, S3_PROCESSED_FOLDER, S3_LANDING_FOLDER, TABLES
import awswrangler as wr
import boto3
import pandas as pd
import re


# --- Transform maps ---

DATETIME_COLUMNS = {
    "centers":      ["created_at"],
    "appointments": ["appointment_date"],
    "payments":     ["payment_date"],
    "patients":     ["created_at"],
    "test_results": ["test_date", "created_at"]
}

DATE_COLUMNS = {
    "patients": ["date_of_birth"],
}

CAPITALIZE_COLUMNS = {
    "centers":      ["state"],
    "appointments": ["status"],
    "payments":     ["payment_method", "payment_status"],
    "patients":     ["first_name", "last_name", "gender"],
    "test_results": ["result_status"],
    "tests":        ["test_name", "category"],
}

# Tables to partition and which date column drives the partition
PARTITION_CONFIG = {
    "appointments": "appointment_date",
    "payments":     "payment_date",
    "test_results": "test_date",
}

# s3 session


def s3_session():
    session = boto3.Session(
        aws_access_key_id=AWS_CONFIG["access_key_id"],
        aws_secret_access_key=AWS_CONFIG["secret_access_key"],
        region_name=AWS_CONFIG["region"]
    )
    return session

# transformation functions


def fix_duplicates(df, table_name):
    """Remove duplicate rows."""
    before = len(df)
    df = df.drop_duplicates()
    after = len(df)

    if before != after:
        print(f"  Removed {before - after} duplicate rows")
    else:
        print(f"  No duplicates found")
    return df


def read_from_landing(table_name):
    """Read a CSV file from S3 into a DataFrame."""
    session = s3_session()
    s3_path = f"s3://{AWS_CONFIG['bucket_name']}/{S3_LANDING_FOLDER}/{table_name}"
    df = wr.s3.read_csv(path=s3_path, boto3_session=session)
    return df


def fix_datetime(df, table_name):
    """Convert specified columns to datetime format and add a date column."""
    """ For each column in DATETIME_COLUMNS:
    - Parse the column as datetime (assuming UTC)
    - Rename original column to *_datetime
    - Create a new *_date column with just the date part
    """

    for col in DATETIME_COLUMNS.get(table_name, []):
        if col not in df.columns:
            continue

        base = col.replace("_at", "").replace("_date", "")

        datetime_col = f"{base}_datetime"
        date_col = f"{base}_date"

        parsed = pd.to_datetime(df[col], utc=True)

        df = df.drop(columns=[col])
        df[datetime_col] = parsed
        df[date_col] = parsed.dt.date

        print(f"{col} → {datetime_col}, {date_col}")

    return df


def fix_date(df, table_name):
    """Convert specified columns to date format."""
    for col in DATE_COLUMNS.get(table_name, []):
        if col in df.columns:
            df[col] = pd.to_datetime(df[col]).dt.date
            print(f"  {col} → converted to date")
    return df


def fix_capitalize_columns(df, table_name):
    """Capitalize specified columns."""
    for col in CAPITALIZE_COLUMNS.get(table_name, []):
        if col in df.columns:
            df[col] = df[col].str.title()
            print(f"  {col} → capitalized")
    return df


def clean_phone(phone):
    """Standardize a single phone number to XXX-XXX-XXXX and extract extension."""
    if pd.isna(phone):
        return None, None

    phone = str(phone)

    # Extract extension if present
    ext_match = re.search(r'x(\d+)', phone, re.IGNORECASE)
    extension = ext_match.group(1) if ext_match else None

    # Strip everything except digits from the core number
    digits = re.sub(r'\D', '', phone.split('x')[0].split('X')[0])

    # Drop country code
    if len(digits) in (11, 13) and (digits.startswith('1') or digits.startswith('001')):
        digits = digits.lstrip('0').lstrip('1')

    # Format as XXX-XXX-XXXX
    if len(digits) == 10:
        return f"{digits[:3]}-{digits[3:6]}-{digits[6:]}", extension
    return None, extension


def fix_phone(df):
    """Standardize phone numbers and extract extensions."""
    if 'phone' in df.columns:
        df[['phone', 'phone_ext']] = df['phone'].apply(
            lambda x: pd.Series(clean_phone(x)))
        print("  phone → standardized + phone_ext extracted")
    return df


def write_to_s3processed(df, table_name):
    """Write the transformed DataFrame back to S3 in Parquet format."""
    session = s3_session()
    s3_path = f"s3://{AWS_CONFIG['bucket_name']}/{S3_PROCESSED_FOLDER}/{table_name}"

    if table_name in PARTITION_CONFIG:
        date_col = PARTITION_CONFIG[table_name]

        # Add year and month partition
        df["year"] = pd.to_datetime(df[date_col]).dt.year
        df["month"] = pd.to_datetime(df[date_col]).dt.month

        wr.s3.to_parquet(
            df=df,
            path=s3_path,
            index=False,
            compression="gzip",
            mode="overwrite_partitions",
            dataset=True,
            partition_cols=["year", "month"],
            boto3_session=session
        )
        print(f"  Written to {s3_path} partitioned by year and month")
    else:
        wr.s3.to_parquet(
            df=df,
            path=s3_path,
            index=False,
            compression="gzip",
            mode="overwrite",
            dataset=True,
            boto3_session=session
        )
        print(f"  Written to {s3_path} without partitioning")

# Main transform function


def transform_table(table_name):
    print(f"Transforming {table_name}...")

    df = read_from_landing(table_name)
    print(f"  Read {len(df)} rows from landing.")

    df = fix_duplicates(df, table_name)
    df = fix_datetime(df, table_name)
    df = fix_date(df, table_name)
    df = fix_capitalize_columns(df, table_name)

    if table_name == "patients":  # only patients has phone numbers in our schema
        df = fix_phone(df)

    write_to_s3processed(df, table_name)
    print(f"Finished transforming {table_name}.\n")
