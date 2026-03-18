import requests
import boto3
import os
import datetime

s3 = boto3.client("s3")

DATA_URL = "https://eforexcel.com/wp/wp-content/uploads/2020/09/2m-Sales-Records.zip"
CURR_DATE = datetime.datetime.now().strftime("%Y-%m-%d")
KEY = f"raw_data/{CURR_DATE}/2m_sales_records.zip"
ARCHIVE_KEY = f"Archive/{CURR_DATE}/2m_sales_records.zip"

def handler(event, context):
    BUCKET_NAME = os.environ["BUCKET_NAME"]
    print(f"Downloading dataset from {DATA_URL}")

    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(DATA_URL, headers=headers, timeout=60)
        print(f"Response status code: {response.status_code}")

        if response.status_code != 200:
            raise Exception(f"Failed to download dataset: {response.status_code}")

        print("Uploading file to S3 Working Directory")

        s3.put_object(
            Bucket=BUCKET_NAME,
            Key=KEY,
            Body=response.content
        )

        return {"status": "success"}
    

    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        raise