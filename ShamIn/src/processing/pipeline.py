"""Main processing pipeline — خط معالجة البيانات الرئيسي."""
from typing import Dict, List, Optional
import logging
from src.processing.text.cleaner import TextCleaner
from src.processing.numeric.extractor import NumericExtractor

logger = logging.getLogger(__name__)


class ProcessingPipeline:
    """
    Orchestrates text cleaning and numeric extraction.
    
    يقوم بـ:
    - تنظيف النصوص العربية
    - استخراج الأسعار والأرقام
    - استخراج اتجاه السوق
    - استخراج النسب المئوية
    - تجهيز البيانات للتخزين والتحليل
    """

    def __init__(
        self,
        clean_for_sentiment: bool = False,
        remove_stopwords: bool = False
    ):
        """
        Args:
            clean_for_sentiment: تنظيف للمشاعر (يحتفظ ببعض علامات الترقيم)
            remove_stopwords: إزالة الكلمات الشائعة
        """
        self.cleaner = TextCleaner(
            remove_diacritics=True,
            normalize_arabic=True,
            remove_punctuation=not clean_for_sentiment,
            remove_english_numbers=False,  # نحتفظ بالأرقام للاستخراج
            remove_emails=True
        )
        self.extractor = NumericExtractor()
        self.clean_for_sentiment = clean_for_sentiment
        self.remove_stopwords_flag = remove_stopwords
        
        if remove_stopwords:
            self.stopwords = TextCleaner.get_arabic_stopwords()
        else:
            self.stopwords = None

    def process(self, raw_item: Dict) -> Dict:
        """
        Process a single raw data item.
        
        Args:
            raw_item: البيانات الخام {
                'id': str,
                'source': str,
                'raw_text': str,
                'timestamp': datetime,
                'raw_numeric': Optional[float],
                ...
            }
            
        Returns:
            Dict: البيانات المعالجة
        """
        text = raw_item.get('raw_text', '') or raw_item.get('text', '')
        
        if not text:
            logger.warning(f"Empty text in item {raw_item.get('id')}")
            return self._empty_result(raw_item)
        
        # تنظيف النص
        if self.clean_for_sentiment:
            cleaned_text = self.cleaner.clean_for_sentiment(text)
        else:
            cleaned_text = self.cleaner.clean(text)
        
        # إزالة stopwords إذا مطلوب
        if self.remove_stopwords_flag and self.stopwords:
            cleaned_text = TextCleaner.remove_stopwords(cleaned_text, self.stopwords)
        
        # استخراج المعلومات الرقمية
        numerics = self.extractor.extract_all(text)  # من النص الأصلي للدقة
        
        # استخراج السياق الكامل
        currency_context = self.extractor.extract_currency_context(text)
        
        return {
            'id': raw_item.get('id'),
            'source': raw_item.get('source'),
            'timestamp': raw_item.get('timestamp'),
            'original_text': text,
            'cleaned_text': cleaned_text,
            
            # الأسعار
            'extracted_price': numerics['price'] or raw_item.get('raw_numeric'),
            'all_prices': numerics['all_prices'],
            
            # التغيرات
            'direction': numerics['direction'],
            'price_change': numerics['price_change'],
            
            # النسب المئوية
            'percentage': numerics['percentage'],
            'all_percentages': numerics['all_percentages'],
            
            # جميع الأرقام
            'all_numbers': numerics['all_numbers'],
            
            # السياق
            'location': currency_context['location'],
            
            # البيانات الأصلية الأخرى
            'category': raw_item.get('category'),
            'language': raw_item.get('language'),
            'metadata': raw_item.get('metadata', {}),
        }
    
    def _empty_result(self, raw_item: Dict) -> Dict:
        """نتيجة فارغة في حالة عدم وجود نص."""
        return {
            'id': raw_item.get('id'),
            'source': raw_item.get('source'),
            'timestamp': raw_item.get('timestamp'),
            'original_text': '',
            'cleaned_text': '',
            'extracted_price': None,
            'all_prices': [],
            'direction': None,
            'price_change': None,
            'percentage': None,
            'all_percentages': [],
            'all_numbers': [],
            'location': None,
            'category': raw_item.get('category'),
            'language': raw_item.get('language'),
            'metadata': raw_item.get('metadata', {}),
        }

    def process_batch(self, items: List[Dict]) -> List[Dict]:
        """
        Process a batch of raw items.
        
        Args:
            items: قائمة البيانات الخام
            
        Returns:
            List[Dict]: قائمة البيانات المعالجة
        """
        results = []
        
        for item in items:
            try:
                processed = self.process(item)
                results.append(processed)
            except Exception as e:
                logger.error(f"Error processing item {item.get('id')}: {e}")
                results.append(self._empty_result(item))
        
        return results
    
    def process_for_storage(self, raw_item: Dict) -> Dict:
        """
        معالجة للتخزين (تنسيق محسّن لقاعدة البيانات).
        
        Args:
            raw_item: البيانات الخام
            
        Returns:
            Dict: بيانات جاهزة للتخزين
        """
        processed = self.process(raw_item)
        
        # تنسيق للتخزين
        return {
            'item_id': processed['id'],
            'source_name': processed['source'],
            'collected_at': processed['timestamp'],
            'original_text': processed['original_text'],
            'cleaned_text': processed['cleaned_text'],
            'extracted_price': processed['extracted_price'],
            'price_direction': processed['direction'],
            'percentage_change': processed['percentage'],
            'location': processed['location'],
            'category': processed['category'],
            'language': processed['language'],
            'metadata': processed['metadata'],
        }
    
    def process_for_ml(self, raw_item: Dict) -> Dict:
        """
        معالجة للنماذج ML (ميزات فقط).
        
        Args:
            raw_item: البيانات الخام
            
        Returns:
            Dict: ميزات جاهزة للـ ML
        """
        processed = self.process(raw_item)
        
        return {
            'text_features': {
                'cleaned_text': processed['cleaned_text'],
                'text_length': len(processed['cleaned_text'].split()),
                'has_price': processed['extracted_price'] is not None,
                'has_direction': processed['direction'] is not None,
                'has_percentage': processed['percentage'] is not None,
                'location': processed['location'],
            },
            'numeric_features': {
                'price': processed['extracted_price'],
                'direction': processed['direction'],
                'percentage': processed['percentage'],
                'num_prices': len(processed['all_prices']),
                'num_percentages': len(processed['all_percentages']),
                'num_numbers': len(processed['all_numbers']),
            },
            'metadata': {
                'source': processed['source'],
                'category': processed['category'],
                'language': processed['language'],
                'timestamp': processed['timestamp'],
            }
        }
