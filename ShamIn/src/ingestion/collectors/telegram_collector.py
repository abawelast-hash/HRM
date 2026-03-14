"""Telegram Channel Collector with session rotation and anti-ban delays."""
from telethon import TelegramClient
from telethon.errors import FloodWaitError
import asyncio
import random
from datetime import datetime, timedelta
from typing import List, Dict

from .base import BaseCollector


class TelegramCollector(BaseCollector):
    """
    Telegram channel collector with:
    - Multiple accounts (session pool)
    - Random delays (anti-ban)
    - FloodWait handling
    """

    def __init__(self, name: str, channel: str, api_credentials: List[Dict]):
        super().__init__(name, source_type="telegram")
        self.channel = channel
        self.clients: List[TelegramClient] = []
        self.current_client_idx = 0

        for cred in api_credentials:
            client = TelegramClient(
                session=f"sessions/{cred['session_name']}",
                api_id=cred['api_id'],
                api_hash=cred['api_hash']
            )
            self.clients.append(client)

    async def __aenter__(self):
        for client in self.clients:
            await client.start()
        return self

    async def __aexit__(self, *args):
        for client in self.clients:
            await client.disconnect()

    def get_next_client(self) -> TelegramClient:
        """Rotate between accounts."""
        client = self.clients[self.current_client_idx]
        self.current_client_idx = (self.current_client_idx + 1) % len(self.clients)
        return client

    async def collect(self, limit: int = 100, since_hours: int = 24) -> List[Dict]:
        """Collect messages from channel."""
        items = []
        client = self.get_next_client()

        since_date = datetime.utcnow() - timedelta(hours=since_hours)

        try:
            async for message in client.iter_messages(
                self.channel,
                limit=limit,
                offset_date=since_date
            ):
                if not message.text:
                    continue

                raw_data = {
                    'timestamp': message.date,
                    'text': message.text,
                    'metadata': {
                        'message_id': message.id,
                        'views': message.views,
                        'forwards': message.forwards,
                        'has_media': message.media is not None,
                    }
                }

                items.append(self.to_unified_format(raw_data))

                # Random delay to avoid ban
                await asyncio.sleep(random.uniform(0.5, 2.0))

        except FloodWaitError as e:
            print(f"⚠️  FloodWait: waiting {e.seconds} seconds...")
            await asyncio.sleep(e.seconds)
            return await self.collect(limit, since_hours)

        return items
