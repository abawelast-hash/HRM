# 🚀 دليل النشر (Deployment Guide)

<div dir="rtl">

دليل شامل لنشر نظام ShamIn على خادم VPS (Hostinger أو أي خادم آخر).

</div>

---

## 📋 جدول المحتويات

1. [المتطلبات](#-المتطلبات)
2. [إعداد الخادم](#-إعداد-الخادم)
3. [نشر التطبيق](#-نشر-التطبيق)
4. [إدارة الخدمات](#-إدارة-الخدمات)
5. [المراقبة والصيانة](#-المراقبة-والصيانة)
6. [حل المشاكل](#-حل-المشاكل)

---

## 🔧 المتطلبات

### متطلبات الخادم (Server Requirements)

| المكون | الحد الأدنى | الموصى به |
|--------|-------------|------------|
| **CPU** | 2 cores | 4 cores |
| **RAM** | 4 GB | 8 GB |
| **Disk** | 20 GB SSD | 50 GB SSD |
| **OS** | Ubuntu 20.04+ | Ubuntu 22.04 LTS |
| **Network** | 1 Gbps | 1 Gbps |

### البرمجيات المطلوبة
- Docker 24.0+
- Docker Compose 2.20+
- Git
- SSH client
- (اختياري) Nginx للـ reverse proxy

### بيانات الاعتماد المطلوبة
- ✅ SSH access للخادم (username + password أو private key)
- ✅ GitHub access (لسحب الكود)
- ⏳ Telegram API credentials (api_id, api_hash)
- ⏳ Email SMTP credentials (للتنبيهات)

---

## 🖥️ إعداد الخادم

### الخطوة 1: الاتصال بالخادم

```bash
# الاتصال عبر SSH
ssh username@187.77.173.160

# أو باستخدام مفتاح خاص
ssh -i path/to/private-key username@187.77.173.160
```

### الخطوة 2: تحديث النظام

```bash
# تحديث قوائم الحزم
sudo apt update && sudo apt upgrade -y

# تثبيت الأدوات الأساسية
sudo apt install -y curl wget git vim htop
```

### الخطوة 3: تثبيت Docker

```bash
# إزالة الإصدارات القديمة (إذا وجدت)
sudo apt remove docker docker-engine docker.io containerd runc

# إضافة مفتاح GPG الرسمي لـ Docker
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# إضافة مستودع Docker
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# تثبيت Docker
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# التحقق من التثبيت
docker --version
docker compose version

# إضافة المستخدم لمجموعة docker (لتشغيل بدون sudo)
sudo usermod -aG docker $USER

# إعادة تسجيل الدخول لتطبيق التغييرات
exit
# ثم الاتصال مرة أخرى
ssh username@187.77.173.160
```

### الخطوة 4: إعداد Firewall (UFW)

```bash
# تفعيل UFW
sudo ufw enable

# السماح بـ SSH
sudo ufw allow 22/tcp

# السماح بـ HTTP/HTTPS (إذا كنت تستخدم Nginx)
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# السماح بـ Dashboard (Streamlit) - اختياري إذا كنت تريد الوصول المباشر
sudo ufw allow 8501/tcp

# السماح بـ API (FastAPI)
sudo ufw allow 8000/tcp

# التحقق من القواعد
sudo ufw status
```

### الخطوة 5: إنشاء مجلد التطبيق

```bash
# إنشاء مجلد للتطبيقات
sudo mkdir -p /opt/shamin
sudo chown $USER:$USER /opt/shamin
cd /opt/shamin
```

---

## 📦 نشر التطبيق

### الخطوة 1: استنساخ المستودع

```bash
cd /opt/shamin

# استنساخ من GitHub
git clone https://github.com/abawelast-hash/HRM.git
cd HRM/ShamIn

# التحقق من الفرع
git branch
# يجب أن يكون: * main
```

### الخطوة 2: إعداد ملف البيئة (.env)

```bash
# نسخ المثال
cp .env.example .env

# تحرير الملف
nano .env
```

**محتوى `.env`:**

```bash
# ===== Database Credentials =====
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=shamin
POSTGRES_USER=shamin_user
POSTGRES_PASSWORD=<your-strong-password>

INFLUXDB_URL=http://influxdb:8086
INFLUXDB_TOKEN=<your-influx-token>
INFLUXDB_ORG=shamin_org
INFLUXDB_BUCKET=exchange_rates

REDIS_URL=redis://redis:6379/0

MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=<your-minio-access-key>
MINIO_SECRET_KEY=<your-minio-secret-key>

# ===== Telegram API (اختياري) =====
TELEGRAM_API_ID=<your-api-id>
TELEGRAM_API_HASH=<your-api-hash>
TELEGRAM_PHONE=<your-phone-number>

# ===== Email/SMS (اختياري) =====
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=<your-email>
SMTP_PASSWORD=<your-app-password>

# ===== Application Settings =====
LOG_LEVEL=INFO
ENVIRONMENT=production
```

**ملاحظات:**
- استبدل `<your-strong-password>` بكلمة مرور قوية
- احصل على `INFLUXDB_TOKEN` من InfluxDB UI بعد التشغيل الأول
- Telegram API credentials من https://my.telegram.org

### الخطوة 3: تشغيل Docker Compose

```bash
# التأكد من أنك في مجلد ShamIn
cd /opt/shamin/HRM/ShamIn

# تشغيل جميع الخدمات
docker compose up -d

# التحقق من الحاويات
docker compose ps

# يجب أن ترى:
# - shamin-postgres-1
# - shamin-influxdb-1
# - shamin-redis-1
# - shamin-minio-1
```

### الخطوة 4: تهيئة قواعد البيانات

```bash
# الدخول لحاوية Python (نستخدم dashboard مؤقتاً)
docker compose run --rm dashboard bash

# داخل الحاوية:
python scripts/setup_db.py
python scripts/setup_influxdb.py
python scripts/setup_minio.py

# الخروج
exit
```

**أو بشكل مباشر:**

```bash
docker compose exec postgres psql -U shamin_user -d shamin -c "\dt"
# يجب أن ترى: raw_texts, data_sources
```

### الخطوة 5: إنشاء Systemd Services (خدمات دائمة)

#### 5.1 Dashboard Service

```bash
sudo nano /etc/systemd/system/shamin-dashboard.service
```

**المحتوى:**

```ini
[Unit]
Description=ShamIn Dashboard (Streamlit)
After=docker.service
Requires=docker.service

[Service]
Type=simple
User=your-username
WorkingDirectory=/opt/shamin/HRM/ShamIn
ExecStart=/usr/bin/docker compose up dashboard
ExecStop=/usr/bin/docker compose stop dashboard
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

#### 5.2 API Service

```bash
sudo nano /etc/systemd/system/shamin-api.service
```

**المحتوى:**

```ini
[Unit]
Description=ShamIn API (FastAPI)
After=docker.service
Requires=docker.service

[Service]
Type=simple
User=your-username
WorkingDirectory=/opt/shamin/HRM/ShamIn
ExecStart=/usr/bin/docker compose up api
ExecStop=/usr/bin/docker compose stop api
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

#### 5.3 Celery Worker Service

```bash
sudo nano /etc/systemd/system/shamin-celery.service
```

**المحتوى:**

```ini
[Unit]
Description=ShamIn Celery Worker
After=docker.service redis.service
Requires=docker.service

[Service]
Type=simple
User=your-username
WorkingDirectory=/opt/shamin/HRM/ShamIn
ExecStart=/usr/bin/docker compose up celery-worker
ExecStop=/usr/bin/docker compose stop celery-worker
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

#### 5.4 Celery Beat Service

```bash
sudo nano /etc/systemd/system/shamin-beat.service
```

**المحتوى:**

```ini
[Unit]
Description=ShamIn Celery Beat (Scheduler)
After=docker.service redis.service
Requires=docker.service

[Service]
Type=simple
User=your-username
WorkingDirectory=/opt/shamin/HRM/ShamIn
ExecStart=/usr/bin/docker compose up celery-beat
ExecStop=/usr/bin/docker compose stop celery-beat
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

#### 5.5 تفعيل الخدمات

```bash
# إعادة تحميل systemd
sudo systemctl daemon-reload

# تفعيل الخدمات للتشغيل التلقائي
sudo systemctl enable shamin-dashboard
sudo systemctl enable shamin-api
sudo systemctl enable shamin-celery
sudo systemctl enable shamin-beat

# تشغيل الخدمات
sudo systemctl start shamin-dashboard
sudo systemctl start shamin-api
sudo systemctl start shamin-celery
sudo systemctl start shamin-beat

# التحقق من الحالة
sudo systemctl status shamin-dashboard
sudo systemctl status shamin-api
sudo systemctl status shamin-celery
sudo systemctl status shamin-beat
```

---

## 🔄 إدارة الخدمات

### التحقق من الحالة

```bash
# حالة جميع الخدمات
sudo systemctl status shamin-*

# حالة حاويات Docker
docker compose ps

# سجلات الخدمات
sudo journalctl -u shamin-dashboard -f
sudo journalctl -u shamin-api -f

# سجلات Docker
docker compose logs -f dashboard
docker compose logs -f api
docker compose logs -f celery-worker
```

### إعادة تشغيل الخدمات

```bash
# إعادة تشغيل Dashboard
sudo systemctl restart shamin-dashboard

# إعادة تشغيل API
sudo systemctl restart shamin-api

# إعادة تشغيل Celery
sudo systemctl restart shamin-celery
sudo systemctl restart shamin-beat

# إعادة تشغيل جميع الخدمات
sudo systemctl restart shamin-*
```

### إيقاف الخدمات

```bash
# إيقاف مؤقت
sudo systemctl stop shamin-dashboard

# إيقاف دائم (تعطيل التشغيل التلقائي)
sudo systemctl disable shamin-dashboard
```

### سحب التحديثات من Git

```bash
# الانتقال للمجلد
cd /opt/shamin/HRM/ShamIn

# إيقاف الخدمات
sudo systemctl stop shamin-*

# سحب التحديثات
git pull origin main

# إعادة بناء الحاويات (إذا تغيرت المتطلبات)
docker compose build

# إعادة تشغيل الخدمات
sudo systemctl start shamin-*

# التحقق
sudo systemctl status shamin-*
```

---

## 📊 المراقبة والصيانة

### مراقبة الموارد

```bash
# استخدام الذاكرة والمعالج
htop

# مساحة القرص
df -h

# استخدام Docker
docker stats

# حجم الصور والحاويات
docker system df
```

### نسخ احتياطي (Backup)

#### نسخ احتياطي لقاعدة البيانات

```bash
# PostgreSQL backup
docker compose exec postgres pg_dump -U shamin_user shamin > backup_$(date +%Y%m%d).sql

# InfluxDB backup
docker compose exec influxdb influx backup /backup/$(date +%Y%m%d)

# نقل النسخ الاحتياطية لمكان آمن
scp backup_*.sql user@backup-server:/backups/
```

#### نسخ احتياطي تلقائية (Cron Job)

```bash
# تحرير crontab
crontab -e

# إضافة السطر التالي (نسخ احتياطي يومي الساعة 2 صباحاً)
0 2 * * * cd /opt/shamin/HRM/ShamIn && docker compose exec -T postgres pg_dump -U shamin_user shamin > /backups/postgres_$(date +\%Y\%m\%d).sql
```

### تنظيف الموارد

```bash
# حذف الصور غير المستخدمة
docker image prune -a

# حذف الحاويات المتوقفة
docker container prune

# حذف الشبكات غير المستخدمة
docker network prune

# حذف الـ volumes غير المستخدمة (احذر!)
docker volume prune

# تنظيف شامل
docker system prune -a --volumes
```

### Logs Rotation

```bash
# إنشاء ملف logrotate
sudo nano /etc/logrotate.d/shamin
```

**المحتوى:**

```
/opt/shamin/HRM/ShamIn/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 0644 your-username your-username
    sharedscripts
    postrotate
        docker compose restart dashboard api celery-worker celery-beat
    endscript
}
```

---

## 🐛 حل المشاكل

### المشكلة 1: الخدمة لا تعمل

```bash
# التحقق من السجلات
sudo journalctl -u shamin-dashboard -n 50

# التحقق من Docker logs
docker compose logs dashboard --tail=100

# التحقق من الحاويات
docker compose ps

# إعادة تشغيل كاملة
docker compose down
docker compose up -d
```

### المشكلة 2: قاعدة البيانات لا تعمل

```bash
# التحقق من PostgreSQL
docker compose exec postgres psql -U shamin_user -d shamin -c "SELECT 1;"

# التحقق من InfluxDB
docker compose exec influxdb influx ping

# إعادة إنشاء الجداول
docker compose exec postgres psql -U shamin_user -d shamin -f /scripts/schema.sql
```

### المشكلة 3: Celery لا يجمع البيانات

```bash
# التحقق من Celery worker
docker compose logs celery-worker --tail=50

# التحقق من Celery beat
docker compose logs celery-beat --tail=50

# التحقق من Redis
docker compose exec redis redis-cli PING

# قائمة انتظار المهام
docker compose exec redis redis-cli LLEN celery

# تفريغ قائمة الانتظار
docker compose exec redis redis-cli FLUSHALL
```

### المشكلة 4: الذاكرة ممتلئة

```bash
# التحقق من الاستخدام
free -h
docker stats

# إيقاف الخدمات غير الضرورية
sudo systemctl stop shamin-dashboard  # مؤقتاً

# تنظيف Docker
docker system prune -a

# زيادة swap (إذا لزم الأمر)
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

### المشكلة 5: Port مشغول

```bash
# التحقق من المنافذ المستخدمة
sudo lsof -i :8501  # Dashboard
sudo lsof -i :8000  # API
sudo lsof -i :5432  # PostgreSQL

# إيقاف العملية
sudo kill -9 <PID>

# تغيير المنفذ في docker-compose.yml
nano docker-compose.yml
# غيّر "8501:8501" إلى "8502:8501" مثلاً
```

---

## 🔒 الأمان (Security)

### 1. تأمين SSH

```bash
# تعطيل تسجيل الدخول بـ root
sudo nano /etc/ssh/sshd_config
# غيّر: PermitRootLogin no

# تفعيل SSH key فقط (اختياري)
# PasswordAuthentication no

# إعادة تشغيل SSH
sudo systemctl restart sshd
```

### 2. تأمين PostgreSQL

```bash
# تغيير كلمة المرور
docker compose exec postgres psql -U postgres -c "ALTER USER shamin_user WITH PASSWORD 'new-strong-password';"

# تحديث .env
nano .env
# غيّر POSTGRES_PASSWORD
```

### 3. Nginx Reverse Proxy (اختياري)

```bash
# تثبيت Nginx
sudo apt install nginx

# إنشاء ملف configuration
sudo nano /etc/nginx/sites-available/shamin
```

**المحتوى:**

```nginx
server {
    listen 80;
    server_name 187.77.173.160;  # أو اسم النطاق

    # Dashboard
    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # API
    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

```bash
# تفعيل الموقع
sudo ln -s /etc/nginx/sites-available/shamin /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

## 🎯 Checklist النشر

- [ ] الخادم محدّث وجاهز
- [ ] Docker و Docker Compose مثبتين
- [ ] Firewall مُعد بشكل صحيح
- [ ] المستودع مستنسخ
- [ ] ملف `.env` مُعد بالكامل
- [ ] قواعد البيانات مُهيأة
- [ ] Systemd services مُنشأة ومُفعّلة
- [ ] الخدمات تعمل وتستجيب
- [ ] Backup معدّ (cron job)
- [ ] Logs rotation مُعد
- [ ] Monitoring قيد التشغيل
- [ ] تم اختبار real-time collection
- [ ] Dashboard يعمل: http://187.77.173.160:8501
- [ ] API يعمل: http://187.77.173.160:8000/docs

---

## 📞 الدعم

إذا واجهت مشكلة:
1. راجع السجلات: `sudo journalctl -u shamin-* -f`
2. راجع Docker logs: `docker compose logs -f`
3. راجع [troubleshooting section](#-حل-المشاكل)
4. افتح issue على GitHub

---

<div align="center">

**نُشر بنجاح! 🎉**

</div>
