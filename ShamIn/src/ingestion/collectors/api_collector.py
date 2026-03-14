"""External Economic Indicators Collector."""
import aiohttp
from datetime import datetime
from typing import List, Dict

from .base import BaseCollector


class APICollector(BaseCollector):
    """Collect external economic indicators from APIs."""

    def __init__(self, name: str, metric: str, endpoint: str):
        super().__init__(name, source_type="api")
        self.metric = metric
        self.endpoint = endpoint

    async def collect(self) -> List[Dict]:
        """Fetch indicator value."""
        async with aiohttp.ClientSession() as session:
            async with session.get(
                self.endpoint,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                data = await response.json()

        value = self._parse_response(data)

        raw_data = {
            'timestamp': datetime.utcnow(),
            'text': f"{self.metric}: {value}",
            'numeric': value,
            'metadata': {
                'metric': self.metric,
            }
        }

        return [self.to_unified_format(raw_data)]

    @staticmethod
    def _parse_response(data: dict) -> float:
        """Extract value from API response."""
        if 'price' in data:
            return float(data['price'])
        elif 'value' in data:
            return float(data['value'])
        elif 'data' in data and isinstance(data['data'], list) and data['data']:
            return float(data['data'][-1].get('value', 0))
        raise ValueError(f"Unknown API response format: {list(data.keys())}")
