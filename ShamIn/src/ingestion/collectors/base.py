"""Base Collector Class — unified pattern for all data collectors."""
from abc import ABC, abstractmethod
from typing import List, Dict, Any
import asyncio
import hashlib
from datetime import datetime
import uuid


class BaseCollector(ABC):
    """
    Base class for all data collectors.
    Inspired by data_fetcher.py in ACTION-main.
    """

    def __init__(self, name: str, source_type: str):
        self.name = name
        self.source_type = source_type
        self.session = None

    @abstractmethod
    async def collect(self, **kwargs) -> List[Dict[str, Any]]:
        """Collect data from source — implemented by subclasses."""
        pass

    def compute_hash(self, content: str) -> str:
        """Compute SHA-256 hash for deduplication."""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()

    def to_unified_format(self, raw_data: Dict) -> Dict:
        """Convert to unified schema."""
        return {
            "id": str(uuid.uuid4()),
            "source": self.name,
            "source_type": self.source_type,
            "timestamp": raw_data.get('timestamp', datetime.utcnow()),
            "raw_text": raw_data.get('text', ''),
            "raw_numeric": raw_data.get('numeric'),
            "language": raw_data.get('language', 'ar'),
            "metadata": raw_data.get('metadata', {}),
            "content_hash": self.compute_hash(str(raw_data))
        }

    async def collect_with_retry(self, max_retries: int = 3, **kwargs) -> List[Dict[str, Any]]:
        """Collect with exponential backoff retry."""
        for attempt in range(max_retries):
            try:
                return await self.collect(**kwargs)
            except Exception as e:
                wait_time = 2 ** attempt
                print(f"⚠️  {self.name} attempt {attempt + 1} failed: {e}. Retrying in {wait_time}s...")
                await asyncio.sleep(wait_time)

        raise Exception(f"Failed to collect from {self.name} after {max_retries} attempts")
