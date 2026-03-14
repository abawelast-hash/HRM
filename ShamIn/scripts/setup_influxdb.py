"""ShamIn - InfluxDB bucket setup script."""
from influxdb_client import InfluxDBClient, BucketsApi
import os


def setup_influxdb():
    url = os.getenv('INFLUXDB_URL', 'http://localhost:8086')
    token = os.getenv('INFLUXDB_TOKEN')
    org = os.getenv('INFLUXDB_ORG', 'shamin_org')

    client = InfluxDBClient(url=url, token=token, org=org)
    buckets_api = BucketsApi(client)

    buckets = [
        ('exchange_rates', '90d'),
        ('external_indicators', '90d'),
        ('features', '30d'),
        ('predictions', '365d'),
    ]

    for bucket_name, retention in buckets:
        try:
            buckets_api.create_bucket(
                bucket_name=bucket_name,
                org=org,
                retention_rules=[{"everySeconds": retention}]
            )
            print(f"✅ Bucket '{bucket_name}' created")
        except Exception as e:
            print(f"⚠️  Bucket '{bucket_name}' might already exist: {e}")

    client.close()


if __name__ == "__main__":
    setup_influxdb()
