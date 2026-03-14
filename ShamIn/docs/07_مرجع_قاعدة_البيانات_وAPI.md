# مرجع قاعدة البيانات وواجهة API — مشروع ShamIn

---

## القسم الأول: مخطط قاعدة البيانات (PostgreSQL)

### نظرة عامة

المشروع يستخدم 7 جداول مترابطة:

```
sources ──1:N──→ raw_news ──1:1──→ processed_news
                                        │
                                   classified_events
                                        
predictions ←── model_performance
                                        
drift_monitoring (مستقل)
```

---

### جدول 1: `sources` — مصادر البيانات

| العمود | النوع | القيود | الوصف |
|--------|-------|--------|-------|
| `id` | `INTEGER` | PRIMARY KEY, AUTO | معرف تسلسلي |
| `name` | `VARCHAR(255)` | UNIQUE, NOT NULL | اسم فريد للمصدر |
| `type` | `VARCHAR(50)` | NOT NULL | نوع: `rss`, `telegram`, `web`, `api` |
| `url` | `TEXT` | — | رابط المصدر |
| `frequency_minutes` | `INTEGER` | DEFAULT 15 | تردد الجمع |
| `is_active` | `BOOLEAN` | DEFAULT TRUE | مفعل أم لا |
| `last_fetch` | `TIMESTAMP` | — | آخر جمع ناجح |
| `config` | `JSONB` | — | إعدادات إضافية (CSS selector, regex...) |
| `created_at` | `TIMESTAMP` | DEFAULT NOW | وقت الإنشاء |

**الفهارس**: `name` (UNIQUE)

**مثال إدخال**:
```sql
INSERT INTO sources (name, type, url, frequency_minutes)
VALUES ('enab_baladi', 'rss', 'https://www.enabbaladi.net/feed', 15);
```

---

### جدول 2: `raw_news` — الأخبار الخام

| العمود | النوع | القيود | الوصف |
|--------|-------|--------|-------|
| `id` | `UUID` | PRIMARY KEY | معرف فريد عالمي |
| `source_id` | `INTEGER` | FOREIGN KEY → sources.id | مصدر الخبر |
| `source_type` | `VARCHAR(50)` | NOT NULL | نوع المصدر |
| `timestamp` | `TIMESTAMP` | NOT NULL, INDEX | وقت الخبر الأصلي |
| `raw_text` | `TEXT` | NOT NULL | النص الكامل الخام |
| `raw_numeric` | `FLOAT` | — | قيمة رقمية (سعر) إن وُجدت |
| `language` | `VARCHAR(10)` | DEFAULT 'ar' | اللغة |
| `content_hash` | `VARCHAR(64)` | UNIQUE, INDEX | بصمة SHA-256 (لمنع التكرار) |
| `metadata` | `JSONB` | — | بيانات إضافية |
| `created_at` | `TIMESTAMP` | DEFAULT NOW | وقت التخزين |

**الفهارس**: `timestamp` (B-Tree), `content_hash` (UNIQUE)

**مثال استعلام**:
```sql
-- آخر 50 خبر من تلغرام
SELECT * FROM raw_news 
WHERE source_type = 'telegram' 
ORDER BY timestamp DESC 
LIMIT 50;
```

---

### جدول 3: `processed_news` — الأخبار المعالجة

| العمود | النوع | القيود | الوصف |
|--------|-------|--------|-------|
| `id` | `UUID` | PRIMARY KEY | نفس معرف raw_news |
| `cleaned_text` | `TEXT` | — | النص بعد التنظيف (8 خطوات) |
| `extracted_price` | `FLOAT` | — | السعر المُستخرج من النص |
| `event_category` | `VARCHAR(50)` | — | التصنيف: military, political, economic, social |
| `event_weight` | `FLOAT` | — | وزن الحدث (0.0 - 1.0) |
| `sentiment` | `VARCHAR(20)` | — | المشاعر: positive, negative, neutral |
| `sentiment_score` | `FLOAT` | — | درجة المشاعر (-1.0 إلى 1.0) |
| `embedding_vector` | `JSONB` | — | متجه التمثيل الرقمي (64 بُعد) |
| `processing_timestamp` | `TIMESTAMP` | — | وقت المعالجة |
| `processing_version` | `VARCHAR(20)` | — | إصدار خط المعالجة |

**مثال استعلام**:
```sql
-- أخبار عسكرية بوزن عالٍ
SELECT cleaned_text, event_weight, sentiment 
FROM processed_news 
WHERE event_category = 'military' AND event_weight > 0.7
ORDER BY processing_timestamp DESC;
```

---

### جدول 4: `predictions` — التنبؤات

| العمود | النوع | القيود | الوصف |
|--------|-------|--------|-------|
| `id` | `UUID` | PRIMARY KEY | معرف التنبؤ |
| `prediction_timestamp` | `TIMESTAMP` | NOT NULL, INDEX | وقت إجراء التنبؤ |
| `horizon_hours` | `INTEGER` | NOT NULL | أفق التنبؤ (24 أو 72 ساعة) |
| `predicted_price` | `FLOAT` | NOT NULL | السعر المتوقع |
| `predicted_direction` | `VARCHAR(20)` | — | up, down, stable |
| `confidence` | `FLOAT` | — | مستوى الثقة (0-1) |
| `q05` | `FLOAT` | — | الكمية 5% (حد أدنى شبه مؤكد) |
| `q25` | `FLOAT` | — | الكمية 25% |
| `q50` | `FLOAT` | — | الكمية 50% (الوسيط) |
| `q75` | `FLOAT` | — | الكمية 75% |
| `q95` | `FLOAT` | — | الكمية 95% (حد أقصى شبه مؤكد) |
| `top_features` | `JSONB` | — | أهم 10 ميزات مؤثرة |
| `shap_values` | `JSONB` | — | قيم SHAP للتفسير |
| `contributing_events` | `JSONB` | — | الأحداث المساهمة |
| `actual_price` | `FLOAT` | — | السعر الفعلي (يُملأ لاحقاً) |
| `error_mae` | `FLOAT` | — | الخطأ المطلق |
| `error_mape` | `FLOAT` | — | الخطأ النسبي |
| `direction_correct` | `BOOLEAN` | — | هل أصاب الاتجاه |
| `model_version` | `VARCHAR(50)` | — | إصدار النموذج |

**مثال**: تنبؤ بـ 5 كميات:
```
q05=14100  q25=14300  q50=14600  q75=14900  q95=15200
  ◄─────── نطاق الثقة 90% ────────►
         ◄── نطاق 50% ──►
```

---

### جدول 5: `model_performance` — أداء النماذج

| العمود | النوع | القيود | الوصف |
|--------|-------|--------|-------|
| `id` | `INTEGER` | PRIMARY KEY, AUTO | معرف |
| `model_name` | `VARCHAR(100)` | NOT NULL | اسم النموذج (tft, xgboost, hlt) |
| `model_version` | `VARCHAR(50)` | NOT NULL | إصدار (v1.0, v1.1...) |
| `mae` | `FLOAT` | — | Mean Absolute Error — متوسط الخطأ المطلق |
| `rmse` | `FLOAT` | — | Root Mean Squared Error — جذر متوسط مربع الخطأ |
| `mape` | `FLOAT` | — | Mean Absolute Percentage Error — نسبة الخطأ |
| `r2_score` | `FLOAT` | — | R² — معامل التحديد (1.0 = مثالي) |
| `directional_accuracy` | `FLOAT` | — | دقة تنبؤ الاتجاه (%) |
| `backtest_windows` | `INTEGER` | — | عدد نوافذ الاختبار الخلفي |
| `hyperparameters` | `JSONB` | — | المعاملات الفائقة المستخدمة |
| `tested_at` | `TIMESTAMP` | DEFAULT NOW | وقت الاختبار |

---

### جدول 6: `classified_events` — الأحداث المصنفة

| العمود | النوع | القيود | الوصف |
|--------|-------|--------|-------|
| `id` | `UUID` | PRIMARY KEY | معرف الحدث |
| `news_id` | `UUID` | FOREIGN KEY → raw_news.id | مرتبط بخبر |
| `category` | `VARCHAR(50)` | NOT NULL | military, political, economic, social |
| `weight` | `FLOAT` | DEFAULT 0.5 | الوزن (0-1) |
| `decay_applied` | `BOOLEAN` | DEFAULT FALSE | هل طُبق الاضمحلال |
| `impact_score` | `FLOAT` | — | درجة التأثير المُقاسة |
| `classified_at` | `TIMESTAMP` | DEFAULT NOW | وقت التصنيف |

---

### جدول 7: `drift_monitoring` — مراقبة الانجراف

| العمود | النوع | القيود | الوصف |
|--------|-------|--------|-------|
| `id` | `INTEGER` | PRIMARY KEY, AUTO | معرف |
| `drift_type` | `VARCHAR(50)` | NOT NULL | data_drift أو concept_drift |
| `feature_name` | `VARCHAR(100)` | — | اسم الميزة المرصودة |
| `ks_statistic` | `FLOAT` | — | إحصائية KS |
| `p_value` | `FLOAT` | — | القيمة الاحتمالية |
| `is_drift_detected` | `BOOLEAN` | DEFAULT FALSE | هل كُشف انجراف |
| `checked_at` | `TIMESTAMP` | DEFAULT NOW | وقت الفحص |

---

## القسم الثاني: InfluxDB — السلاسل الزمنية

### البنية

| المفهوم | القيمة | الوصف |
|---------|--------|-------|
| **Bucket** | `exchange_rates` | حاوية البيانات |
| **Measurement** | `exchange_rate` | نوع القياس |
| **Tag** | `source` | اسم المصدر (للفلترة) |
| **Field** | `price` | قيمة السعر |
| **Timestamp** | ISO 8601 | وقت القياس |

### كتابة بيانات (من الكود):
```python
from src.storage.timeseries_db import TimeSeriesDB

db = TimeSeriesDB()
db.write_price(
    bucket="exchange_rates",
    source="sp_today",
    price=14500.0,
    timestamp=datetime.utcnow()
)
```

### استعلام (Flux Query):
```flux
from(bucket: "exchange_rates")
  |> range(start: -24h)
  |> filter(fn: (r) => r._measurement == "exchange_rate")
  |> filter(fn: (r) => r.source == "sp_today")
```

---

## القسم الثالث: MinIO — التخزين الكائني

### البنية

| Bucket | المحتوى | الوصف |
|--------|---------|-------|
| `models` | ملفات `.pth` و `.pkl` | النماذج المُدربة |
| `data` | ملفات CSV و JSON | بيانات مُعالجة |
| `backups` | ملفات نسخ احتياطي | نسخ من PostgreSQL |

### مسار حفظ النماذج:
```
models/
├── tft/
│   ├── v1.0/
│   │   └── tft_v1.0.pth          # 120 MB
│   └── v1.1/
│       └── tft_v1.1.pth
├── xgboost/
│   └── v1.0/
│       └── xgboost_v1.0.pkl       # 5 MB
└── sentiment_lstm/
    └── v1.0/
        └── sentiment_lstm_v1.0.pth # 30 MB
```

### استخدام من الكود:
```python
from src.storage.object_store import ObjectStore

store = ObjectStore()

# حفظ نموذج
store.save_model("tft", model_bytes, version="v1.0")

# تحميل نموذج
data = store.load_model("tft/v1.0/tft_v1.0.pth")
```

---

## القسم الرابع: سجل النماذج (Model Registry)

### البنية (ملف JSON):
```json
{
    "models": {
        "tft": {
            "v1.0": {
                "metrics": {"mae": 120.5, "rmse": 180.2, "mape": 0.8},
                "path": "models/tft/v1.0/tft_v1.0.pth",
                "registered_at": "2024-01-15T10:30:00"
            },
            "v1.1": {
                "metrics": {"mae": 95.3, "rmse": 140.1, "mape": 0.6},
                "path": "models/tft/v1.1/tft_v1.1.pth",
                "registered_at": "2024-02-01T14:00:00"
            }
        }
    },
    "active": {
        "name": "tft",
        "version": "v1.1"
    }
}
```

---

## القسم الخامس: واجهة FastAPI

### نقاط النهاية الحالية

#### `GET /`
- **الوصف**: معلومات عامة عن التطبيق
- **المصادقة**: لا تحتاج
- **الاستجابة**:
```json
{
    "app": "ShamIn",
    "status": "running",
    "version": "1.0.0-beta"
}
```

#### `GET /health`
- **الوصف**: فحص صحة الخدمة
- **الاستجابة**:
```json
{"status": "healthy"}
```

### نقاط النهاية المخططة (مراحل لاحقة)

#### `GET /predictions/latest`
- **الوصف**: آخر تنبؤ
- **الاستجابة المتوقعة**:
```json
{
    "prediction_timestamp": "2024-01-15T10:00:00Z",
    "predicted_price": 14600.0,
    "direction": "up",
    "confidence": 0.85,
    "quantiles": {
        "q05": 14100, "q25": 14300,
        "q50": 14600, "q75": 14900, "q95": 15200
    },
    "horizon_hours": 24,
    "model_version": "v1.1"
}
```

#### `GET /predictions/history?days=7`
- **الوصف**: تاريخ التنبؤات
- **المعاملات**: `days` — عدد الأيام

#### `GET /events/latest?limit=10`
- **الوصف**: آخر الأحداث المصنفة

#### `GET /models/performance`
- **الوصف**: مقاييس أداء كل النماذج

#### `POST /predictions/custom`
- **الوصف**: تنبؤ مخصص بمعاملات محددة
- **الجسم**:
```json
{
    "horizon_hours": 48,
    "include_quantiles": true,
    "include_shap": true
}
```

### إعدادات CORS

```python
allow_origins=["*"]           # يقبل من أي مصدر
allow_methods=["*"]           # كل الطرق (GET, POST...)
allow_headers=["*"]           # كل الرؤوس
allow_credentials=True        # يقبل ملفات تعريف الارتباط
```

---

## القسم السادس: ملفات الإعدادات

### `config/settings.yaml`
```yaml
app:
  name: ShamIn
  version: 1.0.0-beta
  debug: false
  log_level: INFO

database:
  url: ${POSTGRES_URL}              # يُقرأ من .env
  pool_size: 10

influxdb:
  url: ${INFLUXDB_URL}
  token: ${INFLUXDB_TOKEN}
  org: ${INFLUXDB_ORG}
  bucket: exchange_rates

redis:
  url: ${REDIS_URL}

minio:
  endpoint: ${MINIO_ENDPOINT}
  access_key: ${MINIO_ACCESS_KEY}
  secret_key: ${MINIO_SECRET_KEY}
  secure: false
```

### `config/model_config.yaml` (ملخص)
```yaml
tft:
  hidden_size: 128
  lstm_layers: 2
  attention_heads: 4
  dropout: 0.3
  learning_rate: 0.001
  max_epochs: 100
  early_stopping_patience: 10
  quantiles: [0.05, 0.25, 0.5, 0.75, 0.95]
  max_encoder_length: 168        # أسبوع = 168 ساعة
  max_prediction_length: 72      # 3 أيام

xgboost:
  n_estimators: 500
  max_depth: 8
  learning_rate: 0.05

holt_winters:
  seasonal: true
  seasonal_periods: 24            # دورة يومية

ensemble:
  weights:
    tft: 0.60
    xgboost: 0.25
    hlt: 0.15
```

### `config/alerts.yaml`
```yaml
price_change:
  threshold_pct: 5.0             # تنبيه إذا تغير >5%
  window_hours: 1

military_event:
  weight_threshold: 0.8          # تنبيه إذا حدث عسكري بوزن >0.8

model_drift:
  ks_threshold: 0.1              # عتبة KS للانجراف
  check_interval_hours: 6

collection_failure:
  max_consecutive: 3             # تنبيه بعد 3 فشلات متتالية

notifications:
  telegram_bot_token: ${ALERT_BOT_TOKEN}
  telegram_chat_id: ${ALERT_CHAT_ID}
```
