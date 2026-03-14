# 🏛️ ShamIn - نظام التنبؤ الذكي بسعر الصرف

## 🚀 البدء السريع

### 1. تشغيل لوحة التحكم (الطريقة الأسهل)

**Windows:**
```cmd
start.bat
اختر [1] لوحة التحكم
```

**Linux/Mac:**
```bash
cd ShamIn
python run_dashboard.py
```

ثم افتح: **http://localhost:8501**

---

### 2. تشغيل محركات الجمع يدوياً

#### اذهب إلى صفحة "🔄 تشغيل ومراقبة"

**الميزات:**
- ✅ تشغيل كل محرك لوحده
- ✅ تشغيل جميع المحركات معاً  
- ✅ مشاهدة البيانات real-time
- ✅ إحصائيات فورية
- ✅ عرض الأخطاء والنجاحات

**المحركات المتاحة:**
1. **📰 RSS** - جمع المقالات من مصادر الأخبار
2. **💰 الأسعار** - جمع أسعار الصرف من المواقع
3. **📱 تلغرام أسعار** - قنوات الأسعار (يتطلب API)
4. **📱 تلغرام أخبار** - قنوات الأخبار (يتطلب API)
5. **🌍 المؤشرات** - البيانات الخارجية (قيد التطوير)
6. **🚀 الكل معاً** - تشغيل شامل

---

### 3. إضافة مصادر جديدة

#### اذهب إلى صفحة "➕ إدارة المصادر"

**يمكنك إضافة:**
- مصادر RSS جديدة (اسم + URL + تصنيف)
- مواقع أسعار (URL + طريقة الاستخراج)
- قنوات تلغرام (username + نوع المحتوى)

**الميزات:**
- ✅ اختبار المصدر قبل الإضافة
- ✅ تفعيل/تعطيل ديناميكي
- ✅ حذف المصادر
- ✅ الحفظ التلقائي

---

## 📊 ما ستراه

### في صفحة "تشغيل ومراقبة":

```
🔄 جاري جمع من: عنب بلدي (1/5)
✅ عنب بلدي: 12 مقال

🔄 جاري جمع من: رويترز (2/5)
✅ رويترز: 8 مقال

📊 الإحصائيات
━━━━━━━━━━━━━━━━
   48
مقال تم جمعه من 5/5 مصدر
```

### بيانات الأسعار:

```
🌐 جمع من: sp-today.com
✅ sp-today: 14,850 ل.س

🌐 جمع من: investing.com
✅ investing.com: 14,920 ل.س

💰 الأسعار المجموعة
━━━━━━━━━━━━━━━━━━━
sp-today: 14,850.00 ل.س (دمشق)
investing-com: 14,920.00 ل.س (رسمي)
central-bank-sy: 10,500.00 ل.س (رسمي)
```

---

## 🔧 إعداد Telegram (اختياري)

1. سجل في: https://my.telegram.org
2. احصل على:
   - `API_ID`
   - `API_HASH`
3. أضفهم في ملف `.env`:
   ```
   TELEGRAM_API_ID=123456
   TELEGRAM_API_HASH=abcdef123456
   ```
4. أعد تشغيل التطبيق

---

## 🎯 الاستخدام المتقدم

### تشغيل عبر API

```bash
# تشغيل API Server
cd ShamIn
python run_api.py
```

**Endpoints:**
```bash
# جمع RSS
curl -X POST http://localhost:8000/tasks/collect/rss

# جمع الأسعار
curl -X POST http://localhost:8000/tasks/collect/web-prices

# جمع الكل
curl -X POST http://localhost:8000/tasks/collect/all

# الإحصائيات
curl -X GET http://localhost:8000/tasks/stats/recent
```

**التوثيق الكامل:** http://localhost:8000/docs

---

## 📁 البنية

```
ShamIn/
├── run_dashboard.py          # تشغيل Dashboard
├── run_api.py                # تشغيل API
├── src/
│   ├── ingestion/
│   │   ├── collectors/
│   │   │   ├── rss_collector.py      ✅ جاهز
│   │   │   ├── web_scraper.py        ✅ جاهز
│   │   │   └── telegram_collector.py ⏳ يتطلب API
│   │   └── scheduler.py              ✅ Celery tasks
│   └── presentation/
│       ├── dashboard/app.py          ✅ لوحة التحكم
│       └── api/
│           ├── main.py               ✅ FastAPI
│           └── routes/tasks.py       ✅ Manual triggers
├── config/
│   └── sources.yaml          # المصادر (يتم التعديل من Dashboard)
└── docs/
    └── MONITORING_GUIDE.md   # دليل المراقبة الكامل
```

---

## ✅ ما تم إنجازه

- ✅ **RSS Collector** - جمع المقالات من 5 مصادر
- ✅ **Web Scraper** - جمع الأسعار من 3 مواقع
- ✅ **Celery Scheduler** - جدولة تلقائية
- ✅ **Dashboard** - 10 صفحات عربية RTL
- ✅ **Source Management** - إضافة/تعديل/حذف المصادر
- ✅ **Real-time Monitoring** - مراقبة مباشرة للجمع
- ✅ **API Endpoints** - تحكم برمجي كامل
- ✅ **Database Storage** - PostgreSQL + InfluxDB

---

## 🔜 الخطوات التالية (حسب TARGET.MD)

### المرحلة 1 (0-3 أشهر):
1. ✅ البنية التحتية - Docker + قواعد البيانات
2. ✅ جامعي البيانات - RSS + Web
3. ⏳ معالجات النصوص - TextCleaner + NumericExtractor
4. ⏳ نماذج البداية - Naive Bayes (Sentiment + Events)
5. ⏳ نماذج التنبؤ - HLT + XGBoost

### التالي:
- **Text Processors** لتنظيف النصوص العربية
- **Telegram Collector** (بعد إعداد API)
- **Sentiment Analyzer** (جمع 1000 نص للتدريب)

---

## 📞 المساعدة

- **دليل المراقبة**: `ShamIn/docs/MONITORING_GUIDE.md`
- **الخطة الكاملة**: `TARGET.MD`
- **دليل التشغيل**: `ShamIn/docs/06_دليل_التشغيل.md`

---

## 🎬 جربه الآن!

```bash
# الطريقة الأسهل (Windows)
start.bat

# أو مباشرة
cd ShamIn
python run_dashboard.py
```

**افتح المتصفح → اذهب لـ "🔄 تشغيل ومراقبة" → اضغط على أي محرك!**

🎉 **استمتع بمشاهدة البيانات وهي تُجمع أمامك مباشرة!**
