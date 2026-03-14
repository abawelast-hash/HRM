"""RSS Feed Collector."""
import feedparser
import asyncio
from datetime import datetime
from typing import List, Dict

from .base import BaseCollector


class RSSCollector(BaseCollector):
    def __init__(self, name: str, url: str):
        super().__init__(name, source_type="rss")
        self.url = url

    async def collect(self, since: datetime = None) -> List[Dict]:
        """Collect latest items from RSS feed."""
        loop = asyncio.get_event_loop()
        feed = await loop.run_in_executor(None, feedparser.parse, self.url)

        items = []
        for entry in feed.entries:
            published = entry.get('published_parsed')
            if published:
                pub_date = datetime(*published[:6])
            else:
                pub_date = datetime.utcnow()

            if since and pub_date < since:
                continue

            raw_data = {
                'timestamp': pub_date,
                'text': f"{entry.get('title', '')} {entry.get('summary', '')}",
                'metadata': {
                    'title': entry.get('title'),
                    'link': entry.get('link'),
                    'author': entry.get('author'),
                }
            }

            items.append(self.to_unified_format(raw_data))

        return items
