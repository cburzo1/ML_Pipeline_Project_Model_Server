from io import BytesIO

import boto3
import os
from dotenv import load_dotenv

load_dotenv()

'''print("AWS_ACCESS_KEY_ID:", os.getenv("AWS_ACCESS_KEY_ID"))
print("AWS_SECRET_ACCESS_KEY:", os.getenv("AWS_SECRET_ACCESS_KEY"))
print("AWS_REGION:", os.getenv("AWS_REGION"))
print("AWS_BUCKET_NAME:", os.getenv("AWS_BUCKET_NAME"))'''

s3_client = boto3.client(
    "s3",
    region_name=os.getenv("AWS_REGION"),
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY")
)

BUCKET_NAME = os.getenv("AWS_BUCKET_NAME")


def upload_file(file, path):

    s3_client.upload_fileobj(
        file,
        BUCKET_NAME,
        path
    )

def get_file(path):
    file = BytesIO()

    s3_client.download_fileobj(
        BUCKET_NAME,
        path,
        file
    )

    file.seek(0)

    return file

def delete_file(path):

    s3_client.delete_object(
        Bucket=BUCKET_NAME,
        Key=path
    )