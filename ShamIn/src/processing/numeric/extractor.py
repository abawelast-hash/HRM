"""Numeric value extractor from Arabic text."""
import re
from typing import Optional, Tuple


class NumericExtractor:
    """Extract prices, percentages, and directions from Arabic text."""

    # Price patterns (SYP)
    _PRICE_PATTERNS = [
        r'(\d{1,3}[,.]?\d{3,})\s*(?:ل\.س|ليرة|SYP)',
        r'(?:الدولار|dollar)\s*(?:=|:)?\s*(\d{1,3}[,.]?\d{3,})',
        r'(\d{4,7})',  # fallback: any 4-7 digit number
    ]

    # Percentage patterns
    _PCT_PATTERN = re.compile(r'(\d+\.?\d*)\s*%')

    # Direction keywords
    _UP_WORDS = {'ارتفع', 'ارتفاع', 'صعود', 'زيادة', 'ارتقى', 'صاعد'}
    _DOWN_WORDS = {'انخفض', 'انخفاض', 'هبوط', 'تراجع', 'هابط', 'نزول'}
    _STABLE_WORDS = {'استقر', 'استقرار', 'ثبات', 'مستقر'}

    def extract_price(self, text: str) -> Optional[float]:
        """Extract SYP price from text."""
        for pattern in self._PRICE_PATTERNS:
            match = re.search(pattern, text)
            if match:
                price_str = match.group(1).replace(',', '')
                try:
                    price = float(price_str)
                    if self.validate_price(price):
                        return price
                except ValueError:
                    continue
        return None

    def extract_percentage(self, text: str) -> Optional[float]:
        """Extract percentage value."""
        match = self._PCT_PATTERN.search(text)
        if match:
            return float(match.group(1)) / 100.0
        return None

    def extract_direction(self, text: str) -> Optional[str]:
        """Extract price direction from text."""
        words = set(text.split())
        if words & self._UP_WORDS:
            return "up"
        if words & self._DOWN_WORDS:
            return "down"
        if words & self._STABLE_WORDS:
            return "stable"
        return None

    def extract_all(self, text: str) -> dict:
        """Extract all numeric information."""
        return {
            'price': self.extract_price(text),
            'percentage': self.extract_percentage(text),
            'direction': self.extract_direction(text),
        }

    @staticmethod
    def validate_price(price: float, min_val: float = 100, max_val: float = 1_000_000) -> bool:
        """Validate that price is within reasonable SYP range."""
        return min_val <= price <= max_val
