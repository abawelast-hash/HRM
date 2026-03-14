"""Arabic text cleaner for ShamIn."""
import re
import html
import unicodedata
from typing import Optional, List
import logging

logger = logging.getLogger(__name__)


class TextCleaner:
    """
    Clean and normalize Arabic text from news sources.
    
    الميزات:
    - إزالة HTML tags and entities
    - إزالة التشكيل (diacritics)
    - تطبيع الحروف العربية
    - إزالة علامات الترقيم
    - إزالة الروابط والإيميلات
    - إزالة الإيموجي
    - توحيد المسافات
    """

    # Arabic normalization map
    _NORM_MAP = str.maketrans({
        'أ': 'ا', 'إ': 'ا', 'آ': 'ا', 'ٱ': 'ا',
        'ة': 'ه',
        'ى': 'ي',
    })

    # Eastern Arabic numerals → Western
    _NUMERAL_MAP = str.maketrans('٠١٢٣٤٥٦٧٨٩', '0123456789')
    
    # علامات الترقيم العربية والإنجليزية
    PUNCTUATION = re.compile(r'[،؛؟!\.,:;?\'"()\[\]{}«»""''…—–\-_+=@#$%^&*<>/\\|`~]')
    
    # الأرقام الإنجليزية
    ENGLISH_NUMBERS = re.compile(r'[0-9]+')

    def __init__(
        self,
        remove_diacritics: bool = True,
        normalize_arabic: bool = True,
        remove_punctuation: bool = False,
        remove_english_numbers: bool = False,
        remove_emails: bool = True
    ):
        """
        Args:
            remove_diacritics: إزالة التشكيل
            normalize_arabic: تطبيع الحروف العربية
            remove_punctuation: إزالة علامات الترقيم
            remove_english_numbers: إزالة الأرقام الإنجليزية
            remove_emails: إزالة الإيميلات
        """
        self.remove_diacritics_flag = remove_diacritics
        self.normalize_arabic_flag = normalize_arabic
        self.remove_punctuation_flag = remove_punctuation
        self.remove_english_numbers_flag = remove_english_numbers
        self.remove_emails_flag = remove_emails

    def clean(self, text: str) -> str:
        """Full cleaning pipeline."""
        if not text:
            return ""
        
        # فك ترميز HTML entities
        text = html.unescape(text)
        
        text = self.remove_html(text)
        text = self.remove_urls(text)
        
        if self.remove_emails_flag:
            text = self.remove_emails(text)
        
        text = self.remove_mentions_hashtags(text)
        text = self.remove_emojis(text)
        
        if self.normalize_arabic_flag:
            text = self.normalize_arabic(text)
        
        text = self.convert_numerals(text)
        
        if self.remove_diacritics_flag:
            text = self.remove_diacritics(text)
        
        if self.remove_english_numbers_flag:
            text = self.ENGLISH_NUMBERS.sub(' ', text)
        
        if self.remove_punctuation_flag:
            text = self.PUNCTUATION.sub(' ', text)
        
        text = self.normalize_whitespace(text)
        return text.strip()

    @staticmethod
    def remove_html(text: str) -> str:
        """إزالة HTML tags."""
        return re.sub(r'<[^>]+>', ' ', text)

    @staticmethod
    def remove_urls(text: str) -> str:
        """إزالة الروابط."""
        return re.sub(r'https?://\S+|www\.\S+', ' ', text)
    
    @staticmethod
    def remove_emails(text: str) -> str:
        """إزالة الإيميلات."""
        return re.sub(r'\S+@\S+\.\S+', ' ', text)

    @staticmethod
    def remove_mentions_hashtags(text: str) -> str:
        """إزالة المنشنات والهاشتاجات."""
        return re.sub(r'[@#]\S+', ' ', text)

    @staticmethod
    def remove_emojis(text: str) -> str:
        """إزالة الإيموجي."""
        emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"  # emoticons
            "\U0001F300-\U0001F5FF"  # symbols & pictographs
            "\U0001F680-\U0001F6FF"  # transport & map symbols
            "\U0001F900-\U0001F9FF"  # supplemental symbols
            "\U00002702-\U000027B0"  # dingbats
            "\U0001FA00-\U0001FA6F"  # chess symbols
            "\U0001FA70-\U0001FAFF"  # symbols extended
            "]+",
            flags=re.UNICODE
        )
        return emoji_pattern.sub(' ', text)

    def normalize_arabic(self, text: str) -> str:
        """تطبيع الحروف العربية."""
        return text.translate(self._NORM_MAP)

    def convert_numerals(self, text: str) -> str:
        """تحويل الأرقام العربية إلى إنجليزية."""
        return text.translate(self._NUMERAL_MAP)

    @staticmethod
    def remove_diacritics(text: str) -> str:
        """إزالة التشكيل."""
        return re.sub(r'[\u0617-\u061A\u064B-\u0652\u0670]', '', text)

    @staticmethod
    def normalize_whitespace(text: str) -> str:
        """توحيد المسافات."""
        return re.sub(r'\s+', ' ', text)
    
    def clean_batch(self, texts: List[str]) -> List[str]:
        """
        تنظيف مجموعة من النصوص.
        
        Args:
            texts: قائمة النصوص
            
        Returns:
            List[str]: قائمة النصوص النظيفة
        """
        return [self.clean(text) for text in texts]
    
    def clean_for_sentiment(self, text: str) -> str:
        """
        تنظيف نص لتحليل المشاعر (يحتفظ بعلامات التعجب والاستفهام).
        
        Args:
            text: النص
            
        Returns:
            str: نص منظف
        """
        if not text:
            return ""
        
        text = html.unescape(text)
        text = self.remove_html(text)
        text = self.remove_urls(text)
        text = self.remove_emails(text)
        text = self.normalize_arabic(text)
        text = self.convert_numerals(text)
        text = self.remove_diacritics(text)
        
        # إزالة كل علامات الترقيم ماعدا ! و ؟
        text = re.sub(r'[،؛\.,:;"\'"()\[\]{}«»""''…—–\-_+=@#$%^&*<>/\\|`~]', ' ', text)
        
        text = self.normalize_whitespace(text)
        return text.strip()
    
    @staticmethod
    def get_arabic_stopwords() -> set:
        """
        الحصول على قائمة الكلمات الشائعة العربية.
        
        Returns:
            set: مجموعة stopwords العربية
        """
        stopwords = {
            'في', 'من', 'الي', 'علي', 'عن', 'مع', 'هذا', 'هذه', 'ذلك', 'تلك',
            'التي', 'الذي', 'ما', 'لا', 'نعم', 'كان', 'كانت', 'يكون', 'تكون',
            'له', 'لها', 'لهم', 'لهن', 'به', 'بها', 'بهم', 'هو', 'هي', 'هم', 'هن',
            'ان', 'ان', 'لن', 'لم', 'قد', 'كل', 'بعض', 'غير', 'سوي', 'عند',
            'منذ', 'خلال', 'بعد', 'قبل', 'فوق', 'تحت', 'حول', 'عبر', 'ضد',
            'او', 'ام', 'لكن', 'لكنه', 'الا', 'غيره', 'سوي', 'ليس', 'ليست',
            'انا', 'انت', 'نحن', 'انتم', 'انتن', 'اياه', 'اياها', 'اياهم',
            'كيف', 'اين', 'متي', 'لماذا', 'كم', 'ماذا', 'من', 'اي', 'اية',
            'هل', 'الم', 'الن', 'اذا', 'اذ', 'حيث', 'بينما', 'عندما', 'كلما',
            'مثل', 'نحو', 'شبه', 'كان', 'كما', 'سواء', 'ايضا', 'ايضا', 'كذلك',
            'هنا', 'هناك', 'هنالك', 'ثم', 'ثمه', 'حتي', 'لعل', 'ليت', 'لو',
        }
        return stopwords
    
    @staticmethod
    def remove_stopwords(text: str, stopwords: set = None) -> str:
        """
        إزالة الكلمات الشائعة.
        
        Args:
            text: النص
            stopwords: مجموعة الكلمات الشائعة (اختياري)
            
        Returns:
            str: نص بدون stopwords
        """
        if stopwords is None:
            stopwords = TextCleaner.get_arabic_stopwords()
        
        words = text.split()
        filtered = [word for word in words if word not in stopwords]
        return ' '.join(filtered)
