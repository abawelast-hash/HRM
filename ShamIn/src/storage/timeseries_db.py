"""InfluxDB time-series client."""
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
import os
from datetime import datetime


class TimeSeriesDB:
    """Client for InfluxDB time-series operations."""

    def __init__(self):
        self.url = os.getenv('INFLUXDB_URL', 'http://localhost:8086')
        self.token = os.getenv('INFLUXDB_TOKEN', '')
        self.org = os.getenv('INFLUXDB_ORG', 'shamin_org')
        self._client = None

    @property
    def client(self):
        if self._client is None:
            self._client = InfluxDBClient(url=self.url, token=self.token, org=self.org)
        return self._client

    def write_price(self, bucket: str, source: str, price: float, timestamp: datetime = None):
        """Write an exchange rate data point."""
        write_api = self.client.write_api(write_options=SYNCHRONOUS)
        point = (
            Point("exchange_rate")
            .tag("source", source)
            .field("price", price)
            .time(timestamp or datetime.utcnow())
        )
        write_api.write(bucket=bucket, record=point)

    def query_prices(self, bucket: str, range_hours: int = 24) -> list:
        """Query recent exchange rate data."""
        query_api = self.client.query_api()
        query = f'''
        from(bucket: "{bucket}")
          |> range(start: -{range_hours}h)
          |> filter(fn: (r) => r._measurement == "exchange_rate")
          |> sort(columns: ["_time"])
        '''
        result = query_api.query(query)
        records = []
        for table in result:
            for record in table.records:
                records.append({
                    'time': record.get_time(),
                    'value': record.get_value(),
                    'source': record.values.get('source'),
                })
        return records

    def close(self):
        if self._client:
            self._client.close()
            self._client = None
