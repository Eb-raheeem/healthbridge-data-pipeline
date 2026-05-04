import sys  # noqa: E402
import os  # noqa: E402
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # noqa: E402

from checks.checks import run_all_checks
from elt.extract import get_engine, extract_table
from elt.load import upload_to_s3
from config import TABLES
from catalog.catalog import register_tables_in_glue
from elt.transform import transform_table


def run_pipeline():
    print("=== HealthBridge ELT Pipeline starting ===\n")

    # Step 1: Connect to the database
    engine = get_engine()

    # Step 2: Extract and upload each table
    for schema, table in TABLES:
        print(f"\nProcessing table: {schema}.{table}")

        # Extract data
        df = extract_table(engine, schema, table)

        # Upload to S3
        upload_to_s3(df, table_name=table)
    print("\n=== All tables loaded to S3 landing zone. successfully ===")

    # Step 3: Transform each table
    print("\n=== Starting transformation phase ===")
    for _, table in TABLES:
        transform_table(table)
    print("\n=== All tables transformed and written to S3 processed zone successfully ===")

    # Step 4: Update Glue Catalog
    print("\n=== Registering tables in Glue Catalog ===")
    register_tables_in_glue()
    print("\n=== HealthBridge ELT Pipeline completed successfully ===")

    # Step 5: Run data quality checks
    print("\n=== Running data quality checks ===")
    from checks.checks import run_all_checks
    run_all_checks()
    print("\n=== Data quality checks completed ===")


if __name__ == "__main__":
    run_pipeline()
