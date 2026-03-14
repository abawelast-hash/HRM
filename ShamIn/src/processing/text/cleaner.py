"""Arabic text cleaner for ShamIn."""
import re
import unicodedata


class TextCleaner:
    """Clean and normalize Arabic text from news sources."""

    # Arabic normalization map
    _NORM_MAP = str.maketrans({
        'أ': 'ا', 'إ': 'ا', 'آ': 'ا',
        'ة': 'ه',
        'ى': 'ي',
    })

    # Eastern Arabic numerals → Western
    _NUMERAL_MAP = str.maketrans('٠١٢٣٤٥٦٧٨٩', '0123456789')

    def clean(self, text: str) -> str:
        """Full cleaning pipeline."""
        if not text:
            return ""
        text = self.remove_html(text)
        text = self.remove_urls(text)
        text = self.remove_mentions_hashtags(text)
        text = self.remove_emojis(text)
        text = self.normalize_arabic(text)
        text = self.convert_numerals(text)
        text = self.remove_diacritics(text)
        text = self.normalize_whitespace(text)
        return text.strip()

    @staticmethod
    def remove_html(text: str) -> str:
        return re.sub(r'<[^>]+>', '', text)

    @staticmethod
    def remove_urls(text: str) -> str:
        return re.sub(r'https?://\S+|www\.\S+', '', text)

    @staticmethod
    def remove_mentions_hashtags(text: str) -> str:
        return re.sub(r'[@#]\S+', '', text)

    @staticmethod
    def remove_emojis(text: str) -> str:
        emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"
            "\U0001F300-\U0001F5FF"
            "\U0001F680-\U0001F6FF"
            "\U0001F900-\U0001F9FF"
            "\U00002702-\U000027B0"
            "\U0001FA00-\U0001FA6F"
            "\U0001FA70-\U0001FAFF"
            "]+",
            flags=re.UNICODE
        )
        return emoji_pattern.sub('', text)

    def normalize_arabic(self, text: str) -> str:
        return text.translate(self._NORM_MAP)

    def convert_numerals(self, text: str) -> str:
        return text.translate(self._NUMERAL_MAP)

    @staticmethod
    def remove_diacritics(text: str) -> str:
        return re.sub(r'[\u0617-\u061A\u064B-\u0652]', '', text)

    @staticmethod
    def normalize_whitespace(text: str) -> str:
        return re.sub(r'\s+', ' ', text)
