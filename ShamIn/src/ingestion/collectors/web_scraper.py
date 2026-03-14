"""Web Scraper for exchange rate websites."""
from bs4 import BeautifulSoup
import aiohttp
import re
from datetime import datetime
from typing import List, Dict, Optional

from .base import BaseCollector


class WebScraper(BaseCollector):
    def __init__(self, name: str, url: str, parser_config: Dict):
        super().__init__(name, source_type="web")
        self.url = url
        self.parser_config = parser_config

    async def collect(self) -> List[Dict]:
        """Scrape exchange rate from website."""
        async with aiohttp.ClientSession() as session:
            async with session.get(self.url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                html = await response.text()

        soup = BeautifulSoup(html, 'html.parser')
        price = self.extract_price(soup)

        if price is None:
            return []

        raw_data = {
            'timestamp': datetime.utcnow(),
            'text': f"سعر الصرف: {price}",
            'numeric': price,
            'metadata': {
                'source_url': self.url,
                'extraction_method': 'css_selector'
            }
        }

        return [self.to_unified_format(raw_data)]

    def extract_price(self, soup: BeautifulSoup) -> Optional[float]:
        """Extract price using CSS selector or regex."""
        if 'css_selector' in self.parser_config:
            element = soup.select_one(self.parser_config['css_selector'])
            if element:
                text = element.get_text(strip=True)
                return self._parse_price(text)

        if 'regex_pattern' in self.parser_config:
            pattern = self.parser_config['regex_pattern']
            match = re.search(pattern, soup.get_text())
            if match:
                return float(match.group(1).replace(',', ''))

        return None

    @staticmethod
    def _parse_price(text: str) -> Optional[float]:
        """Convert text to float price."""
        cleaned = re.sub(r'[^\d.]', '', text)
        try:
            return float(cleaned)
        except ValueError:
            return None
