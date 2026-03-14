"""Numeric value extractor from Arabic text."""
import re
from typing import Optional, List, Dict, Tuple
import logging

logger = logging.getLogger(__name__)


class NumericExtractor:
    """
    Extract prices, percentages, and directions from Arabic text.
    
    الميزات:
    - استخراج أسعار الصرف
    - استخراج النسب المئوية
    - تحديد اتجاه السعر (ارتفاع/انخفاض/استقرار)
    - استخراج جميع الأرقام
    - دعم الأرقام العربية والإنجليزية
    - استخراج سياق كامل
    """

    # تحويل الأرقام العربية إلى إنجليزية
    ARABIC_TO_ENGLISH = str.maketrans('٠١٢٣٤٥٦٧٨٩', '0123456789')

    # Price patterns (SYP)
    _PRICE_PATTERNS = [
        r'(?:الدولار|دولار|USD|usd)\s*:?\s*([\d,\.]+)',  # "الدولار 14500"
        r'(?:سعر\s*(?:الصرف|الدولار)?|السعر)\s*:?\s*([\d,\.]+)',  # "سعر الصرف 14500"
        r'([\d,\.]+)\s*(?:ليرة|ل\.س|SYP|syp)',  # "14500 ليرة"
        r'(?:مقابل|مع)\s*(?:الليرة|ل\.س)\s*([\d,\.]+)',  # "مقابل الليرة 14500"
        r'(\d{4,7})',  # fallback: any 4-7 digit number
    ]

    # Percentage patterns
    _PERCENTAGE_PATTERNS = [
        r'([\d,\.]+)\s*%',  # "5%"
        r'([\d,\.]+)\s*(?:بالمئة|بالمائة|في المئة|في المائة)',  # "5 بالمئة"
        r'نسبة\s*([\d,\.]+)',  # "نسبة 5"
    ]
    
    # Number pattern
    NUMBER_PATTERN = r'[\d٠-٩,\.]+(?:\.\d+)?'

    # Direction keywords
    _UP_WORDS = {'ارتفع', 'ارتفاع', 'صعود', 'زيادة', 'ارتقى', 'صاعد', 'زاد', 'طلع'}
    _DOWN_WORDS = {'انخفض', 'انخفاض', 'هبوط', 'تراجع', 'هابط', 'نزول', 'نزل', 'هبط'}
    _STABLE_WORDS = {'استقر', 'استقرار', 'ثبات', 'مستقر', 'ثابت'}
    
    def __init__(self):
        """تهيئة المستخرج."""
        self.price_patterns = [re.compile(p, re.IGNORECASE) for p in self._PRICE_PATTERNS]
        self.percentage_patterns = [re.compile(p, re.IGNORECASE) for p in self._PERCENTAGE_PATTERNS]
        self.number_pattern = re.compile(self.NUMBER_PATTERN)
    
    def normalize_arabic_numbers(self, text: str) -> str:
        """تحويل الأرقام العربية إلى إنجليزية."""
        return text.translate(self.ARABIC_TO_ENGLISH)

    def extract_price(self, text: str) -> Optional[float]:
        """
        Extract SYP price from text.
        
        Args:
            text: النص
            
        Returns:
            float أو None: السعر
        """
        text = self.normalize_arabic_numbers(text)
        
        for pattern in self.price_patterns:
            match = pattern.search(text)
            if match:
                price_str = match.group(1).replace(',', '')
                try:
                    price = float(price_str)
                    if self.validate_price(price):
                        return price
                except (ValueError, IndexError):
                    continue
        return None
    
    def extract_all_prices(self, text: str) -> List[float]:
        """
        استخراج جميع الأسعار من النص.
        
        Args:
            text: النص
            
        Returns:
            List[float]: قائمة الأسعار
        """
        text = self.normalize_arabic_numbers(text)
        prices = []
        
        for pattern in self.price_patterns:
            matches = pattern.findall(text)
            for match in matches:
                price_str = match.replace(',', '') if isinstance(match, str) else match[0].replace(',', '')
                try:
                    price = float(price_str)
                    if self.validate_price(price):
                        prices.append(price)
                except (ValueError, IndexError):
                    continue
        
        return list(set(prices))  # إزالة التكرار

    def extract_percentage(self, text: str) -> Optional[float]:
        """
        Extract percentage value.
        
        Args:
            text: النص
            
        Returns:
            float أو None: النسبة (بين 0 و 1)
        """
        text = self.normalize_arabic_numbers(text)
        
        for pattern in self.percentage_patterns:
            match = pattern.search(text)
            if match:
                try:
                    pct = float(match.group(1).replace(',', ''))
                    if 0 <= pct <= 100:
                        return pct / 100.0
                except (ValueError, IndexError):
                    continue
        return None
    
    def extract_all_percentages(self, text: str) -> List[float]:
        """
        استخراج جميع النسب المئوية.
        
        Args:
            text: النص
            
        Returns:
            List[float]: قائمة النسب (بين 0 و 1)
        """
        text = self.normalize_arabic_numbers(text)
        percentages = []
        
        for pattern in self.percentage_patterns:
            matches = pattern.findall(text)
            for match in matches:
                pct_str = match.replace(',', '') if isinstance(match, str) else match[0].replace(',', '')
                try:
                    pct = float(pct_str)
                    if 0 <= pct <= 100:
                        percentages.append(pct / 100.0)
                except (ValueError, IndexError):
                    continue
        
        return list(set(percentages))
    
    def extract_all_numbers(self, text: str) -> List[float]:
        """
        استخراج جميع الأرقام.
        
        Args:
            text: النص
            
        Returns:
            List[float]: قائمة الأرقام
        """
        text = self.normalize_arabic_numbers(text)
        matches = self.number_pattern.findall(text)
        
        numbers = []
        for match in matches:
            num_str = match.replace(',', '')
            try:
                numbers.append(float(num_str))
            except ValueError:
                continue
        
        return numbers

    def extract_direction(self, text: str) -> Optional[str]:
        """
        Extract price direction from text.
        
        Args:
            text: النص
            
        Returns:
            str أو None: 'up' أو 'down' أو 'stable'
        """
        words = set(text.split())
        if words & self._UP_WORDS:
            return "up"
        if words & self._DOWN_WORDS:
            return "down"
        if words & self._STABLE_WORDS:
            return "stable"
        return None
    
    def extract_price_change(self, text: str) -> Optional[Dict]:
        """
        استخراج التغير في السعر.
        
        Args:
            text: النص
            
        Returns:
            Dict أو None: {
                'direction': 'up'/'down'/'stable',
                'amount': float,
                'percentage': float
            }
        """
        direction = self.extract_direction(text)
        
        if not direction:
            return None
        
        amount = self.extract_price(text)
        percentage = self.extract_percentage(text)
        
        return {
            'direction': direction,
            'amount': amount,
            'percentage': percentage
        }

    def extract_all(self, text: str) -> Dict:
        """
        Extract all numeric information.
        
        Args:
            text: النص
            
        Returns:
            Dict: جميع المعلومات الرقمية
        """
        return {
            'price': self.extract_price(text),
            'all_prices': self.extract_all_prices(text),
            'percentage': self.extract_percentage(text),
            'all_percentages': self.extract_all_percentages(text),
            'direction': self.extract_direction(text),
            'price_change': self.extract_price_change(text),
            'all_numbers': self.extract_all_numbers(text),
        }
    
    def extract_currency_context(self, text: str) -> Dict:
        """
        استخراج سياق كامل للعملة.
        
        Args:
            text: النص
            
        Returns:
            Dict: سياق كامل
        """
        result = {
            'price': self.extract_price(text),
            'change': self.extract_price_change(text),
            'percentages': self.extract_all_percentages(text),
            'location': None
        }
        
        # استخراج الموقع
        locations = ['دمشق', 'حلب', 'إدلب', 'حمص', 'حماة', 'اللاذقية', 'طرطوس', 'درعا', 'السويداء']
        for loc in locations:
            if loc in text:
                result['location'] = loc
                break
        
        return result

    @staticmethod
    def validate_price(price: float, min_val: float = 100, max_val: float = 1_000_000) -> bool:
        """
        Validate that price is within reasonable SYP range.
        
        Args:
            price: السعر
            min_val: الحد الأدنى
            max_val: الحد الأقصى
            
        Returns:
            bool: صحيح إذا كان السعر منطقياً
        """
        return min_val <= price <= max_val
