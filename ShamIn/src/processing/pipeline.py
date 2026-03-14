"""Main processing pipeline."""
from src.processing.text.cleaner import TextCleaner
from src.processing.numeric.extractor import NumericExtractor


class ProcessingPipeline:
    """Orchestrates text cleaning and numeric extraction."""

    def __init__(self):
        self.cleaner = TextCleaner()
        self.extractor = NumericExtractor()

    def process(self, raw_item: dict) -> dict:
        """Process a single raw data item."""
        text = raw_item.get('raw_text', '')

        cleaned_text = self.cleaner.clean(text)
        numerics = self.extractor.extract_all(cleaned_text)

        return {
            'id': raw_item.get('id'),
            'source': raw_item.get('source'),
            'timestamp': raw_item.get('timestamp'),
            'cleaned_text': cleaned_text,
            'extracted_price': numerics['price'] or raw_item.get('raw_numeric'),
            'direction': numerics['direction'],
            'percentage_change': numerics['percentage'],
        }

    def process_batch(self, items: list) -> list:
        """Process a batch of raw items."""
        return [self.process(item) for item in items]
