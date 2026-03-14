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
