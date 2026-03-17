import boto3
import pyarrow.csv as pv
import pyarrow.parquet as pq
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

    date = key.split("/")[1]

    s3.download_file(bucket, key, TMP_INPUT)

    os.makedirs(TMP_OUTPUT_DIR, exist_ok=True)

    # Read CSV using pyarrow
    table = pv.read_csv(TMP_INPUT)

    # Convert to pandas-like structure
    df = table.to_pandas()

    for country, group in df.groupby("Country"):

        clean_country = country.replace(" ", "_")

        local_file = f"{TMP_OUTPUT_DIR}/{clean_country}.parquet"

        pq.write_table(
            pv.Table.from_pandas(group),
            local_file
        )

        output_key = f"transformed_data/country={clean_country}/{clean_country}.parquet"

        s3.upload_file(local_file, bucket, output_key)

    return {"status": "success"}