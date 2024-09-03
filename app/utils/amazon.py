import os
import io

from boto3 import client
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())
 
s3_client = client(
    "s3",
    aws_access_key_id= os.getenv('AWS_ACCESS_KEY'),
    aws_secret_access_key= os.getenv('AWS_SECRET_KEY'),
    region_name="ap-northeast-2",
)


def upload_to_s3(file: io.BytesIO, bucket_name: str, file_name: str) -> None:
    s3_client.upload_fileobj(
        file,
        bucket_name,
        file_name,
        ExtraArgs={"ContentType": "image/jpeg"},
    )
