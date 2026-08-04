import boto3
from app.core.config import settings
from botocore.config import Config

def generate_upload_post(s3_key: str, content_type: str, max_size_bytes: int = 50_000_000) -> dict:
    client = boto3.client(
        "s3",
        region_name=settings.aws_region,
        config=Config(signature_version="s3v4")
    )
    return client.generate_presigned_post(
        Bucket=settings.documents_bucket_name,
        Key=s3_key,
        Fields={"Content-Type": content_type},
        Conditions=[
            {"Content-Type": content_type},
            ["content-length-range", 0, max_size_bytes],
        ],
        ExpiresIn=300,
    )