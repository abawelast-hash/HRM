"""MinIO object storage client."""
from minio import Minio
import os
import io
import json
from datetime import datetime


class ObjectStore:
    """Client for MinIO object storage operations."""

    def __init__(self):
        self._client = None

    @property
    def client(self):
        if self._client is None:
            self._client = Minio(
                os.getenv('MINIO_ENDPOINT', 'localhost:9000'),
                access_key=os.getenv('MINIO_ACCESS_KEY', ''),
                secret_key=os.getenv('MINIO_SECRET_KEY', ''),
                secure=False,
            )
        return self._client

    def save_model(self, model_name: str, model_bytes: bytes, version: str):
        """Save a trained model to MinIO."""
        bucket = "models"
        object_name = f"{model_name}/{version}/{model_name}_{version}.pth"
        data = io.BytesIO(model_bytes)
        self.client.put_object(bucket, object_name, data, len(model_bytes))
        return object_name

    def load_model(self, object_name: str) -> bytes:
        """Load a model from MinIO."""
        response = self.client.get_object("models", object_name)
        return response.read()

    def save_json(self, bucket: str, key: str, data: dict):
        """Save JSON data to MinIO."""
        content = json.dumps(data, ensure_ascii=False, default=str).encode('utf-8')
        stream = io.BytesIO(content)
        self.client.put_object(bucket, key, stream, len(content), content_type='application/json')

    def list_models(self, model_name: str = None) -> list:
        """List all saved models."""
        prefix = f"{model_name}/" if model_name else ""
        objects = self.client.list_objects("models", prefix=prefix, recursive=True)
        return [obj.object_name for obj in objects]
