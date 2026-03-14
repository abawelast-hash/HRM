# 🔄 دليل التحديث (Update Guide)

<div dir="rtl">

دليل شامل لتحديث نظام ShamIn على الخادم المُنشَر.

</div>

---

## 🎯 متى تحتاج للتحديث؟

- عند إضافة ميزات جديدة للكود
- عند إصلاح أخطاء (bug fixes)
- عند تحديث المتطلبات (requirements.txt)
- عند تحديث التكوين (config files)
- بشكل دوري (مرة شهرياً على الأقل)

---

## 🚀 التحديث السريع (Quick Update)

### على الخادم (VPS)

```bash
# 1. الاتصال بالخادم
ssh username@187.77.173.160

# 2. الانتقال لمجلد التطبيق
cd /opt/shamin/HRM/ShamIn

# 3. سحب أحدث تغييرات
git pull origin main

# 4. إعادة بناء وتشغيل الحاويات
docker compose up -d --build

# 5. التحقق من الحالة
docker compose ps
docker compose logs -f
```

### محلياً (Local - Windows)

```cmd
REM 1. الانتقال للمجلد
cd D:\2_GitHub\abawelast\HRM\HRM\ShamIn

REM 2. سحب التحديثات
git pull origin main

REM 3. إعادة تشغيل
docker compose down
docker compose up -d --build

REM 4. التحقق
docker compose ps
```

---

## 📋 التحديث الكامل (Full Update)

### الخطوة 1: النسخ الاحتياطي

```bash
# نسخ احتياطي لقاعدة البيانات
cd /opt/shamin/HRM/ShamIn

# PostgreSQL backup
docker compose exec postgres pg_dump -U shamin_user shamin_db > backup_before_update_$(date +%Y%m%d).sql

# InfluxDB backup (اختياري)
docker compose exec influxdb influx backup /backup/update_$(date +%Y%m%d)

# نسخ ملف .env
cp .env .env.backup_$(date +%Y%m%d)

# نسخ البيانات المحلية
tar -czf data_backup_$(date +%Y%m%d).tar.gz data/
```

### الخطوة 2: إيقاف الخدمات

```bash
# إيقاف تطبيقات ShamIn
docker compose stop api dashboard celery-worker celery-beat

# أو إيقاف كامل (يوقف قواعد البيانات أيضاً)
docker compose down
```

### الخطوة 3: سحب التحديثات

```bash
# التأكد من أنك على الفرع الصحيح
git branch
# يجب أن يظهر: * main

# جلب آخر تغييرات من GitHub
git fetch origin

# دمج التحديثات
git pull origin main

# التحقق من التغييرات
git log -5 --oneline
```

### الخطوة 4: التحقق من requirements.txt

```bash
# مقارنة requirements.txt القديم والجديد
git diff HEAD~1 requirements.txt

# إذا تغيرت المتطلبات، إعادة بناء الصور
docker compose build --no-cache
```

### الخطوة 5: التحقق من docker-compose.yml

```bash
# مقارنة docker-compose.yml
git diff HEAD~1 docker-compose.yml

# إذا تغير، تحديث الخدمات
docker compose config  # للتحقق من صحة الملف
```

### الخطوة 6: التحقق من .env

```bash
# مقارنة .env.example
git diff HEAD~1 .env.example

# إضافة أي متغيرات جديدة لـ .env يدوياً
nano .env
```

### الخطوة 7: تحديث قاعدة البيانات (إذا لزم)

```bash
# إذا كانت هناك تغييرات في schema.sql
git diff HEAD~1 scripts/schema.sql

# تطبيق التحديثات
docker compose exec postgres psql -U shamin_user -d shamin_db -f /scripts/schema.sql
```

### الخطوة 8: إعادة تشغيل الخدمات

```bash
# إعادة تشغيل كامل
docker compose up -d

# أو تشغيل تدريجي
docker compose up -d postgres influxdb redis minio
sleep 10
docker compose up -d api dashboard celery-worker celery-beat

# التحقق من الحالة
docker compose ps
```

### الخطوة 9: التحقق من السجلات

```bash
# مراقبة السجلات للتأكد من عدم وجود أخطاء
docker compose logs -f --tail=100

# أو لخدمة محددة
docker compose logs -f api
docker compose logs -f dashboard
docker compose logs -f celery-worker
```

### الخطوة 10: اختبار الوظائف

```bash
# اختبار API
curl http://localhost:8000/health

# اختبار Dashboard
curl http://localhost:8501/_stcore/health

# اختبار قاعدة البيانات
docker compose exec postgres psql -U shamin_user -d shamin_db -c "SELECT COUNT(*) FROM raw_texts;"

# اختبار InfluxDB
curl http://localhost:8086/health
```

---

## ⚠️ التراجع عن التحديث (Rollback)

إذا فشل التحديث:

### الطريقة 1: Git Revert

```bash
# العودة للـ commit السابق
git log --oneline -5
git reset --hard <previous-commit-hash>

# إعادة تشغيل
docker compose down
docker compose up -d
```

### الطريقة 2: استعادة النسخة الاحتياطية

```bash
# استعادة قاعدة البيانات
docker compose exec -T postgres psql -U shamin_user -d shamin_db < backup_before_update_YYYYMMDD.sql

# استعادة .env
cp .env.backup_YYYYMMDD .env

# استعادة البيانات
tar -xzf data_backup_YYYYMMDD.tar.gz

# إعادة تشغيل
docker compose restart
```

---

## 🔄 التحديث التلقائي (Auto-Update)

### إنشاء سكريبت تحديث تلقائي

```bash
nano /opt/shamin/auto_update.sh
```

**المحتوى:**

```bash
#!/bin/bash

APP_DIR="/opt/shamin/HRM/ShamIn"
BACKUP_DIR="/opt/shamin/backups"
LOG_FILE="/opt/shamin/update.log"

echo "$(date): Starting auto-update..." >> $LOG_FILE

cd $APP_DIR

# Backup
docker compose exec -T postgres pg_dump -U shamin_user shamin_db > $BACKUP_DIR/auto_backup_$(date +%Y%m%d_%H%M%S).sql

# Pull updates
git fetch origin
UPDATES=$(git rev-list HEAD...origin/main --count)

if [ $UPDATES -gt 0 ]; then
    echo "$(date): Found $UPDATES updates, applying..." >> $LOG_FILE
    
    git pull origin main
    docker compose up -d --build
    
    echo "$(date): Update completed successfully" >> $LOG_FILE
else
    echo "$(date): No updates available" >> $LOG_FILE
fi
```

**تفعيل:**

```bash
chmod +x /opt/shamin/auto_update.sh

# إضافة لـ cron (تحديث يومي الساعة 3 صباحاً)
(crontab -l; echo "0 3 * * * /opt/shamin/auto_update.sh") | crontab -
```

---

## 📊 سجل التحديثات

احتفظ بسجل لكل تحديث:

```bash
# إنشاء ملف سجل
echo "$(date): Updated to commit $(git rev-parse --short HEAD)" >> /opt/shamin/update_log.txt
echo "Changes: $(git log -1 --oneline)" >> /opt/shamin/update_log.txt
echo "---" >> /opt/shamin/update_log.txt
```

---

## 🛠️ تحديثات خاصة

### تحديث Python requirements فقط

```bash
docker compose exec api pip install -r requirements.txt
docker compose restart api dashboard celery-worker celery-beat
```

### تحديث التكوينات فقط

```bash
# بعد تحديث config/*.yaml
docker compose restart api dashboard
```

### تحديث Celery tasks فقط

```bash
docker compose restart celery-worker celery-beat
```

---

## 📞 في حال المشاكل

### المشكلة: الخدمة لا تبدأ بعد التحديث

```bash
# تحقق من السجلات
docker compose logs api --tail=100

# تحقق من التكوين
docker compose config

# إعادة بناء من الصفر
docker compose down
docker compose build --no-cache
docker compose up -d
```

### المشكلة: قاعدة البيانات غير متوافقة

```bash
# استعادة من النسخة الاحتياطية
docker compose exec -T postgres psql -U shamin_user -d shamin_db < backup.sql

# أو تطبيق migrations يدوياً
docker compose exec postgres psql -U shamin_user -d shamin_db
```

### المشكلة: الذاكرة ممتلئة

```bash
# تنظيف Docker
docker system prune -a --volumes

# إعادة تشغيل
docker compose up -d
```

---

## ✅ Checklist التحديث

- [ ] نسخ احتياطي لقاعدة البيانات
- [ ] نسخ احتياطي لـ .env
- [ ] نسخ احتياطي للبيانات المحلية
- [ ] سحب التحديثات من Git
- [ ] التحقق من requirements.txt
- [ ] التحقق من docker-compose.yml
- [ ] التحقق من .env الجديد
- [ ] تحديث schema إذا لزم
- [ ] إعادة بناء الصور إذا لزم
- [ ] إعادة تشغيل الخدمات
- [ ] التحقق من السجلات
- [ ] اختبار API
- [ ] اختبار Dashboard
- [ ] اختبار جمع البيانات
- [ ] تحديث سجل التحديثات
- [ ] حذف النسخ الاحتياطية القديمة

---

## 🎯 أفضل الممارسات

1. **احتفظ بنسخ احتياطية دائماً** قبل أي تحديث
2. **اختبر محلياً أولاً** قبل التحديث على الخادم
3. **اقرأ CHANGELOG.md** لمعرفة ما تغير
4. **حدّث تدريجياً** (قواعد البيانات أولاً، ثم التطبيق)
5. **راقب السجلات** بعد كل تحديث
6. **احتفظ بخطة rollback** جاهزة
7. **حدّث في أوقات الصيانة** (low traffic)

---

<div align="center">

**تحديث سلس! 🚀**

</div>
