import boto3
import pyarrow.csv as pv
import pyarrow.parquet as pq
import pyarrow.compute as pc
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

    s3.download_file(bucket, key, TMP_INPUT)

    os.makedirs(TMP_OUTPUT_DIR, exist_ok=True)

    table = pv.read_csv(TMP_INPUT)

    countries = pc.unique(table['Country'])

    for country in countries.to_pylist():

        clean_country = country.replace(" ", "_")

        mask = pc.equal(table['Country'], country)
        filtered = table.filter(mask)

        local_file = f"{TMP_OUTPUT_DIR}/{clean_country}.parquet"

        pq.write_table(filtered, local_file)

        output_key = f"transformed_data/country={clean_country}/{clean_country}.parquet"

        with open(local_file, "rb") as f:
            s3.put_object(
                Bucket=bucket,
                Key=output_key,
                Body=f
            )

    return {"status": "success"}