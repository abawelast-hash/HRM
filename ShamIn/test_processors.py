"""
اختبار معالجات النصوص - Text Processors Test

يختبر:
- TextCleaner
- NumericExtractor
- ProcessingPipeline
"""

from src.processing.text.cleaner import TextCleaner
from src.processing.numeric.extractor import NumericExtractor
from src.processing.pipeline import ProcessingPipeline
from datetime import datetime


def test_text_cleaner():
    """اختبار منظف النصوص."""
    print("=" * 70)
    print("اختبار TextCleaner")
    print("=" * 70)
    
    # نص غير نظيف
    dirty_text = """
    <p>السُّورِيَّةُ: أعلن البنك المركزي أن سعر صرف الدولار اليوم هو 14,500 ليرة سورية!!!
    للمزيد زوروا موقعنا: https://example.com أو راسلونا: info@example.com</p>
    
    الأسعار: ١٤٥٠٠ - إرتفاع بنسبة 5% عن الأمس 😊🎉
    """
    
    # إنشاء منظف
    cleaner = TextCleaner(
        remove_diacritics=True,
        normalize_arabic=True,
        remove_punctuation=True,
        remove_urls=True,
        remove_emails=True,
        remove_english_numbers=False,
    )
    
    # تنظيف
    clean_text = cleaner.clean(dirty_text)
    
    print("\n📝 النص الأصلي:")
    print(dirty_text)
    print("\n✨ النص النظيف:")
    print(clean_text)
    print("\n" + "-" * 70 + "\n")
    
    # تنظيف لتحليل المشاعر
    sentiment_text = cleaner.clean_for_sentiment(dirty_text)
    print("💭 نص منظف لتحليل المشاعر (يحتفظ بـ !):")
    print(sentiment_text)
    print("\n" + "=" * 70 + "\n")


def test_numeric_extractor():
    """اختبار مستخرج الأرقام."""
    print("=" * 70)
    print("اختبار NumericExtractor")
    print("=" * 70)
    
    extractor = NumericExtractor()
    
    # أمثلة على نصوص
    texts = [
        "سعر الصرف اليوم في دمشق: الدولار 14,500 ليرة سورية",
        "ارتفع سعر الدولار بنسبة 3.5% ليصل إلى ١٤٨٠٠ ليرة",
        "انخفض السعر أمس من 14,600 إلى 14,400 ل.س",
        "التداول اليوم: USD 14500 - ارتفاع طفيف عن الأمس",
    ]
    
    for i, text in enumerate(texts, 1):
        print(f"\n📝 النص {i}:")
        print(f"   {text}")
        print(f"\n   📊 النتائج:")
        
        # استخراج السياق الكامل
        context = extractor.extract_currency_context(text)
        
        print(f"   💰 السعر: {context['price']}")
        print(f"   📈 التغير: {context['change']}")
        print(f"   📊 النسب: {context['percentages']}")
        print(f"   📍 الموقع: {context['location']}")
        print("-" * 70)
    
    print("\n" + "=" * 70 + "\n")


def test_processing_pipeline():
    """اختبار خط المعالجة الكامل."""
    print("=" * 70)
    print("اختبار ProcessingPipeline")
    print("=" * 70)
    
    pipeline = ProcessingPipeline()
    
    # بيانات خام
    raw_items = [
        {
            'id': 'news_001',
            'source': 'enab_baladi',
            'timestamp': datetime.now(),
            'raw_text': '<p>ارتفع سعر صرف الدولار في دمشق اليوم إلى 14,850 ليرة سورية بزيادة 2.5% عن الأمس</p>',
            'category': 'economy',
            'language': 'ar'
        },
        {
            'id': 'news_002',
            'source': 'reuters',
            'timestamp': datetime.now(),
            'raw_text': 'انخفض الدولار بنسبة 1% في حلب ليصل إلى ١٤٧٠٠ ل.س',
            'category': 'economy',
            'language': 'ar'
        }
    ]
    
    # معالجة
    for item in raw_items:
        print(f"\n📄 معالجة: {item['id']}")
        print(f"   المصدر: {item['source']}")
        print(f"\n   النص الأصلي:")
        print(f"   {item['raw_text']}")
        
        # معالجة
        processed = pipeline.process(item)
        
        print(f"\n   ✨ النص النظيف:")
        print(f"   {processed['cleaned_text']}")
        print(f"\n   📊 البيانات المستخرجة:")
        print(f"   • السعر: {processed['extracted_price']}")
        print(f"   • الاتجاه: {processed['direction']}")
        print(f"   • النسبة: {processed['percentage']}")
        print(f"   • الموقع: {processed['location']}")
        print("-" * 70)
    
    print("\n" + "=" * 70 + "\n")
    
    # معالجة دفعة
    print("🔄 معالجة دفعة...")
    processed_batch = pipeline.process_batch(raw_items)
    print(f"✅ تمت معالجة {len(processed_batch)} عنصر")
    
    # معالجة للتخزين
    print("\n💾 معالجة للتخزين...")
    for item in raw_items[:1]:  # عنصر واحد فقط للعرض
        storage_ready = pipeline.process_for_storage(item)
        print(f"\n   البيانات الجاهزة للتخزين:")
        for key, value in storage_ready.items():
            if key not in ['metadata', 'original_text']:
                print(f"   • {key}: {value}")
    
    # معالجة للـ ML
    print("\n🤖 معالجة للنماذج ML...")
    for item in raw_items[:1]:
        ml_ready = pipeline.process_for_ml(item)
        print(f"\n   الميزات للـ ML:")
        print(f"   Text Features: {ml_ready['text_features']}")
        print(f"   Numeric Features: {ml_ready['numeric_features']}")
    
    print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    print("\n")
    print("🏛️ ShamIn - Text Processors Test")
    print("=" * 70)
    print("\n")
    
    # تشغيل الاختبارات
    test_text_cleaner()
    test_numeric_extractor()
    test_processing_pipeline()
    
    print("\n✅ اكتملت جميع الاختبارات بنجاح!")
    print("\n")
