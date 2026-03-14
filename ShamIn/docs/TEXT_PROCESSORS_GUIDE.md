# 🔧 دليل معالجات النصوص - Text Processors Guide

## نظرة عامة

معالجات النصوص في **ShamIn** مسؤولة عن:
1. **تنظيف** النصوص العربية
2. **استخراج** المعلومات الرقمية (أسعار، نسب، أرقام)
3. **تجهيز** البيانات للتخزين والتحليل

---

## 1️⃣ TextCleaner — منظف النصوص

### الاستخدام الأساسي

```python
from src.processing.text.cleaner import TextCleaner

# إنشاء منظف
cleaner = TextCleaner(
    remove_diacritics=True,      # إزالة التشكيل
    normalize_arabic=True,        # تطبيع الحروف (إأآ → ا)
    remove_punctuation=True,      # إزالة علامات الترقيم
    remove_urls=True,             # إزالة الروابط
    remove_emails=True,           # إزالة الإيميلات
    remove_english_numbers=False, # الاحتفاظ بالأرقام
)

# تنظيف نص
text = "<p>السُّورِيَّةُ: أعلن البنك أن السعر 14,500 ليرة!!!</p>"
clean = cleaner.clean(text)
# النتيجة: "السوريه اعلن البنك ان السعر 14 500 ليره"
```

### الميزات

#### ✅ إزالة HTML
```python
text = "<p>هذا <strong>نص</strong> HTML</p>"
# النتيجة: "هذا نص HTML"
```

#### ✅ إزالة التشكيل
```python
text = "السُّورِيَّةُ"
# النتيجة: "السوريه"
```

#### ✅ تطبيع الحروف العربية
```python
text = "إأآ → ا، ة → ه، ى → ي"
# كل أشكال الألف تصبح "ا"
# التاء المربوطة تصبح "ه"
# الياء المقصورة تصبح "ي"
```

#### ✅ تحويل الأرقام العربية
```python
text = "١٤٥٠٠"
# النتيجة: "14500"
```

#### ✅ إزالة الروابط والإيميلات
```python
text = "زوروا https://example.com أو info@example.com"
# النتيجة: "زوروا"
```

#### ✅ إزالة الإيموجي
```python
text = "رائع 😊🎉"
# النتيجة: "رائع"
```

### التنظيف لتحليل المشاعر

```python
# يحتفظ بعلامات التعجب والاستفهام (مهمة للمشاعر)
sentiment_text = cleaner.clean_for_sentiment(text)
```

### إزالة Stopwords

```python
# الحصول على قائمة الكلمات الشائعة
stopwords = TextCleaner.get_arabic_stopwords()

# إزالة من نص
text = "هذا هو السعر في دمشق"
filtered = TextCleaner.remove_stopwords(text, stopwords)
# النتيجة: "السعر دمشق"
```

---

## 2️⃣ NumericExtractor — مستخرج الأرقام

### الاستخدام الأساسي

```python
from src.processing.numeric.extractor import NumericExtractor

extractor = NumericExtractor()

text = "سعر الدولار اليوم 14,500 ليرة بارتفاع 3.5%"
```

### استخراج الأسعار

```python
# سعر واحد
price = extractor.extract_price(text)
# النتيجة: 14500.0

# جميع الأسعار
all_prices = extractor.extract_all_prices(text)
# النتيجة: [14500.0]
```

### استخراج النسب المئوية

```python
# نسبة واحدة
pct = extractor.extract_percentage(text)
# النتيجة: 0.035 (بين 0 و 1)

# جميع النسب
all_pcts = extractor.extract_all_percentages(text)
# النتيجة: [0.035]
```

### استخراج الاتجاه

```python
direction = extractor.extract_direction(text)
# النتيجة: 'up' أو 'down' أو 'stable'

# كلمات الارتفاع: ارتفع، ارتفاع، صعود، زيادة، زاد، طلع
# كلمات الانخفاض: انخفض، انخفاض، هبوط، تراجع، نزل، هبط
# كلمات الاستقرار: استقر، استقرار، ثبات، مستقر
```

### استخراج التغير الكامل

```python
change = extractor.extract_price_change(text)
# النتيجة: {
#     'direction': 'up',
#     'amount': 14500.0,
#     'percentage': 0.035
# }
```

### استخراج سياق العملة

```python
context = extractor.extract_currency_context(text)
# النتيجة: {
#     'price': 14500.0,
#     'change': {...},
#     'percentages': [0.035],
#     'location': 'دمشق'  # إذا وُجد في النص
# }
```

### استخراج جميع المعلومات

```python
all_info = extractor.extract_all(text)
# النتيجة: {
#     'price': 14500.0,
#     'all_prices': [14500.0],
#     'percentage': 0.035,
#     'all_percentages': [0.035],
#     'direction': 'up',
#     'price_change': {...},
#     'all_numbers': [14500.0, 3.5, ...]
# }
```

---

## 3️⃣ ProcessingPipeline — خط المعالجة الكامل

يدمج التنظيف والاستخراج في خطوة واحدة.

### الاستخدام الأساسي

```python
from src.processing.pipeline import ProcessingPipeline

pipeline = ProcessingPipeline()

raw_item = {
    'id': 'news_001',
    'source': 'enab_baladi',
    'timestamp': datetime.now(),
    'raw_text': '<p>ارتفع الدولار إلى 14,850 ليرة بزيادة 2.5%</p>',
    'category': 'economy',
    'language': 'ar'
}

processed = pipeline.process(raw_item)
```

### النتيجة

```python
{
    'id': 'news_001',
    'source': 'enab_baladi',
    'timestamp': ...,
    'original_text': '<p>ارتفع الدولار إلى 14,850 ليرة بزيادة 2.5%</p>',
    'cleaned_text': 'ارتفع الدولار الي 14 850 ليره بزياده 2 5',
    'extracted_price': 14850.0,
    'all_prices': [14850.0],
    'direction': 'up',
    'price_change': {
        'direction': 'up',
        'amount': 14850.0,
        'percentage': 0.025
    },
    'percentage': 0.025,
    'all_percentages': [0.025],
    'all_numbers': [14850.0, 2.5],
    'location': None,
    'category': 'economy',
    'language': 'ar',
    'metadata': {}
}
```

### معالجة دفعة

```python
items = [raw_item1, raw_item2, raw_item3]
processed_batch = pipeline.process_batch(items)
```

### معالجة للتخزين

```python
# بيانات منسقة لقاعدة البيانات
storage_ready = pipeline.process_for_storage(raw_item)

# النتيجة: {
#     'item_id': 'news_001',
#     'source_name': 'enab_baladi',
#     'collected_at': ...,
#     'original_text': ...,
#     'cleaned_text': ...,
#     'extracted_price': 14850.0,
#     'price_direction': 'up',
#     'percentage_change': 0.025,
#     'location': None,
#     'category': 'economy',
#     'language': 'ar',
#     'metadata': {}
# }
```

### معالجة للنماذج ML

```python
# ميزات جاهزة للتعلم الآلي
ml_ready = pipeline.process_for_ml(raw_item)

# النتيجة: {
#     'text_features': {
#         'cleaned_text': ...,
#         'text_length': 10,
#         'has_price': True,
#         'has_direction': True,
#         'has_percentage': True,
#         'location': None
#     },
#     'numeric_features': {
#         'price': 14850.0,
#         'direction': 'up',
#         'percentage': 0.025,
#         'num_prices': 1,
#         'num_percentages': 1,
#         'num_numbers': 2
#     },
#     'metadata': {...}
# }
```

---

## 🧪 الاختبار

```bash
cd ShamIn
python test_processors.py
```

سيعرض:
- اختبار TextCleaner
- اختبار NumericExtractor
- اختبار ProcessingPipeline
- أمثلة حية على المعالجة

---

## 📊 أمثلة عملية

### مثال 1: تنظيف مقال إخباري

```python
cleaner = TextCleaner()

article = """
<div class="article">
    <h1>ارتفاع كبير في سعر الدولار</h1>
    <p>شهدت الأسواق السورية اليوم ارتفاعاً حاداً في سعر صرف الدولار 
    الأمريكي مقابل الليرة السورية، حيث وصل السعر إلى 14,850 ليرة سورية
    في دمشق، بزيادة قدرها 3.5% عن يوم أمس.</p>
    <p>للمزيد: https://example.com</p>
</div>
"""

clean = cleaner.clean(article)
# النتيجة: نص نظيف بدون HTML أو روابط
```

### مثال 2: استخراج من رسالة تلغرام

```python
extractor = NumericExtractor()

telegram_msg = "🔴 عاجل: الدولار في دمشق الآن 14850 ليرة! ارتفاع 2%"

context = extractor.extract_currency_context(telegram_msg)
print(f"السعر: {context['price']}")
print(f"الموقع: {context['location']}")
print(f"الاتجاه: {context['change']['direction']}")
```

### مثال 3: معالجة كاملة

```python
pipeline = ProcessingPipeline()

raw = {
    'id': 'tg_123',
    'source': 'telegram_damascus',
    'raw_text': telegram_msg,
    'timestamp': datetime.now(),
    'language': 'ar'
}

processed = pipeline.process(raw)
storage = pipeline.process_for_storage(processed)

# حفظ في قاعدة البيانات
db.save(storage)
```

---

## 🔧 التخصيص

### إنشاء منظف مخصص

```python
# للتدريب ML (بدون stopwords)
cleaner_ml = TextCleaner(
    remove_diacritics=True,
    normalize_arabic=True,
    remove_punctuation=True,
    remove_stopwords=True  # إزالة الكلمات الشائعة
)

# لتحليل المشاعر (يحتفظ ببعض الترقيم)
cleaner_sentiment = TextCleaner(
    remove_diacritics=True,
    normalize_arabic=True,
    remove_punctuation=False,  # يحتفظ بـ ! و ؟
)
```

### إضافة أنماط استخراج مخصصة

```python
# في NumericExtractor
extractor = NumericExtractor()

# يمكنك إضافة أنماط جديدة عبر توسيع الكلاس
class CustomExtractor(NumericExtractor):
    _CUSTOM_PATTERNS = [
        r'pattern1',
        r'pattern2'
    ]
```

---

## ✅ خلاصة

| المكون | الوظيفة | الاستخدام |
|--------|---------|-----------|
| **TextCleaner** | تنظيف النصوص العربية | قبل التخزين/التحليل |
| **NumericExtractor** | استخراج أسعار وأرقام | من النصوص الخام |
| **ProcessingPipeline** | دمج التنظيف والاستخراج | معالجة شاملة |

**الخطوة التالية**: استخدام هذه المعالجات في تدريب نماذج Naive Bayes للتصنيف! 🚀
