# 🚀 خطوات النشر اليدوي على VPS

## الطريقة 1: باستخدام PowerShell Script (الأسهل)

```powershell
# في PowerShell (تشغيل كمسؤول)
cd D:\2_GitHub\abawelast\HRM\HRM\ShamIn
.\deploy_to_vps.ps1

# سيطلب منك:
# 1. اسم المستخدم للخادم
# 2. كلمة المرور (عند الاتصال)

# ثم سيقوم بكل شيء تلقائياً!
```

---

## الطريقة 2: SSH يدوي خطوة بخطوة

### الخطوة 1: الاتصال بالخادم

```powershell
# في PowerShell
ssh username@187.77.173.160

# أدخل كلمة المرور عندما تُطلب
```

### الخطوة 2: تحميل السكريبت

```bash
# على الخادم
curl -fsSL https://raw.githubusercontent.com/abawelast-hash/HRM/main/ShamIn/deploy.sh -o deploy.sh
chmod +x deploy.sh
```

### الخطوة 3: تنفيذ السكريبت

```bash
# نشر كامل (موصى به للمرة الأولى)
bash deploy.sh

# أو مع خيارات:
# bash deploy.sh --skip-docker    # إذا كان Docker مثبت
# bash deploy.sh --skip-setup     # إذا كانت قواعد البيانات موجودة
# bash deploy.sh --clean          # تثبيت نظيف (حذف القديم)
```

### الخطوة 4: انتظر (5-10 دقائق)

السكريبت سيقوم بـ:
```
[INFO] Step 1: Updating system packages...
[INFO] Step 2: Installing Docker...
[INFO] Step 3: Configuring firewall...
[INFO] Step 4: Setting up application directory...
[INFO] Step 5: Cloning/updating repository...
[INFO] Step 6: Setting up environment file...
[INFO] Step 7: Starting Docker services...
[INFO] Step 8: Initializing databases...
[INFO] Step 9: Starting application services...
[INFO] Step 10: Creating systemd services...
[INFO] Step 11: Setting up backup cron job...
[INFO] Step 12: Running health checks...
[SUCCESS] 🎉 Deployment completed successfully!
```

### الخطوة 5: التحقق

```bash
# على الخادم، تحقق من الخدمات
docker compose ps

# يجب أن ترى:
# shamin_postgres    (healthy)
# shamin_influxdb    (healthy)
# shamin_redis       (healthy)
# shamin_minio       (healthy)
# shamin_api         (running)
# shamin_dashboard   (running)
# shamin_celery_worker (running)
# shamin_celery_beat (running)
```

### الخطوة 6: افتح Dashboard

افتح المتصفح:
```
http://187.77.173.160:8501
```

---

## الطريقة 3: استخدام PuTTY (Windows التقليدي)

### 1. تحميل PuTTY
- حمّل من: https://www.putty.org/
- افتح PuTTY

### 2. الاتصال
```
Host Name: 187.77.173.160
Port: 22
Connection Type: SSH
[Open]
```

### 3. تسجيل الدخول
```
login as: your-username
password: ********
```

### 4. تنفيذ الأوامر
```bash
curl -fsSL https://raw.githubusercontent.com/abawelast-hash/HRM/main/ShamIn/deploy.sh -o deploy.sh
chmod +x deploy.sh
bash deploy.sh
```

---

## 🔧 بعد النشر

### عرض السجلات
```bash
cd /opt/shamin/HRM/ShamIn
docker compose logs -f
```

### إعادة تشغيل خدمة
```bash
sudo systemctl restart shamin-dashboard
sudo systemctl restart shamin-api
```

### إيقاف جميع الخدمات
```bash
sudo systemctl stop shamin-*
```

### التحقق من الحالة
```bash
sudo systemctl status shamin-*
docker compose ps
```

---

## 🔐 معلومات الأمان

بعد النشر، ستجد كلمات المرور المولدة تلقائياً في:
```bash
cat /opt/shamin/HRM/ShamIn/.env
```

احفظها في مكان آمن!

---

## 📞 في حال المشاكل

### خطأ: Cannot connect to Docker daemon
```bash
sudo systemctl start docker
sudo usermod -aG docker $USER
# ثم logout و login مرة أخرى
```

### خطأ: Port already in use
```bash
sudo lsof -i :8501
sudo kill -9 <PID>
docker compose restart
```

### خطأ: Database initialization failed
```bash
docker compose down
docker compose up -d postgres
sleep 10
docker compose exec postgres psql -U shamin_user -d shamin_db -f /scripts/schema.sql
```

---

## ✅ Checklist

- [ ] اتصال SSH يعمل
- [ ] سكريبت deploy.sh محمّل
- [ ] السكريبت تم تنفيذه بنجاح
- [ ] جميع الحاويات تعمل (8/8)
- [ ] Dashboard يفتح على http://187.77.173.160:8501
- [ ] API يعمل على http://187.77.173.160:8000
- [ ] كلمات المرور محفوظة
- [ ] Systemd services مفعّلة
- [ ] Backup cron job مُعد

---

**جاهز للانطلاق! 🚀**
