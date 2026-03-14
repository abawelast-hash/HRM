# 📚 دليل API - نظام شامِن
## ShamIn API Documentation

**الإصدار:** 1.0.0-beta  
**تاريخ التحديث:** 2026-03-14  
**Base URL:** `http://187.77.173.160:8000`

---

## 📋 الفهرس

1. [نظرة عامة](#نظرة-عامة)
2. [المصادقة](#المصادقة)
3. [نقاط النهاية](#نقاط-النهاية)
4. [رموز الاستجابة](#رموز-الاستجابة)
5. [أمثلة الاستخدام](#أمثلة-الاستخدام)
6. [الأخطاء الشائعة](#الأخطاء-الشائعة)

---

## نظرة عامة

ShamIn API هو واجهة برمجية RESTful للتحكم في نظام جمع وتحليل بيانات سعر صرف الليرة السورية.

### الميزات
- 🔄 تشغيل محركات جمع البيانات يدوياً
- 📊 عرض إحصائيات وسجلات
- 📈 جلب الأسعار والتنبؤات (قريباً)
- ⚙️ إدارة المصادر (قريباً)

### Headers الأساسية
```http
Accept: application/json
Content-Type: application/json
```

---

## المصادقة

> 📌 **ملاحظة:** الإصدار الحالي لا يتطلب مصادقة. سيتم إضافتها في الإصدار القادم.

---

## نقاط النهاية

### 1. الصحة والحالة

#### GET /
معلومات أساسية عن التطبيق.

**الاستجابة:**
```json
{
  "app": "ShamIn",
  "status": "running",
  "version": "1.0.0-beta"
}
```

---

#### GET /health
فحص صحة النظام.

**الاستجابة:**
```json
{
  "status": "healthy"
}
```

---

### 2. مهام جمع البيانات

#### POST /tasks/collect/rss
تشغيل جمع بيانات RSS.

**الطلب:**
```http
POST /tasks/collect/rss
```

**الاستجابة:**
```json
{
  "status": "success",
  "task": "rss_collection",
  "timestamp": "2026-03-14T09:57:15.655686",
  "result": {
    "status": "success",
    "sources_total": 5,
    "sources_successful": 1,
    "articles_collected": 19,
    "details": [
      {
        "source": "enab_baladi",
        "count": 19,
        "success": true
      },
      {
        "source": "reuters_meast",
        "count": 0,
        "success": false
      }
    ]
  }
}
```

---

#### POST /tasks/collect/web-prices
تشغيل جمع أسعار من المواقع.

**الطلب:**
```http
POST /tasks/collect/web-prices
```

**الاستجابة:**
```json
{
  "status": "success",
  "task": "web_prices_collection",
  "timestamp": "2026-03-14T09:57:53.408866",
  "result": {
    "status": "success",
    "sources_total": 1,
    "sources_successful": 1,
    "prices_collected": 1,
    "details": [
      {
        "source": "investing-com",
        "price": 115.5,
        "success": true
      }
    ]
  }
}
```

---

#### POST /tasks/collect/telegram-prices
تشغيل جمع أسعار من تلغرام.

**الطلب:**
```http
POST /tasks/collect/telegram-prices
```

**الاستجابة:**
```json
{
  "status": "success",
  "task": "telegram_prices_collection",
  "timestamp": "...",
  "result": {
    "channels_processed": 3,
    "messages_collected": 0,
    "prices_extracted": 0
  }
}
```

---

#### POST /tasks/collect/telegram-news
تشغيل جمع أخبار من تلغرام.

**الطلب:**
```http
POST /tasks/collect/telegram-news
```

---

#### POST /tasks/collect/external-indicators
تشغيل جمع المؤشرات الخارجية (ذهب، نفط، DXY).

**الطلب:**
```http
POST /tasks/collect/external-indicators
```

---

#### POST /tasks/collect/all
تشغيل جميع محركات الجمع معاً.

**الطلب:**
```http
POST /tasks/collect/all
```

**الاستجابة:**
```json
{
  "status": "success",
  "task": "all_collection",
  "results": {
    "rss": { ... },
    "web_prices": { ... },
    "telegram_prices": { ... },
    "telegram_news": { ... },
    "external_indicators": { ... }
  }
}
```

---

### 3. الإحصائيات والسجلات

#### GET /tasks/stats/recent
إحصائيات آخر عمليات الجمع.

**الاستجابة:**
```json
{
  "total_collections": 10,
  "successful": 8,
  "failed": 2,
  "last_collection": "2026-03-14T09:57:53",
  "by_source": {
    "rss": { "success": 5, "failed": 1 },
    "web": { "success": 2, "failed": 0 },
    "telegram": { "success": 1, "failed": 1 }
  }
}
```

---

#### GET /tasks/logs/recent
آخر سجلات النظام.

**Parameters:**
| المعامل | النوع | الافتراضي | الوصف |
|---------|------|-----------|-------|
| limit | int | 100 | عدد السجلات |
| level | str | all | مستوى السجل (info, warning, error) |

**الاستجابة:**
```json
{
  "status": "success",
  "logs": [
    {
      "timestamp": "2026-03-14T09:57:15",
      "level": "INFO",
      "message": "RSS collection started",
      "source": "enab_baladi"
    }
  ]
}
```

---

### 4. البيانات المجمعة

#### GET /tasks/data/raw-texts
جلب النصوص المجمعة من قاعدة البيانات.

**Parameters:**
| المعامل | النوع | الافتراضي | الوصف |
|---------|------|-----------|-------|
| source_type | str | null | نوع المصدر (rss, telegram, web) |
| limit | int | 100 | عدد السجلات (الحد الأقصى 500) |
| offset | int | 0 | إزاحة البداية |

**الاستجابة:**
```json
{
  "status": "success",
  "timestamp": "2026-03-14T10:24:33.568973",
  "data": [
    {
      "id": 119,
      "source_type": "rss",
      "title": "عنوان الخبر",
      "content": "محتوى الخبر...",
      "url": "https://...",
      "metadata": {
        "source": "rt_arabic",
        "language": "ar",
        "published_at": "2026-03-13 19:58:45+00:00"
      },
      "created_at": "2026-03-14T10:24:17.169225"
    }
  ],
  "pagination": {
    "total": 119,
    "limit": 100,
    "offset": 0,
    "has_more": true
  }
}
```

---

#### GET /tasks/data/raw-texts/{id}
جلب نص محدد بالمعرف.

**Parameters:**
| المعامل | النوع | الوصف |
|---------|------|-------|
| id | int | معرف النص |

**الاستجابة:**
```json
{
  "status": "success",
  "timestamp": "2026-03-14T10:30:00.000000",
  "data": {
    "id": 1,
    "source_type": "rss",
    "title": "العنوان الكامل",
    "content": "المحتوى الكامل...",
    "url": "https://...",
    "metadata": {...},
    "created_at": "2026-03-14T10:24:17.000000"
  }
}
```

---

#### GET /tasks/data/search
البحث في النصوص المجمعة.

**Parameters:**
| المعامل | النوع | الافتراضي | الوصف |
|---------|------|-----------|-------|
| q | str | مطلوب | نص البحث (الحد الأدنى حرفين) |
| limit | int | 50 | عدد النتائج (الحد الأقصى 100) |

**الاستجابة:**
```json
{
  "status": "success",
  "timestamp": "2026-03-14T10:35:00.000000",
  "query": "سعر الصرف",
  "data": [
    {
      "id": 50,
      "source_type": "rss",
      "title": "تحليل سعر الصرف",
      "content": "...",
      "created_at": "2026-03-14T10:00:00.000000"
    }
  ],
  "count": 15
}
```

---

#### GET /tasks/data/stats
إحصائيات البيانات المجمعة.

**الاستجابة:**
```json
{
  "status": "success",
  "timestamp": "2026-03-14T10:24:27.068267",
  "stats": {
    "total_texts": 119,
    "by_source": [
      {"source_type": "rss", "count": 119}
    ],
    "by_day": [
      {"date": "2026-03-14", "count": 119}
    ],
    "last_collected": "2026-03-14T10:24:17.169225"
  }
}
```

---

## رموز الاستجابة

| الرمز | الوصف |
|-------|-------|
| 200 | نجاح |
| 201 | تم الإنشاء |
| 400 | طلب غير صالح |
| 401 | غير مصرح |
| 404 | غير موجود |
| 422 | خطأ في التحقق |
| 500 | خطأ داخلي |

---

## أمثلة الاستخدام

### Python
```python
import requests

# جمع RSS
response = requests.post("http://187.77.173.160:8000/tasks/collect/rss")
print(response.json())

# فحص الصحة
health = requests.get("http://187.77.173.160:8000/health")
print(health.json())
```

### cURL
```bash
# جمع RSS
curl -X POST http://187.77.173.160:8000/tasks/collect/rss

# جمع أسعار الويب
curl -X POST http://187.77.173.160:8000/tasks/collect/web-prices

# فحص الصحة
curl http://187.77.173.160:8000/health
```

### JavaScript
```javascript
// جمع RSS
fetch('http://187.77.173.160:8000/tasks/collect/rss', {
  method: 'POST'
})
.then(res => res.json())
.then(data => console.log(data));
```

---

## الأخطاء الشائعة

### 404 - Not Found
```json
{
  "detail": "Not Found"
}
```
**السبب:** نقطة النهاية غير موجودة.

### 422 - Validation Error
```json
{
  "detail": [
    {
      "loc": ["body", "field_name"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```
**السبب:** بيانات الطلب غير صالحة.

### 500 - Internal Server Error
```json
{
  "detail": "Internal server error"
}
```
**السبب:** خطأ في الخادم. تحقق من السجلات.

---

## 📖 المزيد

- **Swagger UI:** http://187.77.173.160:8000/docs
- **ReDoc:** http://187.77.173.160:8000/redoc
- **OpenAPI JSON:** http://187.77.173.160:8000/openapi.json

---

*آخر تحديث: 2026-03-14*
