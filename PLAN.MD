# خطة إنشاء تطبيق التنبؤ بأسعار الصرف — SYP/USD Forecaster
## الإصدار 2.0 — محدّث بناءً على تحليل ACTION-main

---

## مقدمة: الأساس والمنهجية

### السياق

هذه الخطة تبني على الدروس المستفادة من مشروع **ACTION-main** (نظام بولندي للتنبؤ بأسعار الأسهم باستخدام Temporal Fusion Transformer). تم تحليل المشروع بشكل شامل واستخراج:

- **70% من الكود قابل لإعادة الاستخدام المباشر** (TFT، Optuna، PyTorch Lightning، Quantile Loss)
- **أفضل 5 ممارسات مثبتة**: Gap في التقسيم، Log1p Transform، Quantile Predictions، Async fetching، Batch size estimation
- **التحديات المحددة** التي تحتاج معالجة للسوق السوري

### الأسس العلمية

المشروع يستند إلى منهجية مثبتة في الأدبيات المحكمة:

1. **النهج الهجين المتماثل** (Symmetry 2020, 12, 1553)
2. **إطار دمج البيانات المهيكلة وغير المهيكلة** (Ding et al., 2025, arXiv:2408.13214v2)
3. **تفكيك الإشارة التكيفي OCEEMDAN** (Tang & Xie, 2025, IJFS 13(3), 151)
4. **هندسة الميزات ثنائية المرحلة + FCM** (Wang et al., 2023, Digital Signal Processing 143)
5. **نماذج TFT للتنبؤ متعدد الأفق** (Lim et al., 2021, International Journal of Forecasting)

### استراتيجية التنفيذ

- **البداية من Baseline بسيط** (XGBoost + HLT) → هدف MAPE < 5%
- **التطور التدريجي** نحو النماذج المعقدة (DL → Hybrid → TFT)
- **استخدام كود ACTION-main كأساس** مع التعديلات المطلوبة للسوق السوري
- **القياس المستمر** لكل مرحلة قبل الانتقال للتالية

---

## ملحق: ما نستعيره من ACTION-main

قبل البدء، نحدد الكود القابل لإعادة الاستخدام المباشر من ACTION-main:

### مكونات جاهزة للاستخدام (استيراد مباشر)

| المكون | الملف الأصلي | الاستخدام | التعديل المطلوب |
|---|---|---|---|
| **TFT Model** | `old_code/scripts/model.py` | بناء النموذج | تغيير المتغيرات (إزالة Sector، Volume) |
| **Quantile Loss** | `old_code/scripts/utils/model_config.py` | دالة الخسارة | زيادة الكميات إلى [0.05, 0.25, 0.5, 0.75, 0.95] |
| **Optuna Integration** | `old_code/scripts/train.py` | ضبط المعلمات | توسيع نطاق البحث |
| **Batch Size Estimator** | `old_code/scripts/utils/batch_size_estimator.py` | منع OOM | استخدام مباشر |
| **Config Manager** | `old_code/scripts/config_manager.py` | إدارة الإعدادات | تعديل مسارات |
| **Async Fetcher Pattern** | `old_code/scripts/data_fetcher.py` | جمع بيانات | استبدال yfinance بـ Scrapers |
| **TorchNormalizer** | `old_code/scripts/preprocessor.py` | التطبيع | استخدام مباشر |
| **Backtesting Framework** | `old_code/app/benchmark_utils.py` | التقييم | استخدام مباشر |
| **Plotly Charts** | `old_code/app/plot_utils.py` | الرسم | تعديل العناوين للعربية |
| **Streamlit Structure** | `old_code/app/app.py` | الواجهة | إعادة هيكلة بالعربية |

### تعديلات ضرورية (من تحليل نقاط الضعف)

#### 1. معالجة الفجوات الزمنية
```python
# في preprocessor.py — إضافة استيفاء كامل:
def handle_gaps(df):
    """معالجة فجوات نهاية الأسبوع والعطل السورية"""
    # السوق السوري: عطلة جمعة-سبت (وليس سبت-أحد)
    full_index = pd.date_range(start=df.index.min(), end=df.index.max(), freq='H')
    df = df.reindex(full_index)
    
    # استيفاء تربيعي للفجوات القصيرة (1-3 أيام)
    df['Close'] = df['Close'].interpolate(method='quadratic', limit=72)
    
    # علامة على القيم المستوفاة (كميزة إضافية)
    df['is_interpolated'] = df['Close'].isna().shift(1).fillna(False)
    
    return df
```

#### 2. دعم البيانات الساعية
```yaml
# config.yaml المُعدَّل للفوركس الساعي:
data:
  frequency: 'H'               # ساعي بدلاً من يومي
  max_encoder_length: 168      # 7 أيام × 24 ساعة
  max_prediction_length: 24    # 24 ساعة قادمة
  gap_hours: 24                # فجوة 24 ساعة (بدلاً من 10 أيام)
  
model:
  time_varying_known_categoricals:
    - Hour                     # 0-23
    - Day_of_Week              # 0-6
    - is_weekend               # جمعة/سبت
    - is_holiday               # العطل السورية
```

#### 3. استبدال الميزات
```python
# feature_engineer.py — ميزات الفوركس السوري:

# حذف هذه (غير مناسبة):
# - Volume, VWAP (لا يوجد حجم موثوق)
# - Sector (لا معنى له في الفوركس)
# - BB_upper فقط (نحتاج الشريط الكامل)

# إضافة هذه (خاصة بالفوركس):
def add_forex_features(df):
    """ميزات خاصة بسعر صرف الليرة السورية"""
    
    # 1. ميزات جلسات التداول العالمية
    df['session_damascus'] = ((df['Hour'] >= 9) & (df['Hour'] < 15)).astype(int)
    df['session_london'] = ((df['Hour'] >= 8) & (df['Hour'] < 16)).astype(int)
    df['session_newyork'] = ((df['Hour'] >= 13) & (df['Hour'] < 21)).astype(int)
    df['session_overlap'] = (df['session_damascus'] & df['session_london']).astype(int)
    
    # 2. مؤشرات خارجية (مُجمّعة مسبقاً)
    # تُضم من external_indicators في InfluxDB
    df['gold_price_pct'] = df['gold_usd'].pct_change()
    df['oil_price_pct'] = df['brent_usd'].pct_change()
    df['dxy_pct'] = df['dxy'].pct_change()
    df['lbp_rate_pct'] = df['usd_lbp'].pct_change()
    
    # 3. مؤشرات المشاعر (من NLP Pipeline)
    df['sentiment_score'] = df['sentiment_score'].fillna(0)
    df['event_weight'] = df['event_weight'].fillna(0)
    
    # 4. ميزات زمنية سورية
    df['is_friday'] = (df['Day_of_Week'] == 4).astype(int)
    df['is_saturday'] = (df['Day_of_Week'] == 5).astype(int)
    df['is_weekend'] = (df['is_friday'] | df['is_saturday']).astype(int)
    df['is_holiday'] = df['Date'].isin(SYRIA_HOLIDAYS).astype(int)
    df['is_ramadan'] = df['Date'].apply(is_in_ramadan).astype(int)
    
    # 5. Bollinger Bands كاملة (وليس upper فقط)
    bb_middle = df['Close'].rolling(20).mean()
    bb_std = df['Close'].rolling(20).std()
    df['BB_upper'] = bb_middle + 2 * bb_std
    df['BB_middle'] = bb_middle
    df['BB_lower'] = bb_middle - 2 * bb_std
    df['BB_position'] = (df['Close'] - df['BB_lower']) / (df['BB_upper'] - df['BB_lower'])
    
    # 6. مؤشرات فنية إضافية
    df['ATR'] = calculate_atr(df, period=14)  # متوسط المدى الحقيقي
    df['ADX'] = calculate_adx(df, period=14)  # مؤشر الاتجاه
    df['OBV'] = df['Volume'].cumsum() if 'Volume' in df else 0  # حجم التوازن
    
    return df
```

### أفضل الممارسات المُثبتة (نُطبّقها كما هي)

1. **Gap في التقسيم** (10 أيام / 24 ساعة): يمنع Data Leakage
2. **Log1p Transform**: يُحسِّن توزيع البيانات المائلة
3. **Quantile Predictions**: توقع نطاقات ثقة بدلاً من نقطة واحدة
4. **Async Fetching**: جمع بيانات متوازي من مصادر متعددة
5. **Automatic Batch Size**: يمنع OOM ويُحسِّن استخدام GPU

---

## المرحلة 0: التهيئة والإعداد (الأسبوع 1-2)

### 0.1 إعداد بيئة التطوير

- [ ] تثبيت Python 3.11+ (متوافق مع PyTorch 2.3+)
- [ ] **استنساخ ACTION-main كنقطة بداية**:
  ```bash
  git clone https://github.com/original/ACTION-main.git reference/
  # استخراج الكود القابل لإعادة الاستخدام
  ```
- [ ] إنشاء مستودع Git جديد للمشروع السوري
- [ ] تهيئة `.gitignore` (بايثون + Jupyter + بيانات حساسة)
- [ ] إنشاء بيئة افتراضية `venv`
- [ ] إنشاء `requirements.txt` (استيراد من ACTION-main + إضافات):
  ```txt
  # من ACTION-main (أساسي)
  torch>=2.3.0
  pytorch-lightning>=2.2.0
  pytorch-forecasting>=1.0.0
  optuna>=3.5.0
  pandas>=2.0
  streamlit>=1.30.0
  plotly>=5.18.0
  PyYAML
  
  # إضافات للمشروع السوري
  telethon>=1.34.0           # Telegram
  feedparser>=6.0.10         # RSS
  beautifulsoup4>=4.12.0     # Web Scraping
  selenium>=4.16.0           # Dynamic Scraping
  fastapi>=0.109.0           # API Backend
  uvicorn>=0.27.0            # ASGI Server
  celery>=5.3.4              # Task Queue
  redis>=5.0.1               # Message Broker
  psycopg2-binary>=2.9.9     # PostgreSQL
  influxdb-client>=1.39.0    # Time-Series DB
  minio>=7.2.3               # Object Storage
  scikit-learn>=1.4.0        # Baseline Models
  xgboost>=2.0.3             # XGBoost
  statsmodels>=0.14.1        # HLT/ARIMA
  transformers>=4.37.0       # LLMs (مرحلة متقدمة)
  arabic-reshaper>=3.0.0     # دعم العربية
  python-bidi>=0.4.2         # RTL Support
  camel-tools>=1.5.2         # NLP عربي
  farasasegmenter>=0.0.14    # تقطيع عربي
  ```
- [ ] إنشاء `.env.example` لبيانات الاعتماد:
  ```env
  # Telegram
  TELEGRAM_API_ID=
  TELEGRAM_API_HASH=
  
  # Databases
  POSTGRES_URL=postgresql://user:pass@localhost:5432/forex_db
  INFLUXDB_URL=http://localhost:8086
  INFLUXDB_TOKEN=
  INFLUXDB_ORG=forex_org
  INFLUXDB_BUCKET=exchange_rates
  
  # Redis
  REDIS_URL=redis://localhost:6379/0
  
  # MinIO
  MINIO_ENDPOINT=localhost:9000
  MINIO_ACCESS_KEY=
  MINIO_SECRET_KEY=
  
  # APIs (اختياري)
  TWITTER_BEARER_TOKEN=
  ```
- [ ] إنشاء هيكل المجلدات (مُحسّن بناءً على ACTION-main):

```
syp-usd-forecaster/          ← اسم المشروع
├── config/                  ← ملفات الإعدادات (YAML)
│   ├── settings.yaml        ← إعدادات عامة
│   ├── sources.yaml         ← تعريف المصادر
│   ├── model_config.yaml    ← إعدادات TFT (من ACTION-main)
│   └── alerts.yaml          ← قواعد التنبيهات
│
├── src/                     ← الكود الأساسي
│   ├── __init__.py
│   │
│   ├── ingestion/           ← طبقة جمع البيانات (مُحسّنة من ACTION-main)
│   │   ├── __init__.py
│   │   ├── scheduler.py     ← Celery Beat Scheduler
│   │   ├── raw_schema.py    ← Pydantic schemas
│   │   └── collectors/
│   │       ├── __init__.py
│   │       ├── base.py      ← Base Collector Class
│   │       ├── rss_collector.py
│   │       ├── telegram_collector.py
│   │       ├── web_scraper.py
│   │       └── api_collector.py
│   │
│   ├── processing/          ← طبقة المعالجة (مُوسّعة من ACTION-main)
│   │   ├── __init__.py
│   │   ├── pipeline.py      ← Pipeline رئيسي
│   │   ├── text/
│   │   │   ├── __init__.py
│   │   │   ├── cleaner.py
│   │   │   ├── tokenizer.py
│   │   │   ├── classifier.py      ← Event Classification
│   │   │   ├── sentiment.py       ← Sentiment Analysis
│   │   │   └── embeddings.py      ← Word2Vec/GloVe/FastText
│   │   ├── numeric/
│   │   │   ├── __init__.py
│   │   │   ├── extractor.py       ← استخراج الأسعار
│   │   │   └── interpolation.py   ← استيفاء الفجوات (جديد)
│   │   └── features/
│   │       ├── __init__.py
│   │       ├── engineer.py        ← هندسة الميزات (من ACTION-main معدّل)
│   │       ├── weights.py         ← أوزان ديناميكية
│   │       ├── aggregator.py      ← تجميع نوافذ زمنية
│   │       ├── selector.py        ← Mutual Information
│   │       └── store.py           ← Feature Store
│   │
│   ├── prediction/          ← طبقة النماذج (من ACTION-main موسّعة)
│   │   ├── __init__.py
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── baseline.py        ← XGBoost/RandomForest
│   │   │   ├── time_series.py     ← HLT/SES/ARIMA
│   │   │   ├── tft_model.py       ← CustomTFT (من ACTION-main)
│   │   │   └── deep_learning.py   ← CNN/RNN/LSTM للمشاعر
│   │   ├── training/
│   │   │   ├── __init__.py
│   │   │   ├── trainer.py         ← PyTorch Lightning Trainer
│   │   │   ├── evaluator.py       ← المقاييس
│   │   │   ├── backtester.py      ← Backtesting (من ACTION-main)
│   │   │   └── optimizer.py       ← Optuna (من ACTION-main)
│   │   ├── inference/
│   │   │   ├── __init__.py
│   │   │   ├── predictor.py       ← Hybrid Predictor
│   │   │   └── explainer.py       ← SHAP/Grad-CAM
│   │   └── feedback.py            ← حلقة التغذية الراجعة
│   │
│   ├── storage/             ← طبقة التخزين
│   │   ├── __init__.py
│   │   ├── timeseries_db.py       ← InfluxDB Client
│   │   ├── relational_db.py       ← PostgreSQL (SQLAlchemy)
│   │   ├── object_store.py        ← MinIO Client
│   │   └── model_registry.py      ← Model Versioning
│   │
│   ├── presentation/        ← طبقة العرض
│   │   ├── __init__.py
│   │   ├── dashboard/
│   │   │   ├── __init__.py
│   │   │   ├── app.py             ← Streamlit Main (من ACTION-main معدّل)
│   │   │   ├── plot_utils.py      ← Plotly Charts (من ACTION-main)
│   │   │   └── pages/
│   │   │       ├── prediction.py
│   │   │       ├── events.py
│   │   │       ├── performance.py
│   │   │       └── alerts.py
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── main.py            ← FastAPI App
│   │   │   ├── routes/
│   │   │   │   ├── predictions.py
│   │   │   │   ├── rates.py
│   │   │   │   ├── events.py
│   │   │   │   ├── sentiment.py
│   │   │   │   └── models.py
│   │   │   └── schemas/           ← Pydantic Models
│   │   │       ├── prediction.py
│   │   │       ├── rate.py
│   │   │       └── event.py
│   │   └── alerts/
│   │       ├── __init__.py
│   │       └── notifier.py        ← Telegram Bot
│   │
│   ├── monitoring/          ← طبقة المراقبة
│   │   ├── __init__.py
│   │   ├── health_checker.py
│   │   ├── drift_detector.py
│   │   └── quality_checker.py
│   │
│   └── utils/               ← أدوات مساعدة (من ACTION-main)
│       ├── __init__.py
│       ├── config.py              ← Config Loader
│       ├── logging.py             ← Logging Setup
│       ├── batch_size_estimator.py ← من ACTION-main
│       └── validation_utils.py    ← من ACTION-main
│
├── data/                    ← البيانات المحلية
│   ├── raw/                 ← بيانات خام (CSV مؤقت)
│   ├── processed/           ← بيانات معالجة
│   └── models/              ← نماذج محفوظة (.pth)
│       ├── checkpoints/
│       └── normalizers/     ← TorchNormalizer (.pkl)
│
├── reference/               ← مرجع ACTION-main
│   └── ACTION-main/         ← الكود الأصلي
│
├── notebooks/               ← Jupyter Notebooks للتجريب
│   ├── 01_data_exploration.ipynb
│   ├── 02_feature_engineering.ipynb
│   ├── 03_model_experiments.ipynb
│   └── 04_backtesting.ipynb
│
├── tests/                   ← اختبارات وحدة
│   ├── __init__.py
│   ├── test_collectors.py
│   ├── test_processors.py
│   ├── test_models.py
│   └── test_api.py
│
├── scripts/                 ← سكريبتات مساعدة
│   ├── setup_db.py          ← إنشاء جداول
│   ├── migrate_data.py      ← ترحيل بيانات
│   ├── train_model.py       ← نقطة دخول التدريب (من ACTION-main)
│   └── backfill_data.py     ← ملء بيانات تاريخية
│
├── docs/                    ← التوثيق
│   ├── architecture.md
│   ├── api_docs.md
│   ├── decisions.md         ← قرارات التصميم
│   └── papers/              ← الأوراق البحثية المرجعية
│
├── docker-compose.yml       ← خدمات البنية التحتية
├── Dockerfile               ← حاوية التطبيق
├── .env.example
├── .gitignore
├── requirements.txt
├── README.md
├── ACTION-main.md           ← التحليل الشامل (مرجع)
├── TARGET.MD                ← المتطلبات الكاملة
└── PLAN.MD                  ← هذه الخطة
```

### 0.2 إعداد البنية التحتية

- [ ] كتابة `docker-compose.yml` (خدمات البنية التحتية):
  ```yaml
  version: '3.8'
  
  services:
    postgres:
      image: postgres:16-alpine
      container_name: forex_postgres
      environment:
        POSTGRES_USER: forex_user
        POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
        POSTGRES_DB: forex_db
      ports:
        - "5432:5432"
      volumes:
        - postgres_data:/var/lib/postgresql/data
      healthcheck:
        test: ["CMD-SHELL", "pg_isready -U forex_user"]
        interval: 10s
        timeout: 5s
        retries: 5
    
    influxdb:
      image: influxdb:2.7-alpine
      container_name: forex_influxdb
      environment:
        DOCKER_INFLUXDB_INIT_MODE: setup
        DOCKER_INFLUXDB_INIT_USERNAME: admin
        DOCKER_INFLUXDB_INIT_PASSWORD: ${INFLUXDB_PASSWORD}
        DOCKER_INFLUXDB_INIT_ORG: forex_org
        DOCKER_INFLUXDB_INIT_BUCKET: exchange_rates
        DOCKER_INFLUXDB_INIT_ADMIN_TOKEN: ${INFLUXDB_TOKEN}
      ports:
        - "8086:8086"
      volumes:
        - influxdb_data:/var/lib/influxdb2
        - influxdb_config:/etc/influxdb2
      healthcheck:
        test: ["CMD", "influx", "ping"]
        interval: 10s
        timeout: 5s
        retries: 5
    
    redis:
      image: redis:7-alpine
      container_name: forex_redis
      ports:
        - "6379:6379"
      volumes:
        - redis_data:/data
      command: redis-server --appendonly yes
      healthcheck:
        test: ["CMD", "redis-cli", "ping"]
        interval: 10s
        timeout: 5s
        retries: 5
    
    minio:
      image: minio/minio:latest
      container_name: forex_minio
      environment:
        MINIO_ROOT_USER: ${MINIO_ACCESS_KEY}
        MINIO_ROOT_PASSWORD: ${MINIO_SECRET_KEY}
      ports:
        - "9000:9000"    # API
        - "9001:9001"    # Console
      volumes:
        - minio_data:/data
      command: server /data --console-address ":9001"
      healthcheck:
        test: ["CMD", "curl", "-f", "http://localhost:9000/minio/health/live"]
        interval: 10s
        timeout: 5s
        retries: 5
    
    celery_worker:
      build: .
      container_name: forex_celery_worker
      command: celery -A src.ingestion.scheduler worker --loglevel=info
      depends_on:
        - redis
        - postgres
        - influxdb
      environment:
        - REDIS_URL=redis://redis:6379/0
        - POSTGRES_URL=postgresql://forex_user:${POSTGRES_PASSWORD}@postgres:5432/forex_db
        - INFLUXDB_URL=http://influxdb:8086
      volumes:
        - .:/app
    
    celery_beat:
      build: .
      container_name: forex_celery_beat
      command: celery -A src.ingestion.scheduler beat --loglevel=info
      depends_on:
        - redis
        - celery_worker
      environment:
        - REDIS_URL=redis://redis:6379/0
      volumes:
        - .:/app
  
  volumes:
    postgres_data:
    influxdb_data:
    influxdb_config:
    redis_data:
    minio_data:
  ```

- [ ] تشغيل `docker-compose up -d`
- [ ] التحقق من اتصال جميع الخدمات:
  ```bash
  docker-compose ps  # جميع الخدمات healthy
  docker logs forex_postgres
  docker logs forex_influxdb
  ```
- [ ] كتابة `scripts/setup_db.py` لإنشاء الجداول (PostgreSQL):
  ```python
  """إنشاء جداول PostgreSQL للمشروع"""
  from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Float, Boolean, JSON
  from sqlalchemy.ext.declarative import declarative_base
  from sqlalchemy.dialects.postgresql import UUID, JSONB
  import uuid
  from datetime import datetime
  
  Base = declarative_base()
  
  class Source(Base):
      """جدول المصادر"""
      __tablename__ = 'sources'
      
      id = Column(Integer, primary_key=True)
      name = Column(String(255), unique=True, nullable=False)
      type = Column(String(50), nullable=False)  # rss, telegram, web, api
      url = Column(Text)
      frequency_minutes = Column(Integer, default=15)
      is_active = Column(Boolean, default=True)
      last_fetch = Column(DateTime)
      config = Column(JSONB)  # إعدادات خاصة بكل مصدر
      created_at = Column(DateTime, default=datetime.utcnow)
  
  class RawNews(Base):
      """جدول الأخبار الخام"""
      __tablename__ = 'raw_news'
      
      id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
      source_id = Column(Integer, nullable=False)
      source_type = Column(String(50), nullable=False)
      timestamp = Column(DateTime, nullable=False, index=True)
      raw_text = Column(Text, nullable=False)
      raw_numeric = Column(Float)
      language = Column(String(10))
      content_hash = Column(String(64), unique=True, index=True)  # SHA-256 لمنع التكرار
      metadata = Column(JSONB)
      created_at = Column(DateTime, default=datetime.utcnow)
  
  class ProcessedNews(Base):
      """جدول الأخبار المعالجة"""
      __tablename__ = 'processed_news'
      
      id = Column(UUID(as_uuid=True), primary_key=True)  # نفس id من raw_news
      cleaned_text = Column(Text)
      extracted_price = Column(Float)
      event_category = Column(String(50))  # military, political, economic, social
      event_weight = Column(Float)
      sentiment = Column(String(20))  # positive, negative, neutral
      sentiment_score = Column(Float)  # -1 to 1
      embedding_vector = Column(JSONB)  # Word Embedding (اختياري)
      processing_timestamp = Column(DateTime, default=datetime.utcnow)
      processing_version = Column(String(20))  # إصدار Pipeline
  
  class Prediction(Base):
      """جدول التنبؤات"""
      __tablename__ = 'predictions'
      
      id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
      prediction_timestamp = Column(DateTime, nullable=False, index=True)
      horizon_hours = Column(Integer, nullable=False)  # 24 أو 72
      
      # التنبؤ
      predicted_price = Column(Float, nullable=False)
      predicted_direction = Column(String(20))  # up, down, stable
      confidence = Column(Float)  # 0-1
      
      # Quantiles (من TFT)
      q05 = Column(Float)
      q25 = Column(Float)
      q50 = Column(Float)  # median
      q75 = Column(Float)
      q95 = Column(Float)
      
      # التفسير
      top_features = Column(JSONB)  # أهم 10 ميزات
      shap_values = Column(JSONB)  # SHAP explanation
      contributing_events = Column(JSONB)  # الأحداث المؤثرة
      
      # البيانات الفعلية (تُملأ لاحقاً)
      actual_price = Column(Float)
      actual_direction = Column(String(20))
      
      # التقييم
      error_mae = Column(Float)
      error_mape = Column(Float)
      direction_correct = Column(Boolean)
      
      model_version = Column(String(50))  # Gen6_1, Hybrid_v2, etc.
      created_at = Column(DateTime, default=datetime.utcnow)
  
  class ModelPerformance(Base):
      """جدول أداء النماذج"""
      __tablename__ = 'model_performance'
      
      id = Column(Integer, primary_key=True)
      model_name = Column(String(100), nullable=False)
      model_version = Column(String(50), nullable=False)
      evaluation_date = Column(DateTime, nullable=False, index=True)
      
      # مقاييس الأداء
      mae = Column(Float)
      rmse = Column(Float)
      mape = Column(Float)
      r2_score = Column(Float)
      directional_accuracy = Column(Float)
      
      # تفاصيل التقييم
      test_samples = Column(Integer)
      horizon_hours = Column(Integer)
      dataset_version = Column(String(50))
      
      # Backtesting
      backtest_windows = Column(Integer)
      avg_mae = Column(Float)
      std_mae = Column(Float)
      
      hyperparameters = Column(JSONB)
      created_at = Column(DateTime, default=datetime.utcnow)
  
  class ClassifiedEvent(Base):
      """جدول الأحداث المصنفة"""
      __tablename__ = 'classified_events'
      
      id = Column(Integer, primary_key=True)
      timestamp = Column(DateTime, nullable=False, index=True)
      category = Column(String(50), nullable=False)  # military, political, economic, social
      title = Column(Text)
      description = Column(Text)
      weight = Column(Float, default=0.5)  # 0-1
      decay_applied = Column(Boolean, default=False)
      source = Column(String(255))
      impact_score = Column(Float)  # تأثير مُقاس
  
  class DriftMonitoring(Base):
      """جدول مراقبة الانجراف"""
      __tablename__ = 'drift_monitoring'
      
      id = Column(Integer, primary_key=True)
      check_timestamp = Column(DateTime, nullable=False, index=True)
      drift_type = Column(String(50))  # data_drift, concept_drift
      feature_name = Column(String(100))
      ks_statistic = Column(Float)
      p_value = Column(Float)
      is_drift_detected = Column(Boolean)
      recommendation = Column(Text)
  
  def create_all_tables(database_url):
      """إنشاء جميع الجداول"""
      engine = create_engine(database_url)
      Base.metadata.create_all(engine)
      print("✅ تم إنشاء جميع الجداول بنجاح")
  
  if __name__ == "__main__":
      import os
      db_url = os.getenv('POSTGRES_URL', 'postgresql://forex_user:password@localhost:5432/forex_db')
      create_all_tables(db_url)
  ```

- [ ] تنفيذ السكريبت:
  ```bash
  python scripts/setup_db.py
  ```

- [ ] إعداد InfluxDB: إنشاء Buckets والتحقق
  ```python
  # scripts/setup_influxdb.py
  from influxdb_client import InfluxDBClient, BucketsApi
  import os
  
  url = os.getenv('INFLUXDB_URL', 'http://localhost:8086')
  token = os.getenv('INFLUXDB_TOKEN')
  org = os.getenv('INFLUXDB_ORG', 'forex_org')
  
  client = InfluxDBClient(url=url, token=token, org=org)
  buckets_api = BucketsApi(client)
  
  # إنشاء Buckets
  buckets = [
      ('exchange_rates', '90d'),      # بيانات الأسعار (90 يوم)
      ('external_indicators', '90d'),  # المؤشرات الخارجية
      ('features', '30d'),            # الميزات المُجمّعة
      ('predictions', '365d'),        # التنبؤات (سنة)
  ]
  
  for bucket_name, retention in buckets:
      try:
          buckets_api.create_bucket(bucket_name=bucket_name, 
                                    org=org, 
                                    retention_rules=[{"everySeconds": retention}])
          print(f"✅ Bucket '{bucket_name}' created")
      except Exception as e:
          print(f"⚠️  Bucket '{bucket_name}' might already exist: {e}")
  
  client.close()
  ```

- [ ] إعداد MinIO: إنشاء Buckets
  ```python
  # scripts/setup_minio.py
  from minio import Minio
  import os
  
  client = Minio(
      os.getenv('MINIO_ENDPOINT', 'localhost:9000'),
      access_key=os.getenv('MINIO_ACCESS_KEY'),
      secret_key=os.getenv('MINIO_SECRET_KEY'),
      secure=False
  )
  
  buckets = ['raw-data', 'models', 'backups', 'embeddings', 'reports']
  
  for bucket in buckets:
      if not client.bucket_exists(bucket):
          client.make_bucket(bucket)
          print(f"✅ Bucket '{bucket}' created")
      else:
          print(f"ℹ️  Bucket '{bucket}' already exists")
  ```

- [ ] تشغيل جميع سكريبتات الإعداد والتحقق:
  ```bash
  python scripts/setup_db.py
  python scripts/setup_influxdb.py
  python scripts/setup_minio.py
  ```

### 0.3 إعداد ملفات الإعدادات

- [ ] `config/settings.yaml` — إعدادات عامة (النمط مُستوحى من ACTION-main):
  ```yaml
  project:
    name: "SYP-USD Forecaster"
    version: "1.0.0-beta"
    environment: "development"  # development, staging, production
  
  database:
    postgres_url: ${POSTGRES_URL}
    influxdb_url: ${INFLUXDB_URL}
    influxdb_token: ${INFLUXDB_TOKEN}
    influxdb_org: ${INFLUXDB_ORG}
    redis_url: ${REDIS_URL}
  
  storage:
    minio_endpoint: ${MINIO_ENDPOINT}
    minio_access_key: ${MINIO_ACCESS_KEY}
    minio_secret_key: ${MINIO_SECRET_KEY}
    model_bucket: "models"
    data_bucket: "raw-data"
  
  logging:
    level: "INFO"
    format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file: "logs/forex_forecaster.log"
  
  monitoring:
    enable_drift_detection: true
    drift_check_frequency_hours: 24
    enable_quality_checks: true
    quality_check_frequency_hours: 6
  ```

- [ ] `config/sources.yaml` — تعريف المصادر (من TARGET.MD):
  ```yaml
  price_sources:
    - name: "sp_today"
      type: "web"
      url: "https://sp-today.com/"
      frequency_minutes: 5
      parser: "beautifulsoup"
      active: true
      
    - name: "investing_com"
      type: "web"
      url: "https://www.investing.com/currencies/usd-syp"
      frequency_minutes: 60
      parser: "beautifulsoup"
      active: true
    
    - name: "central_bank_syria"
      type: "web"
      url: "http://www.banquecentrale.gov.sy/"
      frequency_minutes: 1440  # يومي
      parser: "beautifulsoup"
      active: true
  
  telegram_sources:
    prices:
      - name: "telegram_rates_1"
        channel: "@syrian_exchange_rates"
        frequency_minutes: 1
        active: true
        type: "price"
      
      - name: "telegram_rates_2"
        channel: "@damascus_market"
        frequency_minutes: 2
        active: true
        type: "price"
    
    news:
      - name: "telegram_news_1"
        channel: "@syria_economic_news"
        frequency_minutes: 5
        active: true
        type: "news"
  
  rss_sources:
    - name: "enab_baladi"
      url: "https://www.enabbaladi.net/feed/"
      frequency_minutes: 15
      category: "news"
      active: true
    
    - name: "reuters_meast"
      url: "https://www.reuters.com/places/middle-east/feed/"
      frequency_minutes: 15
      category: "news"
      active: true
    
    - name: "sana_syria"
      url: "https://www.sana.sy/feed/"
      frequency_minutes: 30
      category: "official"
      active: true
    
    - name: "alaraby"
      url: "https://www.alaraby.co.uk/feed"
      frequency_minutes: 15
      category: "news"
      active: true
    
    - name: "aljazeera_syria"
      url: "https://www.aljazeera.net/xml/rss/syria.xml"
      frequency_minutes: 15
      category: "news"
      active: true
  
  external_apis:
    - name: "gold_price"
      endpoint: "https://goldprice.org/gold-price-api"
      frequency_minutes: 60
      metric: "XAU_USD"
      active: true
    
    - name: "oil_price"
      endpoint: "https://oilprice.com/api"
      frequency_minutes: 60
      metric: "BRENT"
      active: true
    
    - name: "dxy_index"
      url: "https://www.investing.com/indices/usdollar"
      frequency_minutes: 1440  # يومي
      parser: "beautifulsoup"
      metric: "DXY"
      active: true
  ```

- [ ] `config/model_config.yaml` — إعدادات النماذج (مُستوحى من ACTION-main):
  ```yaml
  # إعدادات عامة
  model_registry:
    active_model: "Hybrid_v1"
    device: "cuda"  # cuda أو cpu
    precision: "16-mixed"  # من ACTION-main
    seed: 42
  
  # البيانات
  data:
    frequency: 'H'  # Hourly (تغيير عن ACTION-main الذي كان يومي)
    max_encoder_length: 168  # 7 أيام × 24 ساعة
    max_prediction_length: 24  # 24 ساعة قادمة
    min_encoder_length: 24  # يوم واحد على الأقل
    gap_hours: 24  # فجوة 24 ساعة لمنع Data Leakage (من ACTION-main)
    
    train_ratio: 0.8
    val_ratio: 0.2
    
    # استيفاء (إضافة جديدة)
    interpolation:
      method: "quadratic"
      max_gap_hours: 72  # أقصى فجوة للاستيفاء
      flag_interpolated: true
  
  # الميزات (معدّلة للفوركس السوري)
  features:
    time_varying_unknown_reals:
      - Close  # سعر الصرف
      - MA10   # متوسط متحرك 10 فترات
      - MA50
      - RSI
      - MACD
      - ROC
      - Momentum_20h
      - Close_to_MA_ratio
      - BB_position  # موقع السعر في Bollinger Bands
      - ATR  # Average True Range
      - gold_price_pct  # تغير سعر الذهب
      - oil_price_pct
      - dxy_pct
      - lbp_rate_pct  # تغير الليرة اللبنانية
      - sentiment_score  # من NLP
      - event_weight  # من تصنيف الأحداث
      - Relative_Returns  # العائد النسبي (الهدف في TFT)
    
    time_varying_known_categoricals:
      - Hour  # 0-23
      - Day_of_Week  # 0-6
      - Month  # 1-12
      - is_weekend  # جمعة/سبت
      - is_holiday  # العطل السورية
      - session_damascus  # جلسة دمشق
      - session_overlap  # تداخل جلسات
    
    static_categoricals: []  # لا يوجد (حذف Sector من ACTION-main)
    
    target: "Relative_Returns"
    target_normalizer: "TorchNormalizer"  # من ACTION-main
  
  # نموذج TFT (من ACTION-main مع تعديلات)
  tft:
    hidden_size: 128
    lstm_layers: 2
    attention_head_size: 4
    dropout: 0.3
    hidden_continuous_size: 64
    
    # Quantile Loss (موسّع عن ACTION-main)
    use_quantile_loss: true
    quantiles: [0.05, 0.25, 0.5, 0.75, 0.95]  # 5 مستويات بدلاً من 3
    
    learning_rate: 0.001
    reduce_on_plateau_patience: 4
  
  # التدريب (من ACTION-main مع تعديلات)
  training:
    max_epochs: 100
    batch_size: null  # يُحدد تلقائياً بـ batch_size_estimator
    gradient_clip_val: 0.1
    
    early_stopping_patience: 15
    
    # Optuna (من ACTION-main)
    optuna_trials: 20  # زيادة من 5 إلى 20
    optuna_timeout: 3600  # ساعة واحدة
    
    # Checkpointing
    checkpoint_dir: "data/models/checkpoints"
    save_top_k: 3
    monitor: "val_loss"
  
  # XGBoost Baseline
  xgboost:
    n_estimators: 500
    max_depth: 6
    learning_rate: 0.1
    subsample: 0.8
    colsample_bytree: 0.8
    objective: "reg:squarederror"
    early_stopping_rounds: 50
  
  # HLT (Holt's Linear Trend)
  hlt:
    smoothing_level: 0.8  # alpha
    smoothing_trend: null  # beta (auto)
    optimized: true
  
  # LSTM للمشاعر (Deep Learning)
  sentiment_lstm:
    embedding_dim: 300  # Word2Vec/GloVe/FastText
    hidden_units: 128
    num_layers: 2
    dropout: 0.3
    bidirectional: true
    learning_rate: 0.001
    max_epochs: 50
    batch_size: 64
  
  # Hybrid Ensemble
  hybrid:
    mode: "weighted_voting"  # weighted_voting, stacking, meta_learner
    weights:
      sentiment_path: 0.3
      time_series_path: 0.4
      baseline_path: 0.3
    
    # أوزان ديناميكية (اختياري)
    dynamic_weights: false
    weight_update_frequency_days: 7
  ```

- [ ] `config/alerts.yaml` — قواعد التنبيهات:
  ```yaml
  telegram_bot:
    token: ${TELEGRAM_BOT_TOKEN}
    chat_ids:
      - ${ADMIN_CHAT_ID}
  
  alerts:
    sharp_change:
      enabled: true
      threshold_percent: 3.0  # تغير > 3% خلال ساعة
      priority: "high"
    
    prediction_error:
      enabled: true
      mape_threshold: 5.0  # MAPE > 5%
      priority: "medium"
    
    source_downtime:
      enabled: true
      threshold_minutes: 60  # تعطل > ساعة
      priority: "high"
    
    data_drift:
      enabled: true
      ks_p_value_threshold: 0.05
      priority: "medium"
    
    model_degradation:
      enabled: true
      performance_drop_percent: 10.0  # تراجع أداء > 10%
      priority: "high"
  
  notifications:
    daily_summary:
      enabled: true
      time: "08:00"  # UTC
    
    weekly_report:
      enabled: true
      day: "Sunday"
      time: "09:00"
  ```

**مخرجات المرحلة 0:**
✅ بيئة تطوير كاملة مع Python 3.11+
✅ Docker Compose يعمل بجميع الخدمات (Postgres, InfluxDB, Redis, MinIO)
✅ جداول PostgreSQL جاهزة
✅ Buckets InfluxDB و MinIO جاهزة
✅ ملفات إعدادات شاملة (4 ملفات YAML)
✅ هيكل مجلدات منظم مع مرجع ACTION-main
✅ كود ACTION-main مُستنسخ ومُحلّل

---

## المرحلة 1: خط جمع البيانات (الأسبوع 3-6)

> **الأساس**: نستخدم نمط Async Pattern من ACTION-main مع استبدال yfinance بـ Scrapers متعددة

### 1.1 بناء Collectors (الأسبوع 3-4)

#### 1.1.1 Base Collector (مستوحى من ACTION-main)

- [ ] إنشاء `src/ingestion/collectors/base.py`:
  ```python
  """Base Collector Class — نمط موحد لجميع الجامعات"""
  from abc import ABC, abstractmethod
  from typing import List, Dict, Any
  import asyncio
  import hashlib
  from datetime import datetime
  import uuid
  
  class BaseCollector(ABC):
      """
      كلاس أساسي لجميع الجامعات
      مستوحى من data_fetcher.py في ACTION-main
      """
      
      def __init__(self, name: str, source_type: str):
          self.name = name
          self.source_type = source_type
          self.session = None
      
      @abstractmethod
      async def collect(self, **kwargs) -> List[Dict[str, Any]]:
          """جمع البيانات من المصدر - يُنفذ في الكلاسات الفرعية"""
          pass
      
      def compute_hash(self, content: str) -> str:
          """حساب SHA-256 hash لمنع التكرار"""
          return hashlib.sha256(content.encode('utf-8')).hexdigest()
      
      def to_unified_format(self, raw_data: Dict) -> Dict:
          """تحويل إلى التنسيق الموحد"""
          return {
              "id": str(uuid.uuid4()),
              "source": self.name,
              "source_type": self.source_type,
              "timestamp": raw_data.get('timestamp', datetime.utcnow()),
              "raw_text": raw_data.get('text', ''),
              "raw_numeric": raw_data.get('numeric'),
              "language": raw_data.get('language', 'ar'),
              "metadata": raw_data.get('metadata', {}),
              "content_hash": self.compute_hash(str(raw_data))
          }
      
      async def collect_with_retry(self, max_retries=3, **kwargs):
          """
          جمع مع إعادة المحاولة (Exponential Backoff)
          مستوحى من ACTION-main
          """
          for attempt in range(max_retries):
              try:
                  return await self.collect(**kwargs)
              except Exception as e:
                  wait_time = 2 ** attempt  # 1s, 2s, 4s
                  print(f"⚠️  Attempt {attempt + 1} failed: {e}. Retrying in {wait_time}s...")
                  await asyncio.sleep(wait_time)
          
          raise Exception(f"Failed to collect from {self.name} after {max_retries} attempts")
  ```

#### 1.1.2 RSS Collector

- [ ] إنشاء `src/ingestion/collectors/rss_collector.py`:
  ```python
  """RSS Feed Collector"""
  import feedparser
  import asyncio
  from datetime import datetime
  from .base import BaseCollector
  from typing import List, Dict
  
  class RSSCollector(BaseCollector):
      def __init__(self, name: str, url: str):
          super().__init__(name, source_type="rss")
          self.url = url
      
      async def collect(self, since: datetime = None) -> List[Dict]:
          """جمع آخر العناصر من RSS Feed"""
          loop = asyncio.get_event_loop()
          
          # تنفيذ feedparser في thread منفصل (blocking I/O)
          feed = await loop.run_in_executor(None, feedparser.parse, self.url)
          
          items = []
          for entry in feed.entries:
              # استخراج التاريخ
              published = entry.get('published_parsed')
              if published:
                  pub_date = datetime(*published[:6])
              else:
                  pub_date = datetime.utcnow()
              
              # تخطي إذا كان قديماً
              if since and pub_date < since:
                  continue
              
              raw_data = {
                  'timestamp': pub_date,
                  'text': f"{entry.get('title', '')} {entry.get('summary', '')}",
                  'metadata': {
                      'title': entry.get('title'),
                      'link': entry.get('link'),
                      'author': entry.get('author'),
                  }
              }
              
              items.append(self.to_unified_format(raw_data))
          
          return items
  ```

- [ ] اختبار على مصدر واحد (عنب بلدي RSS):
  ```python
  # tests/test_rss_collector.py
  import asyncio
  from src.ingestion.collectors.rss_collector import RSSCollector
  
  async def test_enab_baladi():
      collector = RSSCollector("enab_baladi", "https://www.enabbaladi.net/feed/")
      items = await collector.collect_with_retry()
      
      assert len(items) > 0, "No items collected"
      assert items[0]['source_type'] == 'rss'
      assert 'content_hash' in items[0]
      
      print(f"✅ Collected {len(items)} items from Enab Baladi")
      print(f"Sample: {items[0]['raw_text'][:100]}")
  
  if __name__ == "__main__":
      asyncio.run(test_enab_baladi())
  ```

- [ ] إضافة باقي المصادر (رويترز، سانا، الجزيرة، العربي الجديد)
- [ ] كتابة `tests/test_rss_collector.py` — 5+ حالات اختبار

#### 1.1.3 Telegram Collector (نمط متقدم)

- [ ] تثبيت `telethon`
- [ ] إنشاء `src/ingestion/collectors/telegram_collector.py`:
  ```python
  """Telegram Channel Collector with Session Pool"""
  from telethon import TelegramClient
  from telethon.errors import FloodWaitError
  import asyncio
  import random
  from datetime import datetime, timedelta
  from typing import List, Dict
  from .base import BaseCollector
  
  class TelegramCollector(BaseCollector):
      """
      جامع قنوات تلغرام مع:
      - تعدد الحسابات (Session Pool)
      - تأخيرات عشوائية (Anti-Ban)
      - معالجة FloodWait
      """
      
      def __init__(self, name: str, channel: str, api_credentials: List[Dict]):
          super().__init__(name, source_type="telegram")
          self.channel = channel
          self.clients = []
          self.current_client_idx = 0
          
          # إنشاء عدة Clients
          for cred in api_credentials:
              client = TelegramClient(
                  session=f"sessions/{cred['session_name']}",
                  api_id=cred['api_id'],
                  api_hash=cred['api_hash']
              )
              self.clients.append(client)
      
      async def __aenter__(self):
          """بدء جميع الجلسات"""
          for client in self.clients:
              await client.start()
          return self
      
      async def __aexit__(self, *args):
          """إنهاء جميع الجلسات"""
          for client in self.clients:
              await client.disconnect()
      
      def get_next_client(self):
          """تدوير بين الحسابات"""
          client = self.clients[self.current_client_idx]
          self.current_client_idx = (self.current_client_idx + 1) % len(self.clients)
          return client
      
      async def collect(self, limit: int = 100, since_hours: int = 24) -> List[Dict]:
          """جمع رسائل من القناة"""
          items = []
          client = self.get_next_client()
          
          since_date = datetime.utcnow() - timedelta(hours=since_hours)
          
          try:
              async for message in client.iter_messages(
                  self.channel,
                  limit=limit,
                  offset_date=since_date
              ):
                  if not message.text:
                      continue
                  
                  raw_data = {
                      'timestamp': message.date,
                      'text': message.text,
                      'metadata': {
                          'message_id': message.id,
                          'views': message.views,
                          'forwards': message.forwards,
                          'has_media': message.media is not None,
                      }
                  }
                  
                  items.append(self.to_unified_format(raw_data))
                  
                  # تأخير عشوائي لتجنب الحظر
                  await asyncio.sleep(random.uniform(0.5, 2.0))
          
          except FloodWaitError as e:
              print(f"⚠️  FloodWait: waiting {e.seconds} seconds...")
              await asyncio.sleep(e.seconds)
              # إعادة المحاولة مع client آخر
              return await self.collect(limit, since_hours)
          
          return items
  ```

- [ ] إعداد حساب تلغرام للتطوير:
  ```python
  # scripts/setup_telegram.py
  from telethon import TelegramClient
  import os
  
  api_id = int(os.getenv('TELEGRAM_API_ID'))
  api_hash = os.getenv('TELEGRAM_API_HASH')
  
  client = TelegramClient('sessions/dev_session', api_id, api_hash)
  
  async def main():
      await client.start()
      print("✅ Telegram session created successfully")
      await client.disconnect()
  
  if __name__ == "__main__":
      import asyncio
      asyncio.run(main())
  ```

- [ ] اختبار على قناة أسعار واحدة
- [ ] إضافة قنوات الأسعار والأخبار (من config/sources.yaml)
- [ ] كتابة `tests/test_telegram_collector.py`

#### 1.1.4 Web Scraper (مواقع الأسعار)

- [ ] إنشاء `src/ingestion/collectors/web_scraper.py`:
  ```python
  """Web Scraping for Exchange Rate Websites"""
  from bs4 import BeautifulSoup
  import aiohttp
  from datetime import datetime
  from typing import List, Dict, Optional
  from .base import BaseCollector
  import re
  
  class WebScraper(BaseCollector):
      def __init__(self, name: str, url: str, parser_config: Dict):
          super().__init__(name, source_type="web")
          self.url = url
          self.parser_config = parser_config
      
      async def collect(self) -> List[Dict]:
          """جمع سعر الصرف من موقع"""
          async with aiohttp.ClientSession() as session:
              async with session.get(self.url, timeout=30) as response:
                  html = await response.text()
          
          soup = BeautifulSoup(html, 'html.parser')
          
          # استخراج السعر بناءً على الإعدادات
          price = self.extract_price(soup)
          
          if price is None:
              return []
          
          raw_data = {
              'timestamp': datetime.utcnow(),
              'text': f"سعر الصرف: {price}",
              'numeric': price,
              'metadata': {
                  'source_url': self.url,
                  'extraction_method': 'css_selector'
              }
          }
          
          return [self.to_unified_format(raw_data)]
      
      def extract_price(self, soup: BeautifulSoup) -> Optional[float]:
          """استخراج السعر باستخدام CSS Selector أو Regex"""
          # حاول CSS Selector أولاً
          if 'css_selector' in self.parser_config:
              element = soup.select_one(self.parser_config['css_selector'])
              if element:
                  text = element.get_text(strip=True)
                  return self.parse_price(text)
          
          # إذا فشل، استخدم Regex على كامل الصفحة
          if 'regex_pattern' in self.parser_config:
              pattern = self.parser_config['regex_pattern']
              match = re.search(pattern, soup.get_text())
              if match:
                  return float(match.group(1).replace(',', ''))
          
          return None
      
      def parse_price(self, text: str) -> Optional[float]:
          """تحويل نص إلى رقم"""
          # إزالة الفواصل والنص الزائد
          cleaned = re.sub(r'[^\d.]', '', text)
          try:
              return float(cleaned)
          except ValueError:
              return None
  ```

- [ ] إنشاء Parser Configs في `config/sources.yaml`:
  ```yaml
  web_parsers:
    sp_today:
      css_selector: "div.price-box span.price"
      regex_pattern: null
    
    investing_com:
      css_selector: "span[data-test='instrument-price-last']"
      regex_pattern: null
    
    central_bank:
      css_selector: null
      regex_pattern: r'(\d{1,3}[,.]?\d{3,})\s*ل\.س'
  ```

- [ ] اختبار كل موقع على حدة
- [ ] كتابة `tests/test_web_scraper.py`

#### 1.1.5 API Collector (مؤشرات خارجية)

- [ ] إنشاء `src/ingestion/collectors/api_collector.py`:
  ```python
  """External Economic Indicators Collector"""
  import aiohttp
  from datetime import datetime
  from typing import List, Dict
  from .base import BaseCollector
  
  class APICollector(BaseCollector):
      """جمع المؤشرات الخارجية من APIs"""
      
      ENDPOINTS = {
          'gold': 'https://api.gold.org/v1/prices/usd',
          'dxy': 'https://api.investing.com/api/financialdata/8827/historical/chart',
          # إضافة endpoints أخرى
      }
      
      def __init__(self, name: str, metric: str):
          super().__init__(name, source_type="api")
          self.metric = metric
          self.endpoint = self.ENDPOINTS.get(metric)
      
      async def collect(self) -> List[Dict]:
          """جمع قيمة المؤشر"""
          async with aiohttp.ClientSession() as session:
              async with session.get(self.endpoint, timeout=30) as response:
                  data = await response.json()
          
          # معالجة حسب نوع المؤشر
          value = self.parse_response(data)
          
          raw_data = {
              'timestamp': datetime.utcnow(),
              'text': f"{self.metric}: {value}",
              'numeric': value,
              'metadata': {
                  'metric': self.metric,
                  'raw_response': data
              }
          }
          
          return [self.to_unified_format(raw_data)]
      
      def parse_response(self, data: Dict) -> float:
          """استخراج القيمة من  استجابة API"""
          # يعتمد على هيكل كل API
          # مثال بسيط:
          if 'price' in data:
              return float(data['price'])
          elif 'value' in data:
              return float(data['value'])
          else:
              raise ValueError(f"Unknown response format: {data}")
  ```

- [ ] تكامل مع yfinance للمؤشرات السهلة:
  ```python
  # src/ingestion/collectors/yfinance_collector.py
  import yfinance as yf
  from datetime import datetime
  from .base import BaseCollector
  
  class YFinanceCollector(BaseCollector):
      """استخدام yfinance للمؤشرات العالمية (من ACTION-main)"""
      
      TICKERS = {
          'gold': 'GC=F',
          'oil_brent': 'BZ=F',
          'dxy': 'DX-Y.NYB',
          'eur_usd': 'EURUSD=X',
          'gbp_usd': 'GBPUSD=X',
          'usd_try': 'USDTRY=X',
      }
      
      async def collect(self, metric: str) -> List[Dict]:
          ticker = self.TICKERS.get(metric)
          if not ticker:
              raise ValueError(f"Unknown metric: {metric}")
          
          # جلب آخر سعر
          import asyncio
          loop = asyncio.get_event_loop()
          stock = await loop.run_in_executor(None, yf.Ticker, ticker)
          info = await loop.run_in_executor(None, lambda: stock.history(period='1d'))
          
          if info.empty:
              return []
          
          latest = info.iloc[-1]
          
          raw_data = {
              'timestamp': datetime.utcnow(),
              'text': f"{metric}: {latest['Close']}",
              'numeric': float(latest['Close']),
              'metadata': {
                  'ticker': ticker,
                  'volume': float(latest['Volume']),
              }
          }
          
          return [self.to_unified_format(raw_data)]
  ```

- [ ] كتابة `tests/test_api_collector.py`

### 1.2 نظام الجدولة (الأسبوع 5)

- [ ] تثبيت `celery`, `celery[redis]`
- [ ] إنشاء `src/ingestion/scheduler.py`:
  - تعريف المهام (Tasks) لكل Collector
  - جدولة بـ Celery Beat:
    - RSS: كل 15 دقيقة
    - Telegram (أسعار): كل 5 دقائق
    - Telegram (أخبار): كل 5 دقائق
    - Web Scraper (أسعار): كل 5 دقائق
    - API (مؤشرات): كل ساعة
  - معالجة الأخطاء: Exponential Backoff + Circuit Breaker
  - تسجيل كل محاولة (نجاح/فشل/عدد العناصر)
- [ ] إنشاء `src/ingestion/raw_schema.py` — Pydantic schema للتنسيق الموحد
- [ ] تشغيل واختبار الجدولة لمدة 24 ساعة
- [ ] التحقق من عدم وجود تكرارات

### 1.3 التحقق والمراقبة (الأسبوع 6)

- [ ] إنشاء `src/monitoring/health_checker.py`:
  - فحص اتصال كل خدمة (DB, InfluxDB, Redis)
  - فحص حالة كل Collector (آخر جمع، عدد الأخطاء)
  - تنبيه عند تعطل مصدر > ساعة
- [ ] إنشاء سكريبت مراقبة بسيط يطبع حالة النظام
- [ ] التحقق من تراكم البيانات في DB:
  - عدد الأخبار المجمعة
  - عدد نقاط الأسعار
  - تغطية المصادر

**مخرجات المرحلة 1:**
✅ 5+ مصادر تجمع آليًا
✅ جدولة مستقرة تعمل 24/7
✅ بيانات تتراكم في PostgreSQL + InfluxDB
✅ لا تكرارات
✅ سجل أخطاء واضح

> **ملاحظة من ACTION-main**: استخدام Async Pattern من `old_code/scripts/data_fetcher.py` مع `ThreadPoolExecutor` أثبت فعالية عالية في جمع بيانات متوازي. في ACTION-main، كان يتم جمع 50+ ticker في وقت واحد. نطبق نفس النمط هنا على المصادر المتعددة.

---

## المرحلة 2: خط المعالجة الأساسي (الأسبوع 7-10)

### 2.1 تنظيف النصوص (الأسبوع 7)

- [ ] إنشاء `src/processing/text/cleaner.py`:
  - `TextCleaner` class:
    - إزالة HTML tags
    - إزالة URLs
    - إزالة mentions و hashtags
    - إزالة emojis
    - تطبيع عربي (أ/إ/آ→ا، ة→ه، ى→ي)
    - تحويل أرقام شرقية → غربية
    - تطبيع مسافات
    - إزالة تشكيل
- [ ] إنشاء `src/processing/text/tokenizer.py`:
  - تقطيع عربي (Farasa أو NLTK)
  - إزالة Stop Words (قائمة مخصصة)
- [ ] كتابة `tests/test_cleaner.py` — 15+ حالة اختبار

### 2.2 استخراج القيم الرقمية (الأسبوع 7)

- [ ] إنشاء `src/processing/numeric/extractor.py`:
  - `NumericExtractor` class:
    - استخراج أسعار: "الدولار 14500" → 14500
    - استخراج نسب: "3.5%" → 0.035
    - استخراج اتجاه: "ارتفع/انخفض/استقر"
    - التحقق من النطاق المعقول (100 < سعر < 1,000,000)
- [ ] كتابة `tests/test_extractor.py`

### 2.3 مصنف الأحداث (الأسبوع 8)

- [ ] جمع عينة توسيم يدوية: 1000 خبر على الأقل
  - 250 عسكري، 250 سياسي، 250 اقتصادي، 250 اجتماعي
- [ ] إنشاء `src/processing/text/classifier.py`:
  - `EventClassifier` (Naïve Bayes / TF-IDF):
    - تدريب على العينة الموسومة
    - تقييم بـ 5-Fold CV
    - هدف: Accuracy ≥ 70%
    - حفظ النموذج بـ `pickle`
- [ ] كتابة `tests/test_classifier.py`

### 2.4 مصنف المشاعر (الأسبوع 8)

- [ ] توسيم عينة المشاعر: 1000 خبر (إيجابي/سلبي/محايد)
- [ ] إنشاء `src/processing/text/sentiment.py`:
  - `SentimentNB` class:
    - Multinomial Naïve Bayes + TF-IDF
    - تدريب وتقييم (هدف: Accuracy ≥ 70%)
    - `predict(text)` → SentimentResult(label, score, confidence)
    - `predict_batch(texts)` → list
    - حفظ/تحميل النموذج
- [ ] كتابة `tests/test_sentiment.py`

### 2.5 نموذج الأوزان الديناميكية (الأسبوع 9)

- [ ] إنشاء `src/processing/features/weights.py`:
  - `DynamicWeightCalculator`:
    - أوزان ابتدائية: عسكري=0.9, سياسي=0.7, اقتصادي=0.55, اجتماعي=0.35
    - تلاشي أسي: $W_t = W_0 \times e^{-\lambda \Delta t}$
    - حساب الوزن الحالي لكل حدث
    - تجميع أوزان نافذة زمنية
- [ ] كتابة `tests/test_weights.py`

### 2.6 استيفاء البيانات المفقودة (الأسبوع 9)

- [ ] إنشاء `src/processing/numeric/interpolation.py`:
  - Quadratic Interpolation للفجوات القصيرة (1-3 أيام)
  - Forward Fill + Flag للفجوات الطويلة
  - وضع علامة `is_interpolated` على القيم المستوفاة
- [ ] كتابة `tests/test_interpolation.py`

### 2.7 خط المعالجة المتكامل (الأسبوع 10)

- [ ] إنشاء `src/processing/pipeline.py`:
  - `ProcessingPipeline` class:
    - يربط الخطوات: تنظيف → استخراج → تصنيف → مشاعر → أوزان
    - يقرأ من `raw_news` → يكتب في `processed_news` + `classified_events`
    - يعمل كـ Celery Task كل 5 دقائق
  - معالجة الأخطاء: لا يتوقف عند فشل خبر واحد
  - تسجيل الإحصائيات (عدد المعالَج/الفاشل)
- [ ] اختبار تكاملي: إدخال 100 خبر خام → التحقق من الخرج
- [ ] تشغيل مستمر لمدة 48 ساعة → مراقبة

**مخرجات المرحلة 2:**
✅ Pipeline معالجة يعمل آليًا
✅ تنظيف نصوص عربية
✅ تصنيف أحداث (4 فئات)
✅ تحليل مشاعر (3 فئات)
✅ أوزان ديناميكية مع تلاشي زمني
✅ استيفاء بيانات مفقودة

> **درس من ACTION-main**: في `old_code/scripts/preprocessor.py`، يتم استخدام نمط `ffill()` ثم `bfill()` ثم `fillna(0)` بالترتيب لمعالجة القيم المفقودة. هذا النمط ثلاثي الطبقات ضروري لضمان عدم وجود NaN values قبل التدريب. كما أن `allow_missing_timesteps=True` في `TimeSeriesDataSet` يسمح بفجوات زمنية بدون أخطاء.

---

## المرحلة 3: تجميع الميزات والتخزين (الأسبوع 11-12)

### 3.1 تجميع الميزات الزمنية (الأسبوع 11)

- [ ] إنشاء `src/processing/features/aggregator.py`:
  - `FeatureAggregator` class:
    - نوافذ: 1h, 6h, 12h, 24h, 7d
    - **ميزات سعرية** (لكل نافذة):
      - متوسط السعر
      - الانحراف المعياري
      - التغير السعري (ΔP)
      - اتجاه التغير
      - أعلى/أدنى سعر
      - التقلب (Volatility)
    - **ميزات الأحداث** (لكل نافذة):
      - مجموع أوزان كل فئة
      - عدد الأحداث لكل فئة
      - أقصى وزن حدث
      - متوسط المشاعر المرجح
      - نسبة الأخبار الإيجابية/السلبية
    - **ميزات خارجية**:
      - تغير سعر الذهب %
      - تغير سعر النفط %
      - مؤشر الدولار DXY
    - **ميزات زمنية** (Time Dummies):
      - يوم الأسبوع (0-6)
      - ساعة اليوم (0-23)
      - شهر السنة (1-12)
      - هل عطلة (0/1)
  - كتابة في InfluxDB (measurement: `features`)
- [ ] كتابة `tests/test_aggregator.py`

### 3.2 مخزن الميزات (الأسبوع 11)

- [ ] إنشاء `src/processing/features/store.py`:
  - `FeatureStore` class:
    - `save(features, window, timestamp)`
    - `get_latest(window)` → آخر متجه ميزات
    - `get_range(start, end, window)` → DataFrame
    - `get_training_data(days, window)` → X, y
    - إصدارات مجموعات الميزات

### 3.3 طبقة التخزين (الأسبوع 12)

- [ ] إنشاء `src/storage/timeseries_db.py` — عميل InfluxDB
- [ ] إنشاء `src/storage/relational_db.py` — عميل PostgreSQL (SQLAlchemy)
- [ ] إنشاء `src/storage/object_store.py` — عميل MinIO
- [ ] إنشاء `src/storage/model_registry.py`:
  - حفظ نموذج مع metadata
  - تحميل نموذج بالإصدار
  - قائمة النماذج المتاحة
  - تعيين النموذج النشط (Active Model)

**مخرجات المرحلة 3:**
✅ متجهات ميزات جاهزة للتدريب
✅ Feature Store مع إصدارات
✅ طبقة تخزين موحدة
✅ Time Dummies مدمجة

> **جوهرة من ACTION-main**: في `old_code/scripts/utils/feature_engineer.py`، يتم حساب **12 مؤشراً فنياً** بشكل منهجي (MA10, MA50, RSI, MACD, ROC, VWAP, BB, Momentum، إلخ). المهم هنا:
> 
> 1. **Log1p Transform** يُطبّق على Close, Volume, MA10, MA50, VWAP قبل التطبيع — وهذا يحسن توزيع البيانات المائلة بشكل كبير.
> 2. **المؤشرات النسبية** مثل `Close_to_MA_ratio` و `Close_to_BB_upper` أقوى من القيم المطلقة.
> 3. الميزات الزمنية (`Month`, `Day_of_Week`) تُحوّل إلى **strings categorical** - وليس integers - لأن TFT يتعامل معها بشكل أفضل كفئات.
> 
> **لمشروعنا**: نتبنى نفس النهج لكن:
> - نستبدل Volume/VWAP بـ Sentiment/Event Weight
> - نضيف ميزات جلسات التداول العالمية
> - نستخدم Cyclical Encoding للساعة/اليوم (sin/cos)

---

## المرحلة 4: النماذج الأساسية (الأسبوع 13-16)

### 4.1 نموذج XGBoost Baseline (الأسبوع 13)

- [ ] إنشاء `src/prediction/models/baseline.py`:
  - `XGBoostPredictor` class:
    - `train(X, y)` → يدرب النموذج
    - `predict(features)` → PredictionResult
    - `feature_importance()` → dict
    - معلمات أولية: n_estimators=500, max_depth=6, lr=0.1
- [ ] إنشاء `src/prediction/training/trainer.py`:
  - تقسيم زمني: 80% train, 10% val, 10% test
  - التحقق من عدم تسرب بيانات مستقبلية
  - Early Stopping على Validation Set
- [ ] إنشاء `src/prediction/training/evaluator.py`:
  - حساب: MAE, RMSE, MAPE, R², Direction Accuracy
  - تخزين النتائج في `model_performance`
  - طباعة تقرير تقييم
- [ ] تدريب أولي على البيانات المتاحة
- [ ] تقييم: هدف MAPE < 5%
- [ ] كتابة `tests/test_baseline.py`

### 4.2 نموذج السلاسل الزمنية HLT (الأسبوع 14)

- [ ] إنشاء `src/prediction/models/time_series.py`:
  - `HLTPredictor` class:
    - Holt's Linear Trend (statsmodels)
    - `train(price_series)`
    - `predict(horizon=24)` → PredictionResult
    - معلمات: α=0.8, β=auto
  - `SESPredictor` class (بديل أبسط):
    - Simple Exponential Smoothing
  - `ARIMAPredictor` class (اختياري):
    - Auto-ARIMA (pmdarima)
- [ ] تقييم: هدف Accuracy ≥ 90% (المرجع: HLT 95.87%)
- [ ] مقارنة HLT vs SES vs ARIMA

### 4.3 نظام التنبؤ (الأسبوع 15)

- [ ] إنشاء `src/prediction/inference/predictor.py`:
  - `HybridPredictor` class (إصدار أولي — مسارين فقط):
    - المسار 1: XGBoost (وزن 0.5)
    - المسار 2: HLT (وزن 0.5)
    - دمج مرجح
    - حساب نطاق ثقة
    - تحديد اتجاه + احتمالية
  - `predict(features)` → PredictionResult:
    - predicted_price
    - confidence_lower, confidence_upper
    - direction (up/down/stable)
    - direction_probability
    - feature_importance (من XGBoost)
- [ ] إنشاء Celery Task للتنبؤ اليومي:
  - يعمل كل 24 ساعة
  - يقرأ الميزات من Feature Store
  - يخزن التنبؤ في `predictions`
- [ ] كتابة `tests/test_predictor.py`

### 4.4 Backtesting (الأسبوع 16)

- [ ] إنشاء `src/prediction/training/backtester.py`:
  - نافذة تدريب: 180 يوم
  - نافذة اختبار: 30 يوم
  - خطوة: 30 يوم
  - لكل نافذة: تدريب → تنبؤ → تقييم
  - تقرير نهائي: متوسط وانحراف MAE/MAPE/Direction عبر النوافذ
- [ ] تشغيل Backtesting على جميع البيانات المتاحة
- [ ] توثيق النتائج

**مخرجات المرحلة 4:**
✅ XGBoost Baseline يعمل (MAPE < 5%)
✅ HLT يعمل (Accuracy ≥ 90%)
✅ نظام تنبؤ هجين أولي (مساران)
✅ تنبؤ يومي آلي
✅ Backtesting مكتمل
✅ نتائج موثقة

> **من دروس ACTION-main في التدريب**:
> 
> **Backtesting الصارم** (`old_code/app/benchmark_utils.py`):
> - نافذة متدحرجة (Rolling Window): 80% train → 10 days gap → 20% validation
> - لا تسرب بيانات مستقبلية (Data Leakage) بفضل الفجوة الزمنية
> - تقرير شامل: MAE, MAPE, RMSE, Directional Accuracy لكل نافذة
> 
> **Optuna Hyperparameter Tuning** (`old_code/scripts/train.py`):
> - 5-100 تجربة بـ TPESampler (أكفأ من Random Search)
> - MedianPruner يوقف التجارب الضعيفة مبكراً
> - يُحفظ أفضل hyperparameters في config.yaml
> 
> **Batch Size Estimation التلقائي** (`old_code/scripts/utils/batch_size_estimator.py`):
> - يختبر batch sizes متزايدة حتى يصل إلى 90% من GPU memory
> - يمنع Out-of-Memory Errors
> - نتيجة: استخدام أمثل للموارد
> 
> **لمشروعنا**: نطبق نفس الأنماط لكن مع بيانات ساعية بدلاً من يومية، مما يعني:
> - النافذة: 168 ساعة (7 أيام) train → 24 ساعة gap → 24 ساعة validation
> - Optuna يبحث في نطاقات أوسع بسبب تعقيد الفوركس
> - Batch size أصغر (16-64) بسبب التسلسلات الطويلة

---

## المرحلة 5: الواجهات — Dashboard + API (الأسبوع 17-20)

### 5.1 FastAPI Backend (الأسبوع 17-18)

- [ ] تثبيت `fastapi`, `uvicorn`, `pydantic`
- [ ] إنشاء `src/presentation/api/main.py`:
  - إعداد FastAPI app مع metadata
  - Middleware: CORS, Rate Limiting
  - Health Check endpoint
- [ ] إنشاء `src/presentation/api/schemas/` — Pydantic models:
  - `PredictionResponse`
  - `RateResponse`
  - `EventResponse`
  - `ModelPerformanceResponse`
  - `SentimentResponse`
- [ ] إنشاء `src/presentation/api/routes/`:
  - `predictions.py`:
    - `GET /api/v1/prediction/latest?horizon=24`
    - `GET /api/v1/prediction/history?days=7`
  - `rates.py`:
    - `GET /api/v1/rates/current`
    - `GET /api/v1/rates/history?days=30`
  - `events.py`:
    - `GET /api/v1/events/recent?hours=24&category=military`
  - `sentiment.py`:
    - `GET /api/v1/sentiment/current`
  - `models.py`:
    - `GET /api/v1/model/performance`
    - `GET /api/v1/model/explanation/{prediction_id}`
  - `health.py`:
    - `GET /health`
- [ ] إضافة مصادقة بسيطة (API Key header)
- [ ] كتابة `tests/test_api.py`
- [ ] توليد OpenAPI docs (Swagger) تلقائيًا

### 5.2 Streamlit Dashboard (الأسبوع 19-20)

- [ ] تثبيت `streamlit`, `plotly`
- [ ] إنشاء `src/presentation/dashboard/app.py` — الصفحة الرئيسية
- [ ] إنشاء الصفحات:

  **صفحة التنبؤ** (`pages/prediction.py`):
  - [ ] مخطط زمني: سعر فعلي (خط) + توقع (متقطع) + نطاق ثقة (مظلل)
  - [ ] بطاقرقمية: السعر المتوقع، الاتجاه، الاحتمالية
  - [ ] مخطط أهمية الميزات (Feature Importance bar chart)
  - [ ] جدول آخر 7 توقعات مع المقارنة بالفعلي

  **صفحة الأحداث** (`pages/events.py`):
  - [ ] جدول الأحداث خلال 24 ساعة (نوع، وزن، مشاعر، مصدر)
  - [ ] مخطط دائري: توزيع الأحداث بالفئات
  - [ ] مؤشر المشاعر العام (Gauge)
  - [ ] فلتر بالفئة والفترة الزمنية

  **صفحة الأداء** (`pages/performance.py`):
  - [ ] مخطط MAE/MAPE عبر الزمن
  - [ ] مقارنة أداء النماذج (جدول + مخطط)
  - [ ] مخطط الخطأ: توقع vs فعلي (Scatter)
  - [ ] نسبة الاتجاه الصحيح

  **صفحة التنبيهات** (`pages/alerts.py`):
  - [ ] قائمة التنبيهات النشطة
  - [ ] حالة المصادر (أخضر/أحمر)
  - [ ] تاريخ التنبيهات

### 5.3 نظام التنبيهات (الأسبوع 20)

- [ ] إنشاء `src/presentation/alerts/notifier.py`:
  - التنبيه عبر Telegram Bot:
    - تغير حاد > 3% خلال ساعة
    - حدث عالي الوزن > 0.85
    - انحراف كبير عن التوقع
    - تعطل مصدر > ساعة
  - تخزين سجل التنبيهات في DB
- [ ] إنشاء Telegram Bot بسيط
- [ ] ربط التنبيهات بالـ Pipeline

**مخرجات المرحلة 5:**
✅ API جاهز مع Swagger docs
✅ Dashboard تفاعلي (4 صفحات)
✅ نظام تنبيهات تلغرام
✅ مصادقة API بسيطة

> **واجهة Streamlit من ACTION-main** (`old_code/app/app.py`):
> 
> الهيكلية المستخدمة في ACTION-main ممتازة:
> - **الصفحة الرئيسية**: توقعات + مخطط زمني مع نطاق ثقة (Quantiles)
> - **Sidebar**: اختيار stock/ticker + إعدادات
> - **Plotly**: مخططات تفاعلية مع zoom/pan
> - **Caching**: استخدام `@st.cache_data` لتجنب إعادة تحميل البيانات
> - **أهمية الميزات**: bar chart مع الميزات الأكثر تأثيراً
> 
> **دروس مستفادة**:
> - استخدام `plot_utils.py` منفصل يجعل الكود أنظف 
> - المخططات يجب أن تكون RTL-aware للعربية (استخدام `arabic-reshaper` + `bidi`)
> - تحميل async من API الداخلي أسرع من الاتصال بالDB مباشرة
> 
> **لمشروعنا**: نطبق نفس الهيكلية لكن مع:
> - دعم RTL كامل (عربي)
> - صفحات إضافية للأحداث والمشاعر
> - مخططات الأداء المقارن بين النماذج

---

## المرحلة 6: حلقة التغذية الراجعة والمراقبة (الأسبوع 21-22)

### 6.1 حلقة التغذية الراجعة

- [ ] إنشاء `src/prediction/feedback.py`:
  - `FeedbackLoop` class:
    - مقارنة يومية: توقع vs فعلي
    - حساب الخطأ وتخزينه في `predictions.error_*`
    - تحديث أوزان الدمج الهجين حسب أداء كل نموذج
    - إعادة تدريب أسبوعية (نافذة متحركة آخر 180 يوم)
    - تنبيه عند تجاوز MAPE عتبة محددة

### 6.2 مراقبة الانجراف

- [ ] إنشاء `src/monitoring/drift_detector.py`:
  - `DriftMonitor` class:
    - Data Drift: اختبار KS على توزيعات الميزات
    - Concept Drift: مراقبة MAE/MAPE عبر الزمن
    - عتبات: Data Drift p < 0.05, Concept Drift deviation > 15%
    - تنبيه عند اكتشاف انجراف
    - اقتراح إعادة تدريب

### 6.3 مراقبة جودة البيانات

- [ ] إنشاء `src/monitoring/quality_checker.py`:
  - فحص نسبة البيانات المفقودة
  - كشف القيم الشاذة (Z-score > 3)
  - التحقق من اتساق المصادر المتقاطعة
  - تقرير جودة يومي

**مخرجات المرحلة 6:**
✅ تغذية راجعة يومية
✅ إعادة تدريب أسبوعية آلية
✅ مراقبة انجراف
✅ فحص جودة بيانات

---

## المرحلة 7: NLP المتقدم — Word Embedding + DL (الأسبوع 23-30)

### 7.1 تدريب Word Embeddings (الأسبوع 23-24)

- [ ] إنشاء `src/processing/text/embeddings.py`
- [ ] جمع Corpus عربي من البيانات المتراكمة
- [ ] تدريب 3 نماذج Embedding:
  - [ ] **Word2Vec** (gensim): dim=300, window=5, min_count=5
  - [ ] **GloVe** (عربي مدرب مسبقًا + Fine-tuning)
  - [ ] **FastText** (fasttext): dim=300, بما في ذلك n-grams
- [ ] تقييم جودة كل Embedding:
  - Word Similarity tasks
  - Visualization (t-SNE) لكلمات اقتصادية
- [ ] حفظ النماذج في MinIO

### 7.2 نماذج تعلم عميق للمشاعر (الأسبوع 25-28)

- [ ] إنشاء `src/prediction/models/deep_learning.py`
- [ ] تقييم 9 تركيبات:

| # | Embedding | DL Model | هدف الاختبار |
|---|---|---|---|
| 1 | Word2Vec | CNN | Accuracy, F1, CV, MCC |
| 2 | Word2Vec | RNN | Accuracy, F1, CV, MCC |
| 3 | Word2Vec | LSTM | Accuracy, F1, CV, MCC |
| 4 | GloVe | CNN | Accuracy, F1, CV, MCC |
| 5 | GloVe | RNN | Accuracy, F1, CV, MCC |
| 6 | **GloVe** | **LSTM** | **المرشح الأقوى** |
| 7 | FastText | CNN | Accuracy, F1, CV, MCC |
| 8 | FastText | RNN | Accuracy, F1, CV, MCC |
| 9 | FastText | LSTM | Accuracy, F1, CV, MCC |

- [ ] لكل تركيبة:
  - بناء النموذج (TensorFlow/Keras)
  - تدريب مع Early Stopping
  - تقييم على Test Set
  - حساب: Accuracy, F1, CV (5-fold), MCC
  - تسجيل في MLflow
- [ ] اختيار أفضل تركيبة (المتوقع: LSTM + GloVe)
- [ ] هدف: Accuracy ≥ 82%, MCC ≥ 0.40

### 7.3 هندسة ميزات متقدمة (الأسبوع 29)

- [ ] إنشاء `src/processing/features/selector.py`:
  - **مؤشرات تقنية** (ta-lib أو pandas_ta):
    - SMA(5), SMA(10), SMA(20), EMA(5), EMA(20)
    - RSI(14)
    - MACD(12,26,9)
    - Bollinger Bands(20,2)
    - ATR(14)
    - Stochastic, Williams %R, CCI
  - **Mutual Information** لتصفية الميزات:
    - حساب MI(feature, target) لكل ميزة
    - اختيار أعلى K ميزة (K=12-20)
    - حذف ميزات متكررة (MI بين الميزات > عتبة)
  - **Time Dummies** المحسنة:
    - Cyclical Encoding (sin/cos) لليوم والساعة
    - عطلات رسمية سورية
    - أيام قبل/بعد العطلة

### 7.4 تحسين بـ Optuna (الأسبوع 30)

- [ ] إنشاء `src/prediction/training/optimizer.py`:
  - تحسين معلمات XGBoost:
    - n_estimators: [100, 1000]
    - max_depth: [3, 10]
    - learning_rate: [0.01, 0.3]
    - subsample: [0.6, 1.0]
  - تحسين معلمات LSTM:
    - hidden_units: [32, 256]
    - n_layers: [1, 4]
    - dropout: [0.1, 0.5]
    - learning_rate: [1e-4, 1e-2]
  - 100 تجربة لكل نموذج
  - Pruning (MedianPruner) للتجارب السيئة
  - تسجيل أفضل المعلمات

**مخرجات المرحلة 7:**
✅ 3 Word Embeddings مدربة
✅ أفضل تركيبة DL محددة ومقيمة
✅ مكتبة ميزات شاملة ومصفاة
✅ معلمات محسنة بـ Optuna
✅ Accuracy مشاعر ≥ 82%

---

## المرحلة 8: النموذج الهجين الكامل (الأسبوع 31-36)

### 8.1 المسارات الثلاثة (الأسبوع 31-32)

- [ ] ترقية `HybridPredictor` إلى 3 مسارات:
  - **المسار 1 (Sentiment)**: أفضل تركيبة DL من المرحلة 7
  - **المسار 2 (Time Series)**: LSTM أو Bi-LSTM على بيانات الأسعار
  - **المسار 3 (Baseline)**: XGBoost المحسن بـ Optuna
- [ ] تصميم واجهة موحدة لكل مسار:
  - `train(data)` → model
  - `predict(features)` → PredictionResult(price, direction, confidence)
- [ ] تدريب كل مسار بشكل مستقل

### 8.2 طرق الدمج (الأسبوع 33-34)

- [ ] تجربة 3 طرق دمج:

  **أ. Weighted Voting:**
  - أوزان ثابتة ابتدائية
  - أوزان ديناميكية حسب أداء آخر 30 يوم
  - بسيط وشفاف

  **ب. Stacking (Meta-Learner):**
  - مخرجات المسارات الثلاثة → مدخلات لنموذج Ridge أو XGBoost صغير
  - تدريب Meta-Learner على Validation Set
  - أكثر دقة

  **ج. Snapshot Ensemble:**
  - تدريب LSTM واحد مع Cosine Annealing
  - حفظ 3-5 لقطات
  - متوسط التنبؤات

- [ ] مقارنة الطرق الثلاث بـ Backtesting
- [ ] اختيار الأفضل
- [ ] اختبار DM (Diebold-Mariano): هل التحسن معنوي إحصائيًا؟

### 8.3 تكتل البيانات (الأسبوع 35)

- [ ] تجربة Fuzzy C-Means:
  - تقسيم البيانات إلى 3-5 مجموعات
  - تحديد العدد الأمثل (Silhouette Score)
  - بناء نموذج فرعي لكل مجموعة
  - التنبؤ: تحديد المجموعة → استخدام النموذج المناسب
  - دمج بأوزان الانتماء الضبابية

### 8.4 XAI — SHAP (الأسبوع 36)

- [ ] إنشاء `src/prediction/inference/explainer.py`:
  - TreeSHAP لـ XGBoost
  - DeepSHAP لـ LSTM (اختياري)
  - إنتاج لكل توقع:
    - Force Plot (أهم 5 عوامل)
    - Summary Plot (أسبوعي)
  - تخزين التفسير في `predictions.shap_explanation`
- [ ] تكامل SHAP مع Dashboard:
  - عرض Force Plot في صفحة التنبؤ
  - عرض Summary Plot في صفحة الأداء
- [ ] تكامل SHAP مع API:
  - `GET /api/v1/model/explanation/{id}` يعيد SHAP values

**مخرجات المرحلة 8:**
✅ نموذج هجين 3 مسارات
✅ طريقة دمج مختارة ومقيمة
✅ FCM Clustering (اختياري)
✅ SHAP تفسيري في Dashboard + API
✅ تحسن معنوي عن Baseline (DM Test)

---

## المرحلة 9: MLOps والنضج (الأسبوع 37-42)

### 9.1 MLflow (الأسبوع 37-38)

- [ ] تثبيت وإعداد MLflow Server
- [ ] تسجيل جميع التجارب السابقة
- [ ] Model Registry:
  - تسجيل كل نموذج مع المعلمات والمقاييس
  - مراحل: Staging → Production
  - Rollback عند تراجع الأداء
- [ ] تتبع التجارب الجديدة تلقائيًا

### 9.2 CI/CD Pipeline (الأسبوع 39)

- [ ] GitHub Actions أو GitLab CI:
  - عند كل Push:
    - تشغيل Unit Tests
    - تشغيل Lint (ruff/flake8)
    - Type Check (mypy)
  - عند Merge to main:
    - Integration Tests
    - Build Docker Image
    - Push to Registry
  - عند Tag/Release:
    - Deploy to Staging
    - Smoke Tests
    - Manual Approval → Deploy to Production

### 9.3 التقارير التلقائية (الأسبوع 40)

- [ ] إنشاء `src/presentation/reports/generator.py`:
  - **تقرير يومي** (آلي):
    - ملخص التوقعات ومقارنة بالفعلي
    - أهم الأحداث
    - مؤشر المشاعر
  - **تقرير أسبوعي** (آلي):
    - MAE/MAPE الأسبوعي
    - مقارنة نماذج
    - أفضل/أسوأ توقع
  - **تقرير شهري**:
    - تقييم شامل
    - توصيات تحسين
    - حالة البنية التحتية
  - إرسال عبر Telegram Bot أو Email

### 9.4 توسيع الأصول (الأسبوع 41-42)

- [ ] إضافة توقع سعر الذهب بالليرة (اختياري)
- [ ] إضافة توقع المحروقات (اختياري)
- [ ] تحسين Dashboard بناءً على ملاحظات المستخدمين

**مخرجات المرحلة 9:**
✅ MLflow يعمل مع Model Registry
✅ CI/CD Pipeline
✅ تقارير تلقائية (يومية/أسبوعية)
✅ نظام ناضج قابل للصيانة

---

## المرحلة 10: نماذج متقدمة (الأسبوع 43-52) — اختياري

### 10.1 تفكيك الإشارة OCEEMDAN

- [ ] تطبيق CEEMDAN على سلسلة الأسعار
- [ ] تحسين معلمات الضوضاء بـ GWO
- [ ] نمذجة المكونات: FNN (عالي التردد) + GRU (متوسط) + Bi-LSTM (منخفض)
- [ ] دمج بأوزان ZOA ديناميكية
- [ ] مقارنة مع النموذج الهجين الحالي

### 10.2 Temporal Fusion Transformer (TFT) — النموذج الرئيسي من ACTION-main

> **TFT هو النموذج المركزي في ACTION-main** - دعنا نستكشف كيف يمكن تطبيقه على الفوركس السوري.

- [ ] **فهم بنية TFT من ACTION-main** (`old_code/scripts/model.py`):
  ```
  CustomTemporalFusionTransformer:
    ├── Variable Selection Networks (VSN)
    │   ├── Static: Sector (في حالتنا: لا يوجد)
    │   ├── Time-Varying Known: Day_of_Week, Month, Hour
    │   └── Time-Varying Unknown: Close, Indicators, Sentiment
    ├── LSTM Encoder-Decoder
    │   ├── Encoder: 180 timesteps (max_encoder_length)
    │   └── Decoder: 60 timesteps (max_prediction_length)
    ├── Multi-Head Attention (4 heads)
    ├── Gated Residual Networks (GRN)
    └── Quantile Output (0.1, 0.5, 0.9)
  ```

- [ ] **تكييف TFT للفوركس السوري**:
  - **إزالة**: `static_categoricals` (لا sector في الفوركس)
  - **إزالة**: `Volume`, `VWAP` (غير موثوقة في سوق غير رسمي)
  - **إضافة**:
    - `sentiment_score` كـ time-varying unknown
    - `event_weight` كـ time-varying unknown
    - `gold_price_pct`, `oil_price_pct`, `dxy_pct` كـ time-varying unknown
    - `session_overlap` كـ time-varying known categorical
    - `is_ramadan`, `is_holiday` كـ time-varying known categorical
  
- [ ] **معلمات مقترحة للفوركس**:
  ```yaml
  tft_forex:
    # البيانات
    max_encoder_length: 168  # 7 أيام × 24 ساعة
    max_prediction_length: 24  # 24 ساعة
    min_encoder_length: 24
    
    # بنية النموذج (من ACTION-main مُعدّلة)
    hidden_size: 128  # نفس ACTION-main
    attention_head_size: 4  # نفس ACTION-main
    lstm_layers: 2  # نفس ACTION-main
    dropout: 0.3  # نفس ACTION-main
    hidden_continuous_size: 16  # أصغر من ACTION-main (8→16)
    
    # دالة الخسارة
    loss: QuantileLoss
    quantiles: [0.05, 0.25, 0.5, 0.75, 0.95]  # أوسع من ACTION-main
    
    # التدريب
    learning_rate: 0.001  # نفس ACTION-main
    reduce_on_plateau_patience: 4
    batch_size: auto  # من batch_size_estimator.py
  ```

- [ ] **عملية التدريب** (من `old_code/scripts/train.py`):
  1. تحميل بيانات من InfluxDB → DataFrame
  2. Feature Engineering (من `feature_engineer.py`)
  3. إنشاء `TimeSeriesDataSet`:
     ```python
     training = TimeSeriesDataSet(
         data=train_df,
         time_idx="time_idx",  # رقم ترتيبي لكل ساعة
         target="Relative_Returns",  # العائد النسبي (مثل ACTION-main)
         group_ids=["ticker"],  # في حالتنا: ["currency_pair"]
         max_encoder_length=168,
         max_prediction_length=24,
         time_varying_known_categoricals=["Hour", "Day_of_Week", ...],
         time_varying_unknown_reals=["Close", "RSI", "sentiment_score", ...],
         target_normalizer=TorchNormalizer(),  # من ACTION-main
         add_relative_time_idx=True,
         add_target_scales=True,
         add_encoder_length=True,
         allow_missing_timesteps=True,  # مهم للفجوات
     )
     ```
  4. Optuna Hyperparameter Search (5-20 تجربة):
     ```python
     study = optuna.create_study(direction="minimize")
     study.optimize(objective, n_trials=20, show_progress_bar=True)
     best_params = study.best_params
     ```
  5. تدريب النموذج النهائي مع أفضل hyperparameters
  6. حفظ checkpoint + normalizers في `models/`

- [ ] **تقييم TFT**:
  - Quantile Coverage: هل 90% من القيم الفعلية تقع بين Q0.05 و Q0.95؟
  - MAPE على median (Q0.5)
  - Directional Accuracy
  - مقارنة مع LSTM/XGBoost/Hybrid

- [ ] **Feature Importance من TFT** (من ACTION-main):
  ```python
  # TFT يوفر attention weights لكل ميزة
  interpretation = best_model.interpret_output(
      val_dataloader.dataset[0:100],
      reduction="mean"
  )
  
  # رسم أهم الميزات
  feature_importance = interpretation["attention"].mean(0)
  plot_feature_importance(feature_importance)  # من plot_utils.py
  ```

- [ ] **Explainability إضافية**:
  - SHAP values على توقعات TFT
  - Attention visualization: ما هي الساعات الأكثر تأثيراً؟
  - Variable Selection: ما هي الميزات التي يختارها VSN؟

**الفائدة الكبرى لـ TFT في حالتنا**:
- يتعامل مع **multiple time scales** (ساعي، يومي، أسبوعي) بشكل طبيعي
- **Attention mechanism** يتعلم أي فترات زمنية مهمة (مثلاً: بداية جلسة لندن)
- **Quantile predictions** توفر نطاقات ثقة دون الحاجة لـ Monte Carlo
- **Variable Selection** يحدد الميزات المهمة تلقائياً
- **Handles missing data** بفضل `allow_missing_timesteps`

> **ملاحظة حاسمة**: في ACTION-main، TFT تنبأ بـ `Relative_Returns` وليس السعر المطلق. نفعل نفس الشيء:
> ```python
> df['Relative_Returns'] = df.groupby('ticker')['Close'].pct_change()
> target = "Relative_Returns"
> # للحصول على السعر النهائي: price_t+1 = price_t * (1 + predicted_return)
> ```

- [ ] **TSMixer كبديل** (اختياري):
  - أبسط من TFT
  - أسرع في التدريب
  - لكن أقل قوة في التعامل مع البيانات المعقدة

### 10.3 LLM لتصفية الضوضاء

- [ ] اختيار نموذج LLM (عربي أو متعدد اللغات)
- [ ] تصفية نصوص الأخبار: استخراج الأجزاء المتعلقة بسعر الصرف فقط
- [ ] توليد ميزات نصية محسنة
- [ ] مقارنة مع Naïve Bayes + DL

### 10.4 Grad-CAM

- [ ] تطبيق Grad-CAM على نماذج CNN/Transformer
- [ ] تحديد الفترات الزمنية الأكثر تأثيرًا
- [ ] دمج في Dashboard

**مخرجات المرحلة 10:**
✅ OCEEMDAN + FNN/GRU/Bi-LSTM (اختياري)
✅ TFT مُدرَّب على بيانات الفوركس السوري
✅ TSMixer كبديل (اختياري)
✅ LLM لتصفية الضوضاء (اختياري)
✅ Grad-CAM للتفسير (اختياري)
✅ مقارنة شاملة لجميع النماذج

---

## ملخص الدروس الحاسمة من ACTION-main

### 🎯 الدروس الخمسة الذهبية

1. **Gap الزمني في التقسيم** ⏱️
   - **ما هو**: فجوة 10 أيام (أو 24 ساعة) بين Train و Validation
   - **لماذا**: منع Data Leakage — النموذج لا يرى "المستقبل القريب"
   - **الكود** (`old_code/scripts/preprocessor.py`):
     ```python
     split_date = min_date + Timedelta(days=0.8 * total_days)
     val_start = split_date + Timedelta(days=gap_days + 1)  # gap=10
     train = df[df['Date'] < split_date]
     val = df[df['Date'] >= val_start]
     ```
   - **تطبيقنا**: نستخدم 24 ساعة gap في البيانات الساعية

2. **Log1p Transform قبل التطبيع** 📊
   - **ما هو**: `np.log1p(x)` يُطبق على Close, Volume, MA10, MA50, VWAP
   - **لماذا**: يُحسّن توزيع البيانات المائلة (skewed) بشكل كبير
   - **الكود** (`old_code/scripts/preprocessor.py`):
     ```python
     for feature in ['Close', 'Volume', 'MA10', 'MA50', 'VWAP']:
         df[feature] = np.log1p(df[feature].clip(lower=0))
     ```
   - **تطبيقنا**: نطبقه على Close, MA10, MA50 (لا Volume/VWAP)

3. **Quantile Loss بدلاً من MSE** 📈
   - **ما هو**: التنبؤ بنطاقات ثقة (Q0.1, Q0.5, Q0.9) بدلاً من نقطة واحدة
   - **لماذا**: يوفر uncertainty estimation دون Monte Carlo
   - **الكود** (`old_code/scripts/utils/model_config.py`):
     ```python
     loss = QuantileLoss(quantiles=[0.1, 0.5, 0.9])
     ```
   - **تطبيقنا**: نوسع إلى [0.05, 0.25, 0.5, 0.75, 0.95] لمزيد من الدقة

4. **Async Data Fetching** ⚡
   - **ما هو**: جمع بيانات متوازي باستخدام `asyncio` + `ThreadPoolExecutor`
   - **لماذا**: ACTION-main جمع 50+ ticker في دقائق بدلاً من ساعات
   - **الكود** (`old_code/scripts/data_fetcher.py`):
     ```python
     async def fetch_all_stocks(tickers):
         loop = asyncio.get_event_loop()
         with ThreadPoolExecutor(max_workers=10) as executor:
             tasks = [loop.run_in_executor(executor, fetch_stock, t) for t in tickers]
             results = await asyncio.gather(*tasks, return_exceptions=True)
         return results
     ```
   - **تطبيقنا**: نطبقه على جمع RSS/Telegram/Web متوازي

5. **Batch Size Estimation التلقائي** 🚀
   - **ما هو**: تحديد أكبر batch size ممكن دون OOM
   - **لماذا**: استخدام أمثل لـ GPU memory
   - **الكود** (`old_code/scripts/utils/batch_size_estimator.py`):
     ```python
     def estimate_batch_size(model, sample_batch, device):
         batch_size = 8
         while batch_size <= 512:
             try:
                 test_batch = sample_batch[:batch_size]
                 model(test_batch)
                 batch_size *= 2
             except RuntimeError:  # OOM
                 return batch_size // 2
     ```
   - **تطبيقنا**: نستخدمه مباشرة (خاصة مع TFT)

### 📚 ملفات الكود الأساسية للرجوع إليها

| الملف | الغرض | ما نأخذه منه |
|---|---|---|
| `old_code/scripts/model.py` | تعريف CustomTFT | بنية TFT كاملة + متغيرات الإدخال |
| `old_code/scripts/train.py` | حلقة التدريب | Optuna integration + Early Stopping |
| `old_code/scripts/preprocessor.py` | معالجة البيانات | Gap التقسيم + Log1p + TorchNormalizer |
| `old_code/scripts/data_fetcher.py` | جمع البيانات | Async pattern + Retry logic |
| `old_code/scripts/utils/feature_engineer.py` | هندسة الميزات | 12 مؤشر فني + Time Dummies |
| `old_code/scripts/utils/model_config.py` | إعدادات النموذج | Quantile Loss + HyperparamFactory |
| `old_code/scripts/utils/batch_size_estimator.py` | تقدير Batch Size | منع OOM + استخدام أمثل للGPU |
| `old_code/app/benchmark_utils.py` | Backtesting | تقييم شامل + نوافذ متدحرجة |
| `old_code/app/plot_utils.py` | الرسوم | مخططات Plotly تفاعلية |
| `old_code/app/app.py` | Streamlit UI | هيكلة Dashboard |
| `old_code/config/config.yaml` | الإعدادات | بنية ملف الإعدادات |

### 🔧 خطوات نقل الكود من ACTION-main

**للبدء السريع**، استخدم هذه الملفات مباشرة:

```bash
# 1. نسخ الأدوات المساعدة (100% قابلة لإعادة الاستخدام)
cp old_code/scripts/utils/batch_size_estimator.py src/utils/
cp old_code/scripts/utils/validation_utils.py src/utils/

# 2. نسخ بنية TFT (تحتاج تعديل بسيط)
cp old_code/scripts/model.py src/prediction/models/tft_model.py
# ثم عدّل: أزل static_categoricals, أزل Volume/VWAP, أضف sentiment

# 3. نسخ Optuna optimizer (تحتاج تعديل Hyperparams)
cp old_code/scripts/train.py src/prediction/training/train_tft.py
# ثم عدّل: نطاقات البحث للفوركس

# 4. نسخ TorchNormalizer pattern
# انسخ فقط الكود ذي الصلة من old_code/scripts/preprocessor.py

# 5. نسخ Plotly charts (تحتاج تعريب)
cp old_code/app/plot_utils.py src/presentation/dashboard/
# ثم عدّل: أضف دعم RTL للعربية
```

**التعديلات المطلوبة**:

| الملف | التعديل الرئيسي |
|---|---|
| `tft_model.py` | إزالة `static_categoricals`, `Volume`, `VWAP`; إضافة `sentiment_score`, `event_weight` |
| `train_tft.py` | تعديل hyperparameter ranges: `max_encoder_length=168`, `max_prediction_length=24` |
| `preprocessor.py` | تغيير التردد من يومي `'D'` إلى ساعي `'H'`; إضافة معالجة الفجوات السورية |
| `plot_utils.py` | إضافة `arabic-reshaper` + `python-bidi` لدعم RTL |
| `config.yaml` | تعديل جميع القيم للفوركس السوري |

### 🚨 الأخطاء الشائعة المستخلصة من ACTION-main

**تجنب هذه الأخطاء**:

1. ❌ **نسيان Gap في التقسيم** → Data Leakage → أرقام ممتازة في التدريب، سيئة في الإنتاج
2. ❌ **عدم معالجة NaN** → RuntimeError في TFT → استخدم `ffill() + bfill() + fillna(0)`
3. ❌ **OOM في GPU** → استخدم `batch_size_estimator.py`
4. ❌ **تطبيع بدون Log1p** → توزيع سيء → MAPE أعلى بـ 2-3%
5. ❌ **MSE Loss في السلاسل الزمنية** → لا uncertainty → استخدم `QuantileLoss`
6. ❌ **target = السعر المطلق** → صعب التنبؤ → استخدم `Relative_Returns = pct_change()`
7. ❌ **عدم حفظ Normalizers** → لا يمكن inference → احفظ `.pkl` مع الموديل
8. ❌ **Validation على نفس Ticker في التدريب** → تسرب → قسم حسب `time` وليس `random`

---

## ملخص الجدول الزمني

| المرحلة | الأسابيع | المخرج الرئيسي |
|---|---|---|
| 0: التهيئة | 1-2 | بنية تحتية + هيكل مشروع |
| 1: جمع البيانات | 3-6 | 5+ مصادر تجمع آليًا |
| 2: المعالجة | 7-10 | Pipeline: تنظيف + تصنيف + مشاعر |
| 3: الميزات | 11-12 | Feature Store مع Time Dummies |
| 4: النماذج | 13-16 | XGBoost + HLT + تنبؤ يومي |
| 5: الواجهات | 17-20 | Dashboard + API + تنبيهات |
| 6: التغذية الراجعة | 21-22 | Feedback + Drift Monitor |
| 7: NLP المتقدم | 23-30 | DL Sentiment + Optuna |
| 8: الهجين | 31-36 | 3 مسارات + SHAP |
| 9: MLOps | 37-42 | MLflow + CI/CD + تقارير |
| 10: متقدم | 43-52 | OCEEMDAN + TFT + LLM |

---

## استراتيجية التنفيذ الموصى بها

### المسار السريع (Minimum Viable Product — 16 أسبوع)

إذا كنت تريد نظاماً يعمل بسرعة، اتبع هذا المسار:

**الأسابيع 1-6**: المراحل 0-1 (بنية تحتية + جمع bيانات)
- هدف: 3+ مصادر تجمع آليًا (RSS + Web + Telegram)
- تخطى: APIs الخارجية في البداية (أضفها لاحقاً)

**الأسابيع 7-10**: المرحلة 2 (معالجة مبسطة)
- هدف: تنظيف + استخراج أسعار فقط
- تخطى: تصنيف أحداث وتحليل مشاعر (نضيفها في v2.0)

**الأسابيع 11-12**: المرحلة 3 (ميزات أساسية)  
- هدف: MA10, MA50, RSI, MACD, Time Dummies
- تخطى: Mutual Information selection في البداية

**الأسابيع 13-16**: المرحلة 4 (نموذج واحد فقط)
- هدف: **XGBoost فقط** (MAPE < 5%)
- تخطى: HLT/ARIMA/Hybrid في البداية
- أضف Dashboard بسيط (Streamlit)

**النتيجة بعد 16 أسبوع**:
✅ نظام يجمع أسعار تلقائياً
✅ XGBoost يتنبأ بالسعر بدقة معقولة
✅ Dashboard يعرض التوقعات
✅ أساس قوي للتوسع

---

### المسار المتكامل (Full Featured — 42 أسبوع)

لنظام احترافي كامل:

**القدرات الرئيسية**:
1. جمع من 10+ مصادر (المراحل 0-1)
2. NLP عربي للمشاعر (المراحل 2-7)
3. نموذج هجين 3 مسارات (المرحلة 8)
4. MLOps كامل (المرحلة 9)
5. Dashboard احترافي + API

**الجدول الزمني**: كما هو موضح في الخطة (42 أسبوع)

---

### المسار البحثي (State-of-the-Art — 52 أسبوع)

لأفضل دقة ممكنة:

**يضيف على المسار المتكامل**:
- OCEEMDAN signal decomposition
- Temporal Fusion Transformer
- LLM للتصفية
- Grad-CAM للتفسير

**الجدول الزمني**: 52 أسبوع (المرحلة 10 كاملة)

---

## قواعد تنفيذ عامة

1. **اكتب الاختبارات أولاً** قبل الكود (أو بالتوازي) — لا تتقدم بدون اختبارات.
2. **لا تنتقل لمرحلة جديدة** حتى تستقر المرحلة الحالية (48 ساعة بدون أخطاء).
3. **وثّق كل قرار تصميمي** في ملف `docs/decisions.md`.
4. **استخدم Git بانتظام** — commit كل تغيير ذي معنى مع رسالة واضحة.
5. **قس كل شيء** — لا تفترض أن شيئًا يعمل بدون أرقام.
6. **ابدأ بسيطًا ثم عقّد** — Naïve Bayes قبل LSTM قبل TFT.
7. **التقسيم الزمني صارم** — لا تسمح أبدًا بتسرب بيانات مستقبلية.
8. **سجّل كل تجربة** في MLflow أو حتى في ملف CSV.
9. **راجع الكود** قبل دمجه — حتى لو كنت المطور الوحيد.
10. **أمّن بيانات الاعتماد** — لا tokens أو passwords في الكود.

---

*آخر تحديث: مارس 2026*