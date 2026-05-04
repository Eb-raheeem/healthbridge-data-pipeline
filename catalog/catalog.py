import sys  # noqa: E402
import os  # noqa: E402
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # noqa: E402

import awswrangler as wr
import boto3
from config import AWS_CONFIG, S3_PROCESSED_FOLDER


# ---schema definitions ---
table_schemas = {
    "centers": {
        "center_id": "bigint",
        "center_name": "string",
        "city": "string",
        "state": "string",
        "created_datetime": "timestamp",
        "created_date": "date"
    },
    "appointments": {
        "appointment_id": "bigint",
        "patient_id": "bigint",
        "center_id": "bigint",
        "status": "string",
        "appointment_datetime": "timestamp",
        "appointment_date": "date"
    },
    "payments": {
        "payment_id": "bigint",
        "patient_id": "bigint",
        "payment_method": "string",
        "payment_status": "string",
        "amount": "double",
        "payment_datetime": "timestamp",
        "payment_date": "date"
    },
    "patients": {
        "patient_id": "bigint",
        "first_name": "string",
        "last_name": "string",
        "gender": "string",
        "date_of_birth": "date",
        "phone": "string",
        "phone_ext": "string",
        "email": "string",
        "created_datetime": "timestamp",
        "created_date": "date"
    },
    "tests": {
        "test_id": "bigint",
        "test_name": "string",
        "category": "string",
        "price": "bigint",
    },
    "test_results": {
        "result_id": "bigint",
        "appointment_id": "bigint",
        "test_id": "bigint",
        "result_value": "double",
        "result_status": "string",
        "test_datetime": "timestamp",
        "test_date": "date",
        "created_datetime": "timestamp",
        "created_date": "date"
    }
}

# Partition schema
partition_schemas = {
    "year": "bigint",
    "month": "bigint",
}

# Partitioned tables
partitioned_tables = ["appointments", "payments", "test_results"]

GLUE_DATABASE = "healthbridge"

# s3 session


def s3_session():
    session = boto3.Session(
        aws_access_key_id=AWS_CONFIG["access_key_id"],
        aws_secret_access_key=AWS_CONFIG["secret_access_key"],
        region_name=AWS_CONFIG["region"]
    )
    return session


def register_table(table_name, session):
    """Register the transformed table in AWS Glue Catalog."""
    s3_path = f"s3://{AWS_CONFIG['bucket_name']}/{S3_PROCESSED_FOLDER}/{table_name}/"
    schema = table_schemas.get(table_name, {})

    wr.catalog.create_parquet_table(
        database=GLUE_DATABASE,
        table=table_name,
        path=s3_path,
        columns_types=schema,
        partitions_types=partition_schemas if table_name in partitioned_tables else None,
        compression="gzip",
        boto3_session=session,
        mode="overwrite"
    )
    print(f"Registered {table_name} in Glue Catalog")


def register_partitions(table_name, session):
    """Add partitions to the Glue Catalog for a partitioned table."""
    if table_name not in partitioned_tables:
        return
    wr.athena.repair_table(
        database=GLUE_DATABASE,
        table=table_name,
        boto3_session=session
    )
    print(f"Added partitions for {table_name} in Glue Catalog")


def register_tables_in_glue():
    """Register all transformed tables in AWS Glue Catalog."""
    session = s3_session()
    print("Registering tables in Glue Catalog...\n")

    for table_name in table_schemas.keys():
        print(f"Registering table: {table_name}")
        register_table(table_name, session)
        register_partitions(table_name, session)

    print("Finished registering tables in Glue Catalog.")
    print("You can now query the tables using Athena.")
