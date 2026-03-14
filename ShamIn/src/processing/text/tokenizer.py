"""Arabic tokenizer for ShamIn."""
import re
from typing import List


# Common Arabic stop words
ARABIC_STOP_WORDS = {
    'في', 'من', 'على', 'إلى', 'عن', 'مع', 'هذا', 'هذه', 'ذلك', 'تلك',
    'التي', 'الذي', 'الذين', 'اللتين', 'اللذين', 'هو', 'هي', 'هم', 'هن',
    'أنا', 'نحن', 'أنت', 'أنتم', 'كان', 'كانت', 'يكون', 'تكون', 'لم',
    'لن', 'قد', 'قبل', 'بعد', 'عند', 'حتى', 'إذا', 'لو', 'أن', 'إن',
    'ما', 'لا', 'بل', 'لكن', 'و', 'أو', 'ثم', 'ف', 'ب', 'ل', 'ك',
    'كل', 'بعض', 'غير', 'بين', 'فوق', 'تحت', 'أمام', 'خلف', 'حول',
    'منذ', 'خلال', 'ضد', 'نحو', 'عبر', 'دون', 'سوى', 'أي', 'كما',
    'أيضا', 'حيث', 'يمكن', 'ليس', 'ليست', 'ولا', 'وقد', 'ولم', 'ومن',
}


class ArabicTokenizer:
    """Simple Arabic tokenizer with optional Farasa integration."""

    def __init__(self, remove_stop_words: bool = True, use_farasa: bool = False):
        self.remove_stop_words = remove_stop_words
        self.segmenter = None

        if use_farasa:
            try:
                from farasa.segmenter import FarasaSegmenter
                self.segmenter = FarasaSegmenter(interactive=True)
            except ImportError:
                pass

    def tokenize(self, text: str) -> List[str]:
        """Tokenize Arabic text."""
        if self.segmenter:
            segmented = self.segmenter.segment(text)
            tokens = segmented.split()
        else:
            tokens = re.findall(r'[\w\u0600-\u06FF]+', text)

        if self.remove_stop_words:
            tokens = [t for t in tokens if t not in ARABIC_STOP_WORDS]

        return tokens
