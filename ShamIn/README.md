# 🏛️ ShamIn — نظام التنبؤ الذكي بسعر صرف الليرة السورية

<div dir="rtl">

[![Status](https://img.shields.io/badge/Status-Active%20Development-green.svg)](https://github.com/abawelast-hash/HRM)
[![Version](https://img.shields.io/badge/Version-1.0.0--beta-blue.svg)](https://github.com/abawelast-hash/HRM)
[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-Private-red.svg)](LICENSE)

نظام ذكي متكامل لجمع وتحليل البيانات والتنبؤ بسعر صرف الليرة السورية مقابل الدولار الأمريكي (SYP/USD) باستخدام تقنيات التعلم الآلي والتعلم العميق وتحليل المشاعر.

</div>

---

## 📋 جدول المحتويات

- [نظرة عامة](#-نظرة-عامة)
- [الميزات الرئيسية](#-الميزات-الرئيسية)
- [البنية المعمارية](#-البنية-المعمارية)
- [التقنيات المستخدمة](#-التقنيات-المستخدمة)
- [البدء السريع](#-البدء-السريع)
- [بنية المشروع](#-بنية-المشروع)
- [الحالة الحالية](#-الحالة-الحالية)
- [التوثيق](#-التوثيق)
- [الترخيص](#-الترخيص)

---

## 🎯 نظرة عامة

**ShamIn** يجمع بين مصادر بيانات متعددة (قنوات تلغرام، خلاصات RSS، مواقع ويب، APIs خارجية) مع نماذج تعلم آلي متقدمة للتنبؤ بسعر صرف الليرة السورية.

### الأهداف الرئيسية:
- 📊 **جمع تلقائي** للبيانات من 14+ مصدر موثوق
- 🔍 **تحليل ذكي** للنصوص العربية واستخراج المعلومات
- 🤖 **نماذج ML/DL** متعددة (TFT، XGBoost، LSTM، Naive Bayes)
- 📈 **تنبؤات دقيقة** لآفاق 24 ساعة و72 ساعة
- 🎨 **واجهة شاملة** عربية RTL مع مراقبة real-time
- 🔔 **تنبيهات ذكية** عند التغيرات الكبيرة

---

## ✨ الميزات الرئيسية

### 📡 جمع البيانات (Data Collection)
- ✅ **RSS Collector** - جمع من 5 مصادر إخبارية (عنب بلدي، رويترز، سانا، العربي الجديد، الجزيرة)
- ✅ **Web Scraper** - جمع أسعار من 3 مواقع (sp-today، investing.com، البنك المركزي)
- ⏳ **Telegram Collector** - جمع من 6 قنوات (أسعار + أخبار)
- ⏳ **External APIs** - مؤشرات خارجية (ذهب، نفط، DXY)
- ✅ **Retry Logic** - إعادة محاولة تلقائية مع exponential backoff
- ✅ **Deduplication** - منع التكرار بـ MD5 hashing
- ✅ **Storage Integration** - حفظ تلقائي في PostgreSQL و InfluxDB

### 🔧 معالجة النصوص (Text Processing)
- ✅ **TextCleaner** - تنظيف شامل للنصوص العربية:
  - إزالة HTML tags and entities
  - إزالة التشكيل (diacritics)
  - تطبيع الحروف (إأآ → ا، ة → ه، ى → ي)
  - تحويل الأرقام العربية → إنجليزية
  - إزالة الروابط والإيميلات والإيموجي
  - دعم stopwords (60+ كلمة عربية)

- ✅ **NumericExtractor** - استخراج ذكي للمعلومات الرقمية:
  - استخراج أسعار الصرف (8 أنماط مختلفة)
  - استخراج النسب المئوية (3 أنماط)
  - تحديد اتجاه السعر (ارتفاع/انخفاض/استقرار)
  - كشف الموقع الجغرافي (دمشق، حلب، إدلب...)
  - استخراج السياق الكامل

- ✅ **ProcessingPipeline** - خط معالجة متكامل:
  - معالجة للتخزين (DB-ready)
  - معالجة لنماذج ML (features extraction)
  - معالجة لتحليل المشاعر
  - معالجة دفعات مع error handling

### 🎨 لوحة التحكم (Dashboard)
- ✅ **10 صفحات متكاملة** عربية RTL:
  1. 🏠 نظرة عامة - حالة الخدمات والإحصائيات
  2. 📡 مصادر البيانات - عرض جميع المصادر
  3. ➕ إدارة المصادر - إضافة/تعديل/حذف ديناميكي
  4. 🔄 تشغيل ومراقبة - تحكم وعرض real-time
  5. 💱 أسعار الصرف - رسوم بيانية تفاعلية
  6. 🤖 نماذج التنبؤ - وصف النماذج وأدائها
  7. 📰 الأحداث والأخبار - تصنيف وتحليل
  8. 📊 أداء النظام - مقاييس ومؤشرات
  9. 🔔 التنبيهات - قواعد ومراقبة
  10. ⚙️ الإعدادات - إعدادات عامة

- ✅ **60+ Info Tooltips** - شرح تفصيلي لكل عنصر
- ✅ **Real-time Monitoring** - مشاهدة الجمع مباشرة
- ✅ **Interactive Charts** - رسوم بيانية تفاعلية (Plotly)

### 🚀 API Endpoints
- ✅ **Manual Task Execution**:
  - `POST /tasks/collect/rss` - تشغيل جمع RSS
  - `POST /tasks/collect/web-prices` - تشغيل جمع الأسعار
  - `POST /tasks/collect/all` - تشغيل جميع المحركات
- ✅ **Statistics & Monitoring**:
  - `GET /tasks/stats/recent` - إحصائيات أخيرة
  - `GET /tasks/logs/recent` - سجلات التشغيل
- ⏳ **Predictions API** (قيد التطوير)
- ⏳ **Events API** (قيد التطوير)

### 🔄 الجدولة التلقائية (Celery Beat)
- ✅ **RSS**: كل 15 دقيقة
- ✅ **أسعار المواقع**: كل 5 دقائق
- ⏳ **تلغرام (أسعار)**: كل دقيقة
- ⏳ **تلغرام (أخبار)**: كل 5 دقائق
- ⏳ **المؤشرات الخارجية**: كل ساعة

---

## 🏗️ البنية المعمارية

```
┌─────────────────────────────────────────────────────────────────┐
│                     Data Collection Layer                        │
├──────────────┬──────────────┬──────────────┬────────────────────┤
│ RSS Feeds    │ Web Scraping │ Telegram     │ External APIs      │
│ (5 sources)  │ (3 websites) │ (6 channels) │ (Gold, Oil, DXY)   │
└──────────────┴──────────────┴──────────────┴────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                   Processing & Storage Layer                     │
├──────────────┬──────────────┬──────────────┬────────────────────┤
│ TextCleaner  │ Numeric      │ PostgreSQL   │ InfluxDB           │
│ (Arabic NLP) │ Extractor    │ (Texts)      │ (Time-series)      │
└──────────────┴──────────────┴──────────────┴────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    ML/DL Models Layer                            │
├──────────────┬──────────────┬──────────────┬────────────────────┤
│ Naive Bayes  │ HLT          │ XGBoost      │ TFT (Transformer)  │
│ (Sentiment)  │ (Trend)      │ (Gradient)   │ (Deep Learning)    │
└──────────────┴──────────────┴──────────────┴────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                   Presentation Layer                             │
├──────────────┬──────────────┬──────────────┬────────────────────┤
│ Dashboard    │ FastAPI      │ Alerts       │ Reports            │
│ (Streamlit)  │ (REST API)   │ (Email/SMS)  │ (PDF/Excel)        │
└──────────────┴──────────────┴──────────────┴────────────────────┘
```

---

## 🛠️ التقنيات المستخدمة

| الطبقة | التقنية |
|--------|---------|
| **ML/DL Core** | PyTorch, PyTorch Lightning, PyTorch Forecasting (TFT) |
| **Baseline Models** | XGBoost, scikit-learn, statsmodels (HLT) |
| **Arabic NLP** | Custom (TextCleaner, NumericExtractor) |
| **Data Collection** | feedparser, requests, BeautifulSoup, Telethon |
| **Storage** | PostgreSQL 16, InfluxDB 2.7, Redis 7, MinIO |
| **Task Queue** | Celery + Celery Beat |
| **API** | FastAPI + Uvicorn |
| **Dashboard** | Streamlit + Plotly |
| **Deployment** | Docker + Docker Compose |
| **Monitoring** | Custom health checks, logging |

---

## 🚀 البدء السريع

### المتطلبات
- **Python 3.11+**
- **Docker & Docker Compose**
- **Git**

### 1. التثبيت

```bash
# استنساخ المستودع
git clone https://github.com/abawelast-hash/HRM.git
cd HRM/ShamIn

# إنشاء بيئة افتراضية
python -m venv venv

# تفعيل البيئة
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# تثبيت المتطلبات
pip install -r requirements.txt
```

### 2. الإعدادات

```bash
# نسخ ملف البيئة
copy .env.example .env   # Windows
# أو
cp .env.example .env     # Linux/Mac

# تحرير .env وإضافة:
# - بيانات اعتماد PostgreSQL
# - بيانات اعتماد InfluxDB
# - Telegram API credentials (اختياري)
```

### 3. تشغيل البنية التحتية

```bash
# تشغيل Docker containers
docker-compose up -d

# التحقق من الخدمات
docker-compose ps

# تهيئة قواعد البيانات
python scripts/setup_db.py
python scripts/setup_influxdb.py
```

### 4. تشغيل التطبيق

#### الطريقة الأسهل (Windows):
```cmd
start.bat
# اختر [1] لوحة التحكم
```

#### أو يدوياً:
```bash
# تشغيل Dashboard
python run_dashboard.py
# افتح: http://localhost:8501

# تشغيل API (في نافذة أخرى)
python run_api.py
# افتح: http://localhost:8000/docs

# تشغيل Celery Worker (اختياري)
celery -A src.ingestion.scheduler worker --loglevel=info

# تشغيل Celery Beat (اختياري)
celery -A src.ingestion.scheduler beat --loglevel=info
```

---

## 📁 بنية المشروع

```
ShamIn/
├── 📄 README.md                    # هذا الملف
├── 📄 QUICKSTART.md               # دليل البدء السريع
├── 📄 requirements.txt            # المتطلبات
├── 📄 docker-compose.yml          # تكوين Docker
├── 📄 .env.example                # مثال ملف البيئة
├── 📄 start.bat                   # مشغل Windows
├── 📄 run_dashboard.py            # مشغل Dashboard
├── 📄 run_api.py                  # مشغل API
├── 📄 test_processors.py          # اختبار المعالجات
│
├── 📁 config/                     # إعدادات YAML
│   ├── sources.yaml               # مصادر البيانات
│   ├── model_config.yaml          # إعدادات النماذج
│   ├── alerts.yaml                # قواعد التنبيهات
│   └── settings.yaml              # إعدادات عامة
│
├── 📁 src/                        # الكود المصدري
│   ├── 📁 ingestion/              # جمع البيانات
│   │   ├── scheduler.py           # Celery tasks
│   │   └── collectors/
│   │       ├── rss_collector.py   # ✅ جامع RSS
│   │       ├── web_scraper.py     # ✅ جامع أسعار المواقع
│   │       └── telegram_collector.py  # ⏳ جامع تلغرام
│   │
│   ├── 📁 processing/             # معالجة البيانات
│   │   ├── pipeline.py            # ✅ خط المعالجة
│   │   ├── text/
│   │   │   └── cleaner.py         # ✅ منظف النصوص العربية
│   │   └── numeric/
│   │       └── extractor.py       # ✅ مستخرج الأرقام
│   │
│   ├── 📁 prediction/             # نماذج التنبؤ
│   │   ├── models/                # ⏳ نماذج ML/DL
│   │   └── training/              # ⏳ التدريب
│   │
│   ├── 📁 storage/                # قواعد البيانات
│   │   ├── relational_db.py       # ✅ PostgreSQL
│   │   ├── timeseries_db.py       # ✅ InfluxDB
│   │   └── model_registry.py      # ⏳ MinIO
│   │
│   ├── 📁 presentation/           # العرض
│   │   ├── dashboard/
│   │   │   └── app.py             # ✅ Dashboard (10 صفحات)
│   │   └── api/
│   │       ├── main.py            # ✅ FastAPI
│   │       └── routes/
│   │           └── tasks.py       # ✅ Manual execution
│   │
│   ├── 📁 monitoring/             # المراقبة
│   │   ├── health_checker.py      # ⏳ فحص صحة الخدمات
│   │   └── drift_detector.py      # ⏳ كشف الانحراف
│   │
│   └── 📁 utils/                  # أدوات مساعدة
│       ├── config.py              # ✅ تحميل الإعدادات
│       └── logging.py             # ✅ السجلات
│
├── 📁 data/                       # بيانات محلية
│   ├── models/                    # النماذج المدربة
│   ├── processed/                 # بيانات معالجة
│   └── raw/                       # بيانات خام
│
├── 📁 docs/                       # التوثيق
│   ├── MONITORING_GUIDE.md        # ✅ دليل المراقبة
│   ├── TEXT_PROCESSORS_GUIDE.md   # ✅ دليل المعالجات
│   ├── 01_شجرة_الملفات.md        # شجرة الملفات
│   ├── 02_مرجع_المتغيرات_والدوال.md  # مرجع كامل
│   └── ...                        # توثيقات أخرى
│
├── 📁 scripts/                    # نصوص الإعداد
│   ├── setup_db.py                # إعداد PostgreSQL
│   ├── setup_influxdb.py          # إعداد InfluxDB
│   └── setup_minio.py             # إعداد MinIO
│
└── 📁 tests/                      # الاختبارات
    └── __init__.py
```

**الرموز:**
- ✅ = مكتمل وجاهز
- ⏳ = قيد التطوير
- 📄 = ملف
- 📁 = مجلد

---

## 📊 الحالة الحالية

### ✅ المكتمل (Phase 1 - جزئي)

| المكون | الحالة | الوصف |
|--------|--------|-------|
| **RSS Collector** | ✅ 100% | جمع من 5 مصادر، retry logic، deduplication، storage |
| **Web Scraper** | ✅ 100% | 3 مواقع، multiple strategies، InfluxDB storage |
| **TextCleaner** | ✅ 100% | 13 وظيفة، دعم كامل للعربية، stopwords |
| **NumericExtractor** | ✅ 100% | 12 وظيفة، 8 أنماط للأسعار، context extraction |
| **ProcessingPipeline** | ✅ 100% | معالجة شاملة، DB/ML ready |
| **Dashboard** | ✅ 100% | 10 صفحات، 60+ tooltips، RTL |
| **Source Management** | ✅ 100% | إضافة/تعديل/حذف ديناميكي |
| **Real-time Monitoring** | ✅ 100% | عرض مباشر، إحصائيات |
| **API Endpoints** | ✅ 80% | Manual execution، stats، logs |
| **Celery Integration** | ✅ 80% | RSS + Web متصلين |
| **PostgreSQL** | ✅ 100% | Schema، storage |
| **InfluxDB** | ✅ 100% | Time-series storage |

### ⏳ قيد التطوير

| المكون | الأولوية | الحالة |
|--------|---------|--------|
| **Telegram Collector** | 🔴 عالية | يتطلب API credentials |
| **External APIs** | 🟡 متوسطة | قيد التصميم |
| **Sentiment Analyzer** | 🔴 عالية | يتطلب 1000 نص للتدريب |
| **Event Classifier** | 🔴 عالية | Naive Bayes - 5 فئات |
| **HLT Model** | 🟡 متوسطة | Holt Linear Trend |
| **XGBoost Model** | 🟡 متوسطة | Feature engineering |
| **TFT Model** | 🟢 منخفضة | Phase 3 |
| **Alerts System** | 🟡 متوسطة | Email/SMS notifications |

### 📈 الإحصائيات

- **إجمالي الأسطر**: ~5,000+ سطر كود Python
- **عدد الوظائف**: 80+ وظيفة
- **عدد الملفات**: 50+ ملف
- **التغطية**: Phase 1 (50%)

---

## 📚 التوثيق

### دلائل الاستخدام
- [🚀 QUICKSTART.md](../QUICKSTART.md) - البدء السريع (10 دقائق)
- [🔄 MONITORING_GUIDE.md](docs/MONITORING_GUIDE.md) - دليل المراقبة والتشغيل
- [🔧 TEXT_PROCESSORS_GUIDE.md](docs/TEXT_PROCESSORS_GUIDE.md) - دليل معالجات النصوص
- [🎯 TARGET.MD](../TARGET.MD) - الخطة الكاملة والأهداف (6000+ سطر)

### التوثيق الفني
- [📁 01_شجرة_الملفات.md](docs/01_شجرة_الملفات.md) - بنية المشروع الكاملة
- [📖 02_مرجع_المتغيرات_والدوال.md](docs/02_مرجع_المتغيرات_والدوال.md) - مرجع شامل
- [⚙️ 03_التقنيات_المستخدمة.md](docs/03_التقنيات_المستخدمة.md) - Tech stack
- [🔄 04_مسار_البيانات.md](docs/04_مسار_البيانات.md) - Data flow
- [🏗️ 05_الهندسة_المعمارية.md](docs/05_الهندسة_المعمارية.md) - Architecture
- [📘 06_دليل_التشغيل.md](docs/06_دليل_التشغيل.md) - دليل التشغيل

---

## 🎯 خريطة الطريق

### المرحلة 1 (0-3 أشهر) - الأساسيات ✅ 50%
- [x] البنية التحتية (Docker)
- [x] جامعي البيانات الأساسيين (RSS, Web)
- [x] معالجات النصوص (TextCleaner, NumericExtractor)
- [x] لوحة التحكم الأساسية
- [ ] جامع تلغرام
- [ ] نماذج Naive Bayes (Sentiment + Events)
- [ ] نماذج HLT + XGBoost

### المرحلة 2 (3-6 أشهر) - التحسين
- [ ] تحسين جودة البيانات
- [ ] Feature Engineering متقدم
- [ ] Ensemble Models
- [ ] نظام التنبيهات
- [ ] API كاملة

### المرحلة 3 (6-12 أشهر) - التقنيات المتقدمة
- [ ] TFT (Temporal Fusion Transformer)
- [ ] LSTM/GRU Models
- [ ] Hybrid Ensemble
- [ ] Auto-tuning (Optuna)
- [ ] Production Monitoring

### المرحلة 4+ (12-18 أشهر) - التوسع
- [ ] Multi-currency support
- [ ] Real-time predictions
- [ ] Mobile app
- [ ] Advanced analytics

---

## 🤝 المساهمة

هذا مشروع خاص. للاستفسارات أو التعاون: [اتصل بالمطور]

---

## 📄 الترخيص

**Private — All rights reserved.**

جميع الحقوق محفوظة © 2026

---

## 📞 الدعم

للمساعدة أو الإبلاغ عن مشاكل:
1. راجع [QUICKSTART.md](../QUICKSTART.md) للبدء السريع
2. راجع [MONITORING_GUIDE.md](docs/MONITORING_GUIDE.md) للمراقبة
3. راجع [TARGET.MD](../TARGET.MD) للخطة الكاملة
4. تحقق من [Issues](https://github.com/abawelast-hash/HRM/issues)

---

<div align="center">

**صُنع بـ ❤️ للمساعدة في فهم وتوقع سعر صرف الليرة السورية**

[![GitHub](https://img.shields.io/badge/GitHub-abawelast--hash-blue.svg)](https://github.com/abawelast-hash/HRM)

</div>
