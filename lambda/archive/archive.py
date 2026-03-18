import boto3
import os
import datetime

s3 = boto3.client("s3")

CURR_DATE = datetime.datetime.now().strftime("%Y-%m-%d")
ARCHIVE_KEY = f"Archive/{CURR_DATE}/2m_sales_records.zip"

def handler(event, context):
    BUCKET_NAME = os.environ["BUCKET_NAME"]
    try:
        print('Archiving file to S3')
        
        s3.copy_object(
            Bucket=BUCKET_NAME,
            Key=ARCHIVE_KEY,
            CopySource={"Bucket": BUCKET_NAME, "Key": event['Records'][0]['s3']['object']['key']}
        )

        print('Deleting original file from S3')
    
        response = s3.delete_object(
            Bucket=BUCKET_NAME,
            Key=f'raw_data/{CURR_DATE}/2m_sales_records.zip',
        )
        
        return {"status": "success"}

    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        raise