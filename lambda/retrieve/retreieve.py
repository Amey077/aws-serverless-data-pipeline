import requests
import boto3
import os

s3 = boto3.client("s3")

DATA_URL = "https://eforexcel.com/wp/wp-content/uploads/2020/09/2m-Sales-Records.zip"

BUCKET = "${AWS::AccountId}-aws-serverless-data-pipeline-s3-bucket"
KEY = "raw_data/sales_records.zip"

def handler(event, context):

    print(f"Downloading dataset from {DATA_URL}")

    response = requests.get(DATA_URL)

    if response.status_code != 200:
        raise Exception("Failed to download dataset")

    print("Uploading to S3...")

    s3.put_object(
        Bucket=BUCKET,
        Key=KEY,
        Body=response.content
    )

    return {"status": "success"}