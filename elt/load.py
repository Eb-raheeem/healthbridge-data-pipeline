import sys  # noqa: E402
import os  # noqa: E402
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # noqa: E402

import boto3
import awswrangler as wr
from config import AWS_CONFIG, S3_LANDING_FOLDER


def s3_session():
    """Create an S3 session using boto3."""
    try:
        session = boto3.Session(
            aws_access_key_id=AWS_CONFIG["access_key_id"],
            aws_secret_access_key=AWS_CONFIG["secret_access_key"],
            region_name=AWS_CONFIG["region"]
        )
        print("Successfully created S3 session.")
        return session
    except Exception as e:
        print(f"Error creating S3 session: {e}")
        raise


def upload_to_s3(df, table_name):
    """Upload a DataFrame to S3 as a CSV file."""
    try:
        session = s3_session()
        s3_path = f"s3://{AWS_CONFIG['bucket_name']}/{S3_LANDING_FOLDER}/{table_name}"

        # Use awswrangler to upload the DataFrame to S3
        wr.s3.to_csv(
            df=df,
            path=s3_path,
            index=False,
            mode="overwrite",
            dataset=True,
            boto3_session=session
        )

        print(f"Successfully uploaded to {s3_path}.")
    except Exception as e:
        print(f"Error uploading to S3: {e}")
        raise
