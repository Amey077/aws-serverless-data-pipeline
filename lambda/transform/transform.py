import boto3
import pandas as pd
import urllib.parse
import os

s3 = boto3.client("s3")

TMP_INPUT = "/tmp/input.csv"
TMP_OUTPUT_DIR = "/tmp/output"

def handler(event, context):

    bucket = event['Records'][0]['s3']['bucket']['name']
    key = urllib.parse.unquote_plus(
        event['Records'][0]['s3']['object']['key']
    )

    print(f"Processing: s3://{bucket}/{key}")

    # Extract date
    date = key.split("/")[1]

    # Download CSV
    s3.download_file(bucket, key, TMP_INPUT)

    print("File downloaded")

    # Read CSV
    df = pd.read_csv(TMP_INPUT)

    print(f"Rows: {len(df)}")

    # Create output directory
    os.makedirs(TMP_OUTPUT_DIR, exist_ok=True)

    # Partition by Country
    for country, group in df.groupby("Country"):

        clean_country = country.replace(" ", "_")

        local_file = f"{TMP_OUTPUT_DIR}/{clean_country}.parquet"

        group.to_parquet(local_file, index=False)

        output_key = f"transformed_data/country={clean_country}/{clean_country}.parquet"

        print(f"Uploading: {output_key}")

        s3.upload_file(local_file, bucket, output_key)

    # OPTIONAL: archive original zip
    archive_key = f"archive/{date}/{key.split('/')[-1]}"

    s3.copy_object(
        Bucket=bucket,
        CopySource={'Bucket': bucket, 'Key': key},
        Key=archive_key
    )

    print(f"Archived to {archive_key}")

    return {"status": "success"}