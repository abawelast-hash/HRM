"""ShamIn - MinIO bucket setup script."""
from minio import Minio
import os


def setup_minio():
    client = Minio(
        os.getenv('MINIO_ENDPOINT', 'localhost:9000'),
        access_key=os.getenv('MINIO_ACCESS_KEY'),
        secret_key=os.getenv('MINIO_SECRET_KEY'),
        secure=False
    )

    buckets = ['raw-data', 'models', 'backups', 'embeddings', 'reports']

    for bucket in buckets:
        if not client.bucket_exists(bucket):
            client.make_bucket(bucket)
            print(f"✅ Bucket '{bucket}' created")
        else:
            print(f"ℹ️  Bucket '{bucket}' already exists")


if __name__ == "__main__":
    setup_minio()
