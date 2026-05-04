import sys  # noqa: E402
import os  # noqa: E402
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # noqa: E402

from config import AWS_CONFIG, TABLES, S3_PROCESSED_FOLDER
from elt.extract import get_engine
from sqlalchemy import text
import boto3
import awswrangler as wr


result = []


def s3_session():
    session = boto3.Session(
        aws_access_key_id=AWS_CONFIG["access_key_id"],
        aws_secret_access_key=AWS_CONFIG["secret_access_key"],
        region_name=AWS_CONFIG["region"]
    )
    return session


def log_result(table_name, check, status, details=""):
    icon = "✅" if status == "PASS" else "❌"
    msg = f"{icon} [{status}] {check}"
    if details:
        msg += f" - ({details})"
    print(msg)
    result.append({
        "table": table_name,
        "check": check,
        "status": status,
        "details": details
    })


def run_checks():
    print("=== Running data quality checks ===")
    session = s3_session()
    for _, table in TABLES:
        try:
            # Check 1: Row count postgresql database vs S3
            print(f"\nChecking table: {table}")
            engine = get_engine()
            with engine.connect() as conn:
                db_count = conn.execute(
                    text(f"SELECT COUNT(*) FROM prod.{table}")).scalar()

            s3_path = f"s3://{AWS_CONFIG['bucket_name']}/{S3_PROCESSED_FOLDER}/{table}"
            df = wr.s3.read_parquet(s3_path, boto3_session=session)

            if db_count == len(df):
                log_result(table, "Row count check", "PASS",
                           f"{db_count} rows in both DB and S3")
            else:
                log_result(table, "Row count check", "FAIL",
                           f"{db_count} rows in DB vs {len(df)} rows in S3")

            # Check 2: Null checks
            null_counts = df.isnull().sum()
            nulls_found = null_counts[null_counts > 0]
            if nulls_found.empty:
                log_result(table, "Null check", "PASS", "No null values found")
            else:
                log_result(table, "Null check", "FAIL",
                           f"Null values found in columns: {nulls_found.to_dict()}")

            # Check 3: Duplicate checks
            duplicate_count = df.duplicated().sum()
            if duplicate_count == 0:
                log_result(table, "Duplicate check", "PASS",
                           "No duplicate rows found")
            else:
                log_result(table, "Duplicate check", "FAIL",
                           f"{duplicate_count} duplicate rows found")

        except Exception as e:
            log_result(table, "Data quality checks", "FAIL", str(e))


def print_summary():
    print("\n=== Data Quality Check Summary ===")
    failed = [r for r in result if r["status"] == "FAIL"]
    passed = [r for r in result if r["status"] == "PASS"]
    print(
        f"Total checks: {len(result)} | Passed: {len(passed)} | Failed: {len(failed)}")
    if failed:
        print("\nFailed Checks Details:")
        for r in failed:
            print(
                f"- Table: {r['table']}, Check: {r['check']}, Details: {r['details']}")
    else:
        print("All checks passed successfully!")


def run_all_checks():
    run_checks()
    print_summary()
