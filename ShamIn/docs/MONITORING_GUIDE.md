# 🔄 دليل تشغيل ومراقبة محركات الجمع

## نظرة عامة

يوفر نظام **ShamIn** طريقتين لتشغيل ومراقبة محركات جمع البيانات:

1. **لوحة التحكم (Dashboard)** - واجهة مرئية تفاعلية
2. **API Endpoints** - للتحكم البرمجي

---

## 1️⃣ تشغيل عبر لوحة التحكم (الطريقة الموصى بها)

### التشغيل

```bash
# الطريقة الأولى
python ShamIn/run_dashboard.py

# الطريقة الثانية
cd ShamIn
streamlit run src/presentation/dashboard/app.py
```

### الوصول
افتح المتصفح على: **http://localhost:8501**

### الاستخدام

1. اذهب إلى صفحة **"🔄 تشغيل ومراقبة"**
2. اختر محرك الجمع:
   - **📰 RSS**: جمع المقالات من مصادر RSS
   - **💰 الأسعار**: جمع أسعار الصرف من المواقع
   - **📱 تلغرام أسعار**: جمع الأسعار من قنوات تلغرام
   - **📱 تلغرام أخبار**: جمع الأخبار من قنوات تلغرام
   - **🌍 المؤشرات**: جمع المؤشرات الاقتصادية الخارجية
   - **🚀 الكل معاً**: تشغيل جميع المحركات

3. **شاهد النتائج مباشرة**:
   - تقدم الجمع لحظياً
   - عدد المقالات/الأسعار المجموعة
   - نجاح/فشل كل مصدر
   - الإحصائيات النهائية

4. **راقب قاعدة البيانات**:
   - إجمالي المقالات المخزنة
   - البيانات المجموعة اليوم
   - الأسعار المحفوظة

---

## 2️⃣ تشغيل عبر API

### تشغيل الخادم

```bash
# الطريقة الأولى
python ShamIn/run_api.py

# الطريقة الثانية
cd ShamIn
uvicorn src.presentation.api.main:app --reload --host 0.0.0.0 --port 8000
```

### الوصول
- **API Docs**: http://localhost:8000/docs
- **API Base**: http://localhost:8000

### Endpoints المتاحة

#### تشغيل محرك RSS
```bash
curl -X POST http://localhost:8000/tasks/collect/rss
```

**Response:**
```json
{
  "status": "success",
  "task": "rss_collection",
  "timestamp": "2026-03-14T10:30:00",
  "result": {
    "sources_total": 5,
    "sources_successful": 5,
    "articles_collected": 48,
    "details": [...]
  }
}
```

#### تشغيل جمع الأسعار
```bash
curl -X POST http://localhost:8000/tasks/collect/web-prices
```

#### تشغيل جمع تلغرام (الأسعار)
```bash
curl -X POST http://localhost:8000/tasks/collect/telegram-prices
```

#### تشغيل جمع تلغرام (الأخبار)
```bash
curl -X POST http://localhost:8000/tasks/collect/telegram-news
```

#### تشغيل جمع المؤشرات الخارجية
```bash
curl -X POST http://localhost:8000/tasks/collect/external-indicators
```

#### تشغيل جميع المحركات معاً
```bash
curl -X POST http://localhost:8000/tasks/collect/all
```

**Response:**
```json
{
  "status": "success",
  "task": "all_collections",
  "timestamp": "2026-03-14T10:35:00",
  "results": {
    "rss": {...},
    "web_prices": {...},
    "telegram_prices": {...},
    "telegram_news": {...},
    "external_indicators": {...}
  }
}
```

#### الحصول على الإحصائيات الأخيرة
```bash
curl -X GET http://localhost:8000/tasks/stats/recent
```

#### الحصول على آخر سجلات التشغيل
```bash
curl -X GET http://localhost:8000/tasks/logs/recent?limit=50
```

---

## 3️⃣ الجدولة التلقائية (Celery Beat)

للتشغيل التلقائي المجدول:

```bash
# تشغيل Celery Worker
celery -A src.ingestion.scheduler worker --loglevel=info

# تشغيل Celery Beat (للجدولة)
celery -A src.ingestion.scheduler beat --loglevel=info
```

### الجدول الزمني الافتراضي

- **RSS**: كل 15 دقيقة
- **أسعار المواقع**: كل 5 دقائق
- **تلغرام (أسعار)**: كل دقيقة
- **تلغرام (أخبار)**: كل 5 دقائق
- **المؤشرات الخارجية**: كل ساعة

---

## 4️⃣ مثال عملي

### السيناريو: جمع بيانات لأول مرة

```bash
# 1. تشغيل لوحة التحكم
python ShamIn/run_dashboard.py

# في نافذة أخرى: تشغيل API (اختياري)
python ShamIn/run_api.py
```

**في لوحة التحكم:**

1. اذهب إلى **"➕ إدارة المصادر"**
   - أضف مصادر RSS جديدة
   - أضف مواقع أسعار
   - تحقق من إعداد تلغرام

2. اذهب إلى **"🔄 تشغيل ومراقبة"**
   - اضغط **🚀 تشغيل جميع المحركات معاً**
   - شاهد البيانات تُجمع أمامك
   - راقب الإحصائيات

3. تحقق من البيانات:
   - **📡 مصادر البيانات**: عرض جميع المصادر
   - **💱 أسعار الصرف**: الرسوم البيانية
   - **📰 الأحداث والأخبار**: المقالات المجموعة

---

## 5️⃣ الأخطاء الشائعة وحلولها

### ❌ "Telegram API credentials not configured"
**الحل:**
1. سجل في https://my.telegram.org
2. احصل على API_ID و API_HASH
3. أضفهم في `.env`:
   ```
   TELEGRAM_API_ID=your_api_id
   TELEGRAM_API_HASH=your_api_hash
   ```

### ❌ "No RSS sources configured"
**الحل:**
تحقق من ملف `config/sources.yaml` وتأكد من وجود مصادر RSS مفعّلة

### ❌ "Error connecting to PostgreSQL"
**الحل:**
تأكد من تشغيل PostgreSQL:
```bash
docker-compose up -d postgres
```

### ❌ "ImportError: No module named..."
**الحل:**
ثبّت المتطلبات:
```bash
pip install -r requirements.txt
```

---

## 6️⃣ المتطلبات

- **Python 3.11+**
- **PostgreSQL** (للنصوص)
- **InfluxDB** (للأسعار)
- **Redis** (للـ Celery)
- **Streamlit** (للوحة التحكم)
- **FastAPI + Uvicorn** (للـ API)

---

## 7️⃣ الميزات المتاحة

✅ تشغيل كل محرك منفصل
✅ تشغيل جميع المحركات معاً
✅ مراقبة real-time أثناء الجمع
✅ إحصائيات مفصلة لكل مصدر
✅ عرض البيانات المخزنة
✅ API endpoints كاملة
✅ واجهة عربية RTL
✅ معلومات توضيحية (i tooltips)

---

## 8️⃣ التطوير المستقبلي

🔜 WebSocket للـ real-time streaming
🔜 عرض logs مباشر في Dashboard
🔜 رسوم بيانية للأداء
🔜 تنبيهات عند فشل الجمع
🔜 جدولة مخصصة لكل مصدر
🔜 تصدير البيانات (CSV, JSON)

---

## 📞 الدعم

للمساعدة أو الإبلاغ عن مشاكل، راجع:
- `docs/06_دليل_التشغيل.md`
- `TARGET.MD` للخطة الكاملة
- GitHub Issues
