import boto3
import zipfile
import os
import urllib.parse

s3 = boto3.client("s3")

TMP_ZIP_PATH = "/tmp/input.zip"
TMP_EXTRACT_PATH = "/tmp/extracted"

def handler(event, context):
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = urllib.parse.unquote_plus(
        event['Records'][0]['s3']['object']['key']
    )

    print(f"Processing file: s3://{bucket}/{key}")

    parts = key.split("/")
    date = parts[1]

    s3.download_file(bucket, key, TMP_ZIP_PATH)

    os.makedirs(TMP_EXTRACT_PATH, exist_ok=True)

    with zipfile.ZipFile(TMP_ZIP_PATH, 'r') as zip_ref:
        zip_ref.extractall(TMP_EXTRACT_PATH)

    print("Extraction complete")

    for file_name in os.listdir(TMP_EXTRACT_PATH):

        local_path = os.path.join(TMP_EXTRACT_PATH, file_name)

        output_key = f"processed_data/{date}/{file_name}"

        print(f"Uploading {file_name} to {output_key}")

        s3.upload_file(local_path, bucket, output_key)

    return {"status": "success"}