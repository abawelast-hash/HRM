"""ShamIn — لوحة تحكم شاملة باللغة العربية."""
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import os
import json
import redis
import psycopg2

# ──────────────────────────────────────────────────────────
# الإعدادات الأساسية
# ──────────────────────────────────────────────────────────

st.set_page_config(
    page_title="شامِن — نظام التنبؤ بسعر الصرف",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ──────────────────────────────────────────────────────────
# تنسيق CSS للعربية (RTL) + تلميحات i
# ──────────────────────────────────────────────────────────

st.markdown("""
<style>
    /* RTL Support */
    .stApp { direction: rtl; }
    .stMarkdown, .stText { direction: rtl; text-align: right; }
    .stSelectbox > div, .stRadio > div { direction: rtl; }

    /* Info Tooltip Styling */
    .info-tip {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 20px; height: 20px;
        border-radius: 50%;
        background: #3b82f6;
        color: white;
        font-size: 12px;
        font-weight: bold;
        cursor: help;
        margin-right: 6px;
        position: relative;
    }
    .info-tip:hover .tip-text {
        visibility: visible;
        opacity: 1;
    }
    .tip-text {
        visibility: hidden;
        opacity: 0;
        width: 280px;
        background: #1e293b;
        color: #e2e8f0;
        text-align: right;
        border-radius: 8px;
        padding: 10px 14px;
        position: absolute;
        z-index: 999;
        top: 28px;
        right: -10px;
        transition: opacity 0.3s;
        font-size: 13px;
        line-height: 1.6;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
        direction: rtl;
    }

    /* Status Badges */
    .status-badge {
        display: inline-block;
        padding: 3px 12px;
        border-radius: 12px;
        font-size: 13px;
        font-weight: 600;
    }
    .status-healthy { background: #065f46; color: #6ee7b7; }
    .status-warning { background: #78350f; color: #fbbf24; }
    .status-error { background: #7f1d1d; color: #fca5a5; }
    .status-pending { background: #1e3a5f; color: #93c5fd; }

    /* Cards */
    .metric-card {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 20px;
        margin: 8px 0;
        direction: rtl;
        text-align: right;
    }
    .metric-card h3 { color: #94a3b8; font-size: 14px; margin: 0 0 8px 0; }
    .metric-card .value { color: #f1f5f9; font-size: 28px; font-weight: 700; }
    .metric-card .sub { color: #64748b; font-size: 12px; margin-top: 4px; }

    /* Section Header */
    .section-header {
        display: flex;
        align-items: center;
        gap: 10px;
        margin: 20px 0 10px 0;
        direction: rtl;
    }
    .section-header h2 { margin: 0; color: #f1f5f9; }

    /* Phase Badge */
    .phase-badge {
        display: inline-block;
        padding: 2px 10px;
        border-radius: 10px;
        font-size: 11px;
        font-weight: 600;
        margin-right: 8px;
    }
    .phase-active { background: #065f46; color: #6ee7b7; }
    .phase-next { background: #78350f; color: #fbbf24; }
    .phase-future { background: #1e293b; color: #64748b; border: 1px solid #334155; }

    /* Hide Streamlit Defaults */
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    .stDeployButton { display: none; }
</style>
""", unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────
# دوال مساعدة
# ──────────────────────────────────────────────────────────

def info_tip(text: str) -> str:
    """إنشاء أيقونة معلومات مع تلميح."""
    return f'<span class="info-tip">i<span class="tip-text">{text}</span></span>'


def status_badge(status: str) -> str:
    """إنشاء شارة حالة ملونة."""
    labels = {
        "healthy": ("يعمل", "status-healthy"),
        "warning": ("تحذير", "status-warning"),
        "error": ("متوقف", "status-error"),
        "pending": ("قيد الإعداد", "status-pending"),
    }
    label, css = labels.get(status, ("غير معروف", "status-pending"))
    return f'<span class="status-badge {css}">{label}</span>'


def metric_card(title: str, value: str, subtitle: str = "", tip: str = "") -> str:
    """إنشاء بطاقة مقياس."""
    tip_html = info_tip(tip) if tip else ""
    return f'''
    <div class="metric-card">
        <h3>{tip_html} {title}</h3>
        <div class="value">{value}</div>
        <div class="sub">{subtitle}</div>
    </div>
    '''


def check_service(name: str) -> dict:
    """فحص حالة خدمة."""
    try:
        if name == "redis":
            r = redis.Redis.from_url(
                os.getenv("REDIS_URL", "redis://redis:6379/0"),
                socket_connect_timeout=3
            )
            r.ping()
            r.close()
            return {"status": "healthy", "detail": "متصل"}
        elif name == "postgres":
            conn = psycopg2.connect(
                os.getenv("POSTGRES_URL", "postgresql://shamin_user:password@postgres:5432/shamin_db"),
                connect_timeout=3
            )
            conn.close()
            return {"status": "healthy", "detail": "متصل"}
        elif name == "influxdb":
            from influxdb_client import InfluxDBClient
            client = InfluxDBClient(
                url=os.getenv("INFLUXDB_URL", "http://influxdb:8086"),
                token=os.getenv("INFLUXDB_TOKEN", ""),
                org=os.getenv("INFLUXDB_ORG", "shamin_org"),
            )
            health = client.health()
            client.close()
            if health.status == "pass":
                return {"status": "healthy", "detail": "متصل"}
            return {"status": "warning", "detail": str(health.status)}
        elif name == "minio":
            from minio import Minio
            client = Minio(
                os.getenv("MINIO_ENDPOINT", "minio:9000"),
                access_key=os.getenv("MINIO_ACCESS_KEY", ""),
                secret_key=os.getenv("MINIO_SECRET_KEY", ""),
                secure=False,
            )
            client.list_buckets()
            return {"status": "healthy", "detail": "متصل"}
    except Exception as e:
        return {"status": "error", "detail": str(e)[:80]}
    return {"status": "pending", "detail": "غير مهيأ"}


def get_celery_stats() -> dict:
    """جلب إحصائيات Celery من Redis."""
    try:
        r = redis.Redis.from_url(
            os.getenv("REDIS_URL", "redis://redis:6379/0"),
            socket_connect_timeout=3
        )
        info = r.info("keyspace")
        keys_count = 0
        for db_info in info.values():
            if isinstance(db_info, dict):
                keys_count += db_info.get("keys", 0)
        r.close()
        return {"connected": True, "keys": keys_count}
    except Exception:
        return {"connected": False, "keys": 0}


# ──────────────────────────────────────────────────────────
# الشريط الجانبي - التنقل
# ──────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("## 🏛️ شامِن")
    st.markdown("##### نظام التنبؤ الذكي بسعر الصرف")
    st.markdown("---")

    page = st.radio(
        "التنقل",
        [
            "🏠 نظرة عامة",
            "📡 مصادر البيانات",
            "➕ إدارة المصادر",
            "💱 أسعار الصرف",
            "🤖 نماذج التنبؤ",
            "📰 الأحداث والأخبار",
            "📊 أداء النظام",
            "🔔 التنبيهات",
            "⚙️ الإعدادات",
        ],
        label_visibility="collapsed",
    )

    st.markdown("---")
    st.markdown(f"""
    <div style="text-align:center; color:#64748b; font-size:12px;">
        الإصدار 1.0.0-beta<br>
        {datetime.now().strftime('%Y-%m-%d %H:%M')}
    </div>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════
# صفحة: نظرة عامة
# ══════════════════════════════════════════════════════════

if page == "🏠 نظرة عامة":
    st.markdown(f"""
    <h1 style="text-align:right; margin-bottom:5px;">
        🏛️ لوحة التحكم الرئيسية
        {info_tip("لوحة تحكم شاملة لنظام شامِن للتنبؤ بسعر صرف الليرة السورية مقابل الدولار. تعرض حالة جميع الخدمات والمكونات في الوقت الفعلي.")}
    </h1>
    """, unsafe_allow_html=True)

    # ── حالة الخدمات ──
    st.markdown(f"""
    <div class="section-header">
        <h2>⚡ حالة الخدمات</h2>
        {info_tip("الخدمات الأساسية التي يعتمد عليها النظام: قواعد البيانات وطوابير المهام وتخزين الملفات. إذا توقفت أي خدمة سيتأثر جزء من النظام.")}
    </div>
    """, unsafe_allow_html=True)

    services = {
        "PostgreSQL": {
            "check": "postgres",
            "icon": "🐘",
            "tip": "قاعدة البيانات العلائقية الرئيسية. تخزن الأحداث المصنفة والبيانات الوصفية وسجلات النماذج وإعدادات النظام."
        },
        "InfluxDB": {
            "check": "influxdb",
            "icon": "📈",
            "tip": "قاعدة بيانات السلاسل الزمنية. تخزن أسعار الصرف والمؤشرات الاقتصادية مع طوابع زمنية دقيقة لتحليل الاتجاهات."
        },
        "Redis": {
            "check": "redis",
            "icon": "⚡",
            "tip": "وسيط الرسائل والذاكرة المؤقتة. يدير طابور مهام Celery ويخزن النتائج المؤقتة والكاش لتسريع الاستجابة."
        },
        "MinIO": {
            "check": "minio",
            "icon": "📦",
            "tip": "تخزين الكائنات (Object Storage). يحفظ النماذج المدربة والبيانات الخام الكبيرة والنسخ الاحتياطية بتنسيق متوافق مع S3."
        },
    }

    cols = st.columns(4)
    for i, (name, info) in enumerate(services.items()):
        with cols[i]:
            result = check_service(info["check"])
            st.markdown(metric_card(
                title=f'{info["icon"]} {name}',
                value=status_badge(result["status"]),
                subtitle=result["detail"],
                tip=info["tip"],
            ), unsafe_allow_html=True)

    # ── إحصائيات سريعة ──
    st.markdown(f"""
    <div class="section-header">
        <h2>📊 إحصائيات سريعة</h2>
        {info_tip("ملخص سريع لحالة النظام: عدد المصادر النشطة والمهام المجدولة والنماذج المسجلة.")}
    </div>
    """, unsafe_allow_html=True)

    celery_stats = get_celery_stats()

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(metric_card(
            "مصادر البيانات النشطة",
            "11",
            "3 مواقع + 3 تلغرام + 5 RSS",
            "عدد المصادر المفعّلة حالياً في ملف sources.yaml والتي يتم جمع البيانات منها بشكل دوري."
        ), unsafe_allow_html=True)
    with col2:
        st.markdown(metric_card(
            "المهام المجدولة",
            "5",
            "تعمل عبر Celery Beat",
            "المهام الدورية: جمع RSS كل 15 دقيقة، أسعار تلغرام كل 5 دقائق، أخبار تلغرام كل 5 دقائق، أسعار المواقع كل 5 دقائق، مؤشرات اقتصادية كل ساعة."
        ), unsafe_allow_html=True)
    with col3:
        st.markdown(metric_card(
            "Celery Queue",
            "متصل ✓" if celery_stats["connected"] else "غير متصل ✗",
            f"{celery_stats['keys']} مفتاح في Redis" if celery_stats["connected"] else "",
            "طابور المهام Celery يتصل بـ Redis لإدارة تنفيذ مهام الجمع والمعالجة بشكل غير متزامن."
        ), unsafe_allow_html=True)
    with col4:
        st.markdown(metric_card(
            "حالة النماذج",
            "قيد الإعداد",
            "المرحلة 4-5",
            "نماذج التنبؤ (XGBoost, TFT, Ensemble) لم تُدرَّب بعد. ستُفعَّل في المرحلة 4 (Baseline) والمرحلة 5 (Deep Learning)."
        ), unsafe_allow_html=True)

    # ── خارطة الطريق ──
    st.markdown(f"""
    <div class="section-header">
        <h2>🗺️ خارطة تنفيذ المشروع</h2>
        {info_tip("المراحل التنفيذية للمشروع وفق TARGET.MD: كل مرحلة تبني على سابقتها. المرحلة الحالية هي المرحلة 1 (البنية التحتية).")}
    </div>
    """, unsafe_allow_html=True)

    phases = [
        ("المرحلة 1", "البنية التحتية وجمع البيانات", "active",
         "إعداد البنية التحتية (Docker, DB, Queue) + بناء جامعات البيانات (RSS, Web Scraper, Telegram) + خط المعالجة الأولي."),
        ("المرحلة 2", "المعالجة واستخراج الميزات", "next",
         "تنظيف النصوص العربية + استخراج الأسعار من النصوص + تحليل المشاعر + تصنيف الأحداث + Word Embeddings."),
        ("المرحلة 3", "تخزين الميزات والتكامل", "next",
         "بناء Feature Store + تجميع الميزات الزمنية + ربط جميع مصادر البيانات في خط معالجة موحد (Unified Pipeline)."),
        ("المرحلة 4", "نماذج Baseline", "future",
         "تدريب نماذج أولية: XGBoost, Random Forest, Holt-Winters. قياس الأداء (MAE, RMSE, MAPE) وإنشاء خط أساس للمقارنة."),
        ("المرحلة 5", "نماذج التعلم العميق", "future",
         "TFT (Temporal Fusion Transformer), Bi-LSTM, GRU, CNN. استخدام Optuna لضبط المعاملات + Ensemble Weighting."),
        ("المرحلة 6", "التقييم والتفسيرية", "future",
         "تقييم شامل + SHAP/Grad-CAM لتفسير التنبؤات + مقارنة النماذج + اختيار النموذج الأمثل."),
        ("المرحلة 7", "التغذية الراجعة", "future",
         "حلقة تغذية راجعة: مقارنة التوقعات بالواقع + إعادة تدريب تلقائية + كشف الانحراف (Drift Detection)."),
    ]

    for phase_name, desc, status, tip in phases:
        badge_class = f"phase-{status}"
        st.markdown(f"""
        <div style="display:flex; align-items:center; padding:10px 0; border-bottom:1px solid #1e293b; direction:rtl;">
            <span class="phase-badge {badge_class}">{phase_name}</span>
            <span style="color:#e2e8f0; flex:1;">{desc}</span>
            {info_tip(tip)}
        </div>
        """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════
# صفحة: مصادر البيانات
# ══════════════════════════════════════════════════════════

elif page == "📡 مصادر البيانات":
    st.markdown(f"""
    <h1 style="text-align:right;">
        📡 مصادر البيانات
        {info_tip("جميع المصادر التي يجمع منها النظام البيانات تلقائياً. تشمل مواقع أسعار الصرف وقنوات تلغرام وخلاصات RSS ومؤشرات اقتصادية خارجية.")}
    </h1>
    """, unsafe_allow_html=True)

    # ── مصادر الأسعار ──
    st.markdown(f"""
    <div class="section-header">
        <h2>💰 مصادر أسعار الصرف المباشرة</h2>
        {info_tip("مواقع إلكترونية تُعرض عليها أسعار صرف الليرة السورية بشكل مباشر. يتم سحب الأسعار منها بأداة BeautifulSoup كل 5 دقائق إلى ساعة حسب أهمية المصدر.")}
    </div>
    """, unsafe_allow_html=True)

    price_sources = [
        {"name": "sp-today.com", "freq": "كل 5 دقائق",
         "type": "سعر السوق", "status": "active",
         "tip": "موقع الليرة اليوم — أشهر مصدر لأسعار الصرف في السوق السوداء السوري. يعرض سعر الدولار في دمشق وحلب وإدلب."},
        {"name": "Investing.com", "freq": "كل ساعة",
         "type": "سعر رسمي + تاريخي", "status": "active",
         "tip": "موقع عالمي للبيانات المالية. يوفر السعر الرسمي لـ USD/SYP وبيانات تاريخية للتحليل والمقارنة مع سعر السوق."},
        {"name": "البنك المركزي السوري", "freq": "يومياً",
         "type": "سعر رسمي", "status": "active",
         "tip": "الموقع الرسمي للبنك المركزي السوري. يصدر النشرة الرسمية لسعر الصرف يومياً، وهو يختلف عادة عن سعر السوق الفعلي."},
    ]

    for src in price_sources:
        col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
        with col1:
            st.markdown(f"""
            <div style="direction:rtl;">
                <strong style="color:#e2e8f0;">{src['name']}</strong>
                {info_tip(src['tip'])}
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown(f"<span style='color:#94a3b8;'>{src['type']}</span>", unsafe_allow_html=True)
        with col3:
            st.markdown(f"<span style='color:#94a3b8;'>⏱️ {src['freq']}</span>", unsafe_allow_html=True)
        with col4:
            st.markdown(status_badge("healthy"), unsafe_allow_html=True)
        st.markdown("<hr style='border-color:#1e293b; margin:5px 0;'>", unsafe_allow_html=True)

    # ── قنوات تلغرام ──
    st.markdown(f"""
    <div class="section-header">
        <h2>📱 قنوات تلغرام</h2>
        {info_tip("قنوات تلغرام سورية تنشر أسعار الصرف والأخبار الاقتصادية. يتم سحب الرسائل أوتوماتيكياً عبر مكتبة Telethon مع تأخير عشوائي لتفادي الحظر.")}
    </div>
    """, unsafe_allow_html=True)

    telegram_sources = [
        {"name": "أسعار الصرف السورية", "channel": "@syrian_exchange_rates",
         "freq": "كل دقيقة", "type": "أسعار",
         "tip": "قناة تلغرام تنشر أسعار صرف الدولار مقابل الليرة السورية بشكل لحظي. تُستخرج الأسعار الرقمية من النصوص باستخدام Regex متخصص."},
        {"name": "سوق دمشق", "channel": "@damascus_market",
         "freq": "كل دقيقتين", "type": "أسعار",
         "tip": "قناة أسعار سوق دمشق — تغطي أسعار الدولار والذهب والحوالات في العاصمة."},
        {"name": "أخبار سوريا الاقتصادية", "channel": "@syria_economic_news",
         "freq": "كل 5 دقائق", "type": "أخبار",
         "tip": "قناة أخبار اقتصادية سورية. تُحلل نصوصها لتحديد المشاعر (إيجابي/سلبي/محايد) وتصنيف الأحداث المؤثرة على سعر الصرف."},
    ]

    tg_configured = bool(os.getenv("TELEGRAM_API_ID"))
    if not tg_configured:
        st.warning("⚠️ بيانات اعتماد Telegram غير مهيأة. أضف TELEGRAM_API_ID و TELEGRAM_API_HASH في ملف .env")

    for src in telegram_sources:
        col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
        with col1:
            st.markdown(f"""
            <div style="direction:rtl;">
                <strong style="color:#e2e8f0;">{src['name']}</strong>
                {info_tip(src['tip'])}
                <br><span style="color:#64748b; font-size:12px;">{src['channel']}</span>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown(f"<span style='color:#94a3b8;'>{src['type']}</span>", unsafe_allow_html=True)
        with col3:
            st.markdown(f"<span style='color:#94a3b8;'>⏱️ {src['freq']}</span>", unsafe_allow_html=True)
        with col4:
            st.markdown(status_badge("pending" if not tg_configured else "healthy"), unsafe_allow_html=True)
        st.markdown("<hr style='border-color:#1e293b; margin:5px 0;'>", unsafe_allow_html=True)

    # ── خلاصات RSS ──
    st.markdown(f"""
    <div class="section-header">
        <h2>📰 خلاصات RSS</h2>
        {info_tip("مصادر أخبار عبر بروتوكول RSS. يتم جمع العناوين والمحتوى كل 15-30 دقيقة ثم تحليلها لاستخراج الأحداث المؤثرة على سعر الصرف وتحديد مشاعر السوق.")}
    </div>
    """, unsafe_allow_html=True)

    rss_sources = [
        {"name": "عنب بلدي", "url": "enabbaladi.net/feed", "freq": "كل 15 دقيقة", "cat": "أخبار اقتصادية",
         "tip": "موقع إخباري سوري مستقل يغطي الأخبار الاقتصادية والاجتماعية. مصدر مهم لأخبار الاقتصاد المحلي وتحليلاته."},
        {"name": "رويترز (الشرق الأوسط)", "url": "reuters.com/places/middle-east/feed", "freq": "كل 15 دقيقة", "cat": "أخبار سياسية",
         "tip": "وكالة أنباء عالمية — قسم الشرق الأوسط. تغطي الأحداث الجيوسياسية التي تؤثر على استقرار سعر الصرف."},
        {"name": "سانا", "url": "sana.sy/feed", "freq": "كل 30 دقيقة", "cat": "أخبار رسمية",
         "tip": "الوكالة العربية السورية للأنباء (الرسمية). تنشر القرارات الحكومية والتصريحات الرسمية المؤثرة على السوق."},
        {"name": "العربي الجديد", "url": "alaraby.co.uk/feed", "freq": "كل 15 دقيقة", "cat": "أخبار شاملة",
         "tip": "موقع إخباري عربي شامل. يوفر تغطية واسعة للأحداث الإقليمية المؤثرة على الاقتصاد السوري."},
        {"name": "الجزيرة نت (سوريا)", "url": "aljazeera.net/xml/rss/syria", "freq": "كل 15 دقيقة", "cat": "أخبار شاملة",
         "tip": "قسم سوريا في شبكة الجزيرة الإعلامية. يغطي الأحداث السياسية والعسكرية ذات التأثير المباشر على سعر الصرف."},
    ]

    for src in rss_sources:
        col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
        with col1:
            st.markdown(f"""
            <div style="direction:rtl;">
                <strong style="color:#e2e8f0;">{src['name']}</strong>
                {info_tip(src['tip'])}
                <br><span style="color:#64748b; font-size:12px;">{src['url']}</span>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown(f"<span style='color:#94a3b8;'>{src['cat']}</span>", unsafe_allow_html=True)
        with col3:
            st.markdown(f"<span style='color:#94a3b8;'>⏱️ {src['freq']}</span>", unsafe_allow_html=True)
        with col4:
            st.markdown(status_badge("healthy"), unsafe_allow_html=True)
        st.markdown("<hr style='border-color:#1e293b; margin:5px 0;'>", unsafe_allow_html=True)

    # ── مؤشرات اقتصادية ──
    st.markdown(f"""
    <div class="section-header">
        <h2>🌍 المؤشرات الاقتصادية الخارجية</h2>
        {info_tip("مؤشرات اقتصادية عالمية تُستخدم كميزات إضافية لنماذج التنبؤ. تشمل أسعار الذهب والنفط ومؤشر الدولار. أظهرت الأبحاث أن هذه المؤشرات تحسن دقة التنبؤ بنسبة تصل إلى 10%.")}
    </div>
    """, unsafe_allow_html=True)

    ext_sources = [
        {"name": "سعر الذهب (XAU/USD)", "metric": "XAU_USD", "freq": "كل ساعة",
         "tip": "سعر أونصة الذهب بالدولار — مؤشر ملاذ آمن. يرتبط عكسياً مع قوة الدولار ويؤثر على سلوك المضاربين في السوق السوري."},
        {"name": "سعر النفط (Brent)", "metric": "BRENT", "freq": "كل ساعة",
         "tip": "سعر خام برنت — مؤشر اقتصادي كلي. يؤثر على تكلفة الاستيراد وميزان المدفوعات مما ينعكس على سعر الصرف."},
        {"name": "مؤشر الدولار (DXY)", "metric": "DXY", "freq": "يومياً",
         "tip": "مؤشر قوة الدولار مقابل سلة من 6 عملات رئيسية. ارتفاع DXY يعني قوة الدولار عالمياً مما يضغط على العملات الضعيفة كالليرة السورية."},
    ]

    for src in ext_sources:
        col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
        with col1:
            st.markdown(f"""
            <div style="direction:rtl;">
                <strong style="color:#e2e8f0;">{src['name']}</strong>
                {info_tip(src['tip'])}
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown(f"<span style='color:#94a3b8;'>📏 {src['metric']}</span>", unsafe_allow_html=True)
        with col3:
            st.markdown(f"<span style='color:#94a3b8;'>⏱️ {src['freq']}</span>", unsafe_allow_html=True)
        with col4:
            st.markdown(status_badge("healthy"), unsafe_allow_html=True)
        st.markdown("<hr style='border-color:#1e293b; margin:5px 0;'>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════
# صفحة: إدارة المصادر
# ══════════════════════════════════════════════════════════

elif page == "➕ إدارة المصادر":
    st.markdown(f"""
    <h1 style="text-align:right;">
        ➕ إدارة المصادر
        {info_tip("إضافة وتعديل وحذف مصادر البيانات بشكل ديناميكي. يمكنك إضافة أي مصدر RSS أو موقع ويب أو قناة تلغرام واختباره قبل التفعيل.")}
    </h1>
    """, unsafe_allow_html=True)

    # علامات تبويب لأنواع المصادر
    tab1, tab2, tab3 = st.tabs(["📰 مصادر RSS", "💰 مواقع الأسعار", "📱 قنوات تلغرام"])

    # ────────────────────────────────────────────────────────
    # Tab 1: مصادر RSS
    # ────────────────────────────────────────────────────────
    with tab1:
        st.markdown(f"""
        <div class="section-header" style="margin-top:15px;">
            <h2>إضافة مصدر RSS جديد</h2>
            {info_tip("أضف أي خلاصة RSS لموقع إخباري. سيتم جمع المقالات تلقائياً كل 15 دقيقة وتحليلها لاستخراج الأحداث المؤثرة على سعر الصرف.")}
        </div>
        """, unsafe_allow_html=True)

        # نموذج إضافة مصدر RSS
        with st.form("add_rss_source", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                rss_name = st.text_input(
                    "اسم المصدر",
                    placeholder="مثال: موقع إخباري سوري",
                    help="اسم مميز للمصدر"
                )
                rss_url = st.text_input(
                    "رابط RSS",
                    placeholder="https://example.com/feed",
                    help="عنوان URL الكامل لخلاصة RSS"
                )
            
            with col2:
                rss_category = st.selectbox(
                    "التصنيف",
                    ["أخبار اقتصادية", "أخبار سياسية", "أخبار عامة", "أخبار رسمية"],
                    help="تصنيف نوع الأخبار"
                )
                rss_language = st.selectbox(
                    "اللغة",
                    ["ar", "en", "fr"],
                    format_func=lambda x: {"ar": "العربية", "en": "الإنجليزية", "fr": "الفرنسية"}[x],
                    help="لغة المحتوى"
                )
            
            rss_enabled = st.checkbox("تفعيل المصدر فور الإضافة", value=True)
            
            col_test, col_submit = st.columns([1, 1])
            with col_test:
                test_rss = st.form_submit_button("🧪 اختبار المصدر", type="secondary", use_container_width=True)
            with col_submit:
                submit_rss = st.form_submit_button("➕ إضافة المصدر", type="primary", use_container_width=True)

        # معالجة الاختبار
        if test_rss and rss_url:
            with st.spinner("جاري اختبار المصدر..."):
                try:
                    from src.ingestion.collectors.rss_collector import RSSCollector
                    collector = RSSCollector(storage_db=False)
                    result = collector.collect_feed({
                        'name': rss_name or 'test',
                        'url': rss_url,
                        'category': rss_category,
                        'language': rss_language
                    })
                    collector.close()
                    
                    if result['success']:
                        st.success(f"✅ نجح الاختبار! تم العثور على {result['articles_count']} مقال")
                        if result['articles_count'] > 0:
                            st.info(f"📰 عينة: {result.get('sample_title', 'N/A')}")
                    else:
                        st.error(f"❌ فشل الاختبار: {result.get('error', 'خطأ غير معروف')}")
                except Exception as e:
                    st.error(f"❌ خطأ في الاختبار: {str(e)}")

        # معالجة الإضافة
        if submit_rss and rss_name and rss_url:
            try:
                import yaml
                config_path = 'config/sources.yaml'
                
                # قراءة الملف الحالي
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f) or {}
                
                if 'rss_sources' not in config:
                    config['rss_sources'] = {}
                
                # إضافة المصدر الجديد
                source_id = rss_name.lower().replace(' ', '_').replace('-', '_')
                config['rss_sources'][source_id] = {
                    'url': rss_url,
                    'category': rss_category,
                    'language': rss_language,
                    'enabled': rss_enabled
                }
                
                # حفظ الملف
                with open(config_path, 'w', encoding='utf-8') as f:
                    yaml.dump(config, f, allow_unicode=True, sort_keys=False)
                
                st.success(f"✅ تمت إضافة المصدر '{rss_name}' بنجاح!")
                st.info("🔄 سيبدأ جمع البيانات في الدورة القادمة (خلال 15 دقيقة)")
                
            except Exception as e:
                st.error(f"❌ خطأ في الإضافة: {str(e)}")

        # ── قائمة المصادر الحالية ──
        st.markdown(f"""
        <div class="section-header" style="margin-top:30px;">
            <h2>📋 المصادر الحالية</h2>
            {info_tip("جميع مصادر RSS المضافة حالياً. يمكنك تفعيل/تعطيل أي مصدر أو حذفه.")}
        </div>
        """, unsafe_allow_html=True)

        try:
            import yaml
            with open('config/sources.yaml', 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f) or {}
            
            rss_sources_list = config.get('rss_sources', {})
            
            if rss_sources_list:
                for source_id, details in rss_sources_list.items():
                    col1, col2, col3, col4 = st.columns([3, 2, 1, 1])
                    with col1:
                        enabled_icon = "✅" if details.get('enabled', True) else "⏸️"
                        st.markdown(f"{enabled_icon} **{source_id}**")
                        st.caption(details['url'])
                    with col2:
                        st.text(details.get('category', 'N/A'))
                    with col3:
                        st.text(details.get('language', 'ar'))
                    with col4:
                        if st.button("🗑️", key=f"del_rss_{source_id}", help="حذف"):
                            del config['rss_sources'][source_id]
                            with open('config/sources.yaml', 'w', encoding='utf-8') as f:
                                yaml.dump(config, f, allow_unicode=True, sort_keys=False)
                            st.rerun()
                    st.markdown("---")
            else:
                st.info("لا توجد مصادر RSS مضافة بعد")
        except Exception as e:
            st.error(f"خطأ في قراءة المصادر: {str(e)}")

    # ────────────────────────────────────────────────────────
    # Tab 2: مواقع الأسعار
    # ────────────────────────────────────────────────────────
    with tab2:
        st.markdown(f"""
        <div class="section-header" style="margin-top:15px;">
            <h2>إضافة موقع أسعار جديد</h2>
            {info_tip("أضف أي موقع يعرض أسعار الصرف. يمكنك تحديد CSS Selector أو نمط Regex لاستخراج السعر من الصفحة.")}
        </div>
        """, unsafe_allow_html=True)

        with st.form("add_web_source", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                web_name = st.text_input(
                    "اسم الموقع",
                    placeholder="مثال: موقع أسعار دمشق",
                    help="اسم مميز للموقع"
                )
                web_url = st.text_input(
                    "رابط الموقع",
                    placeholder="https://example.com/prices",
                    help="عنوان URL الكامل للصفحة"
                )
            
            with col2:
                web_location = st.text_input(
                    "الموقع الجغرافي",
                    placeholder="دمشق / حلب / السوق السوداء",
                    help="المدينة أو نوع السعر"
                )
                extraction_method = st.selectbox(
                    "طريقة الاستخراج",
                    ["css_selector", "regex", "xpath"],
                    format_func=lambda x: {
                        "css_selector": "CSS Selector",
                        "regex": "نمط Regex",
                        "xpath": "XPath"
                    }[x]
                )
            
            extraction_pattern = st.text_input(
                "نمط الاستخراج",
                placeholder="مثال: .price-value أو \\d+\\.\\d+",
                help="CSS Selector أو Regex حسب الطريقة المختارة"
            )
            
            web_enabled = st.checkbox("تفعيل الموقع فور الإضافة", value=True)
            
            col_test, col_submit = st.columns([1, 1])
            with col_test:
                test_web = st.form_submit_button("🧪 اختبار الموقع", type="secondary", use_container_width=True)
            with col_submit:
                submit_web = st.form_submit_button("➕ إضافة الموقع", type="primary", use_container_width=True)

        # معالجة الاختبار
        if test_web and web_url:
            st.info("🔧 وظيفة الاختبار قيد التطوير — سيتم إضافتها قريباً")

        # معالجة الإضافة
        if submit_web and web_name and web_url:
            try:
                import yaml
                config_path = 'config/sources.yaml'
                
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f) or {}
                
                if 'price_websites' not in config:
                    config['price_websites'] = {}
                
                source_id = web_name.lower().replace(' ', '_').replace('-', '_')
                config['price_websites'][source_id] = {
                    'url': web_url,
                    'location': web_location,
                    'extraction_method': extraction_method,
                    'extraction_pattern': extraction_pattern,
                    'enabled': web_enabled
                }
                
                with open(config_path, 'w', encoding='utf-8') as f:
                    yaml.dump(config, f, allow_unicode=True, sort_keys=False)
                
                st.success(f"✅ تمت إضافة الموقع '{web_name}' بنجاح!")
                st.warning("⚠️ ملاحظة: WebScraper حالياً يدعم 3 مواقع محددة. ستحتاج لتعديل الكود لإضافة مواقع جديدة.")
                
            except Exception as e:
                st.error(f"❌ خطأ في الإضافة: {str(e)}")

        # قائمة المواقع الحالية
        st.markdown(f"""
        <div class="section-header" style="margin-top:30px;">
            <h2>📋 المواقع الحالية</h2>
        </div>
        """, unsafe_allow_html=True)

        try:
            import yaml
            with open('config/sources.yaml', 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f) or {}
            
            web_sources_list = config.get('price_websites', {})
            
            if web_sources_list:
                for source_id, details in web_sources_list.items():
                    col1, col2, col3 = st.columns([3, 2, 1])
                    with col1:
                        enabled_icon = "✅" if details.get('enabled', True) else "⏸️"
                        st.markdown(f"{enabled_icon} **{source_id}**")
                        st.caption(details['url'])
                    with col2:
                        st.text(details.get('location', 'N/A'))
                    with col3:
                        if st.button("🗑️", key=f"del_web_{source_id}", help="حذف"):
                            del config['price_websites'][source_id]
                            with open('config/sources.yaml', 'w', encoding='utf-8') as f:
                                yaml.dump(config, f, allow_unicode=True, sort_keys=False)
                            st.rerun()
                    st.markdown("---")
            else:
                st.info("لا توجد مواقع أسعار مضافة بعد")
        except Exception as e:
            st.error(f"خطأ في قراءة المواقع: {str(e)}")

    # ────────────────────────────────────────────────────────
    # Tab 3: قنوات تلغرام
    # ────────────────────────────────────────────────────────
    with tab3:
        st.markdown(f"""
        <div class="section-header" style="margin-top:15px;">
            <h2>إضافة قناة تلغرام</h2>
            {info_tip("أضف أي قناة تلغرام عامة تنشر أسعار الصرف أو الأخبار الاقتصادية. يجب إعداد TELEGRAM_API_ID أولاً.")}
        </div>
        """, unsafe_allow_html=True)

        # التحقق من إعداد تلغرام
        telegram_configured = bool(os.getenv("TELEGRAM_API_ID"))
        if not telegram_configured:
            st.error("""
            ⚠️ **بيانات اعتماد Telegram غير مهيأة**
            
            لإضافة قنوات تلغرام، يجب أولاً:
            1. الحصول على API_ID و API_HASH من https://my.telegram.org
            2. إضافتهم إلى ملف `.env`:
               ```
               TELEGRAM_API_ID=your_api_id
               TELEGRAM_API_HASH=your_api_hash
               ```
            3. إعادة تشغيل التطبيق
            """)
        else:
            with st.form("add_telegram_source", clear_on_submit=True):
                col1, col2 = st.columns(2)
                with col1:
                    tg_name = st.text_input(
                        "اسم القناة",
                        placeholder="مثال: قناة أسعار دمشق",
                        help="اسم مميز للقناة"
                    )
                    tg_username = st.text_input(
                        "معرّف القناة",
                        placeholder="@channel_username",
                        help="اسم المستخدم للقناة (يبدأ بـ @)"
                    )
                
                with col2:
                    tg_type = st.selectbox(
                        "نوع المحتوى",
                        ["أسعار", "أخبار اقتصادية", "أخبار عامة"],
                        help="نوع البيانات المنشورة في القناة"
                    )
                    tg_language = st.selectbox(
                        "اللغة",
                        ["ar", "en"],
                        format_func=lambda x: {"ar": "العربية", "en": "الإنجليزية"}[x]
                    )
                
                tg_enabled = st.checkbox("تفعيل القناة فور الإضافة", value=True)
                
                submit_tg = st.form_submit_button("➕ إضافة القناة", type="primary", use_container_width=True)

            if submit_tg and tg_name and tg_username:
                try:
                    import yaml
                    config_path = 'config/sources.yaml'
                    
                    with open(config_path, 'r', encoding='utf-8') as f:
                        config = yaml.safe_load(f) or {}
                    
                    if 'telegram_channels' not in config:
                        config['telegram_channels'] = {}
                    
                    source_id = tg_name.lower().replace(' ', '_').replace('-', '_')
                    config['telegram_channels'][source_id] = {
                        'username': tg_username,
                        'type': tg_type,
                        'language': tg_language,
                        'enabled': tg_enabled
                    }
                    
                    with open(config_path, 'w', encoding='utf-8') as f:
                        yaml.dump(config, f, allow_unicode=True, sort_keys=False)
                    
                    st.success(f"✅ تمت إضافة القناة '{tg_name}' بنجاح!")
                    st.info("🔄 سيبدأ جمع البيانات في الدورة القادمة")
                    
                except Exception as e:
                    st.error(f"❌ خطأ في الإضافة: {str(e)}")

            # قائمة القنوات الحالية
            st.markdown(f"""
            <div class="section-header" style="margin-top:30px;">
                <h2>📋 القنوات الحالية</h2>
            </div>
            """, unsafe_allow_html=True)

            try:
                import yaml
                with open('config/sources.yaml', 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f) or {}
                
                tg_sources_list = config.get('telegram_channels', {})
                
                if tg_sources_list:
                    for source_id, details in tg_sources_list.items():
                        col1, col2, col3 = st.columns([3, 2, 1])
                        with col1:
                            enabled_icon = "✅" if details.get('enabled', True) else "⏸️"
                            st.markdown(f"{enabled_icon} **{source_id}**")
                            st.caption(details.get('username', 'N/A'))
                        with col2:
                            st.text(details.get('type', 'N/A'))
                        with col3:
                            if st.button("🗑️", key=f"del_tg_{source_id}", help="حذف"):
                                del config['telegram_channels'][source_id]
                                with open('config/sources.yaml', 'w', encoding='utf-8') as f:
                                    yaml.dump(config, f, allow_unicode=True, sort_keys=False)
                                st.rerun()
                        st.markdown("---")
                else:
                    st.info("لا توجد قنوات تلغرام مضافة بعد")
            except Exception as e:
                st.error(f"خطأ في قراءة القنوات: {str(e)}")


# ══════════════════════════════════════════════════════════
# صفحة: أسعار الصرف
# ══════════════════════════════════════════════════════════

elif page == "💱 أسعار الصرف":
    st.markdown(f"""
    <h1 style="text-align:right;">
        💱 أسعار الصرف
        {info_tip("تتبع أسعار صرف الليرة السورية مقابل الدولار من مصادر متعددة. يُعرض السعر الحالي والتغير والرسم البياني التاريخي.")}
    </h1>
    """, unsafe_allow_html=True)

    # محاولة جلب بيانات من InfluxDB
    prices_data = []
    try:
        from src.storage.timeseries_db import TimeSeriesDB
        tsdb = TimeSeriesDB()
        prices_data = tsdb.query_prices("exchange_rates", range_hours=168)
        tsdb.close()
    except Exception:
        pass

    if prices_data:
        import pandas as pd
        df = pd.DataFrame(prices_data)
        df['time'] = pd.to_datetime(df['time'])

        col1, col2, col3 = st.columns(3)
        latest = df.iloc[-1]['value'] if len(df) > 0 else 0
        prev = df.iloc[-2]['value'] if len(df) > 1 else latest
        change = latest - prev
        change_pct = (change / prev * 100) if prev else 0

        with col1:
            st.markdown(metric_card(
                "آخر سعر مسجل",
                f"{latest:,.0f} ل.س",
                "مقابل 1 دولار أمريكي",
                "آخر سعر تم تسجيله في قاعدة بيانات InfluxDB من أي مصدر نشط."
            ), unsafe_allow_html=True)
        with col2:
            arrow = "📈" if change > 0 else "📉" if change < 0 else "➡️"
            st.markdown(metric_card(
                "التغير",
                f"{arrow} {change:+,.0f} ({change_pct:+.2f}%)",
                "مقارنة بآخر قراءة",
                "الفرق بين آخر قراءتين مسجلتين. الأسهم تشير لاتجاه التغير."
            ), unsafe_allow_html=True)
        with col3:
            st.markdown(metric_card(
                "عدد القراءات",
                f"{len(df):,}",
                "آخر 7 أيام",
                "إجمالي نقاط البيانات المسجلة في آخر أسبوع من جميع المصادر."
            ), unsafe_allow_html=True)

        # رسم بياني
        st.markdown(f"""
        <div class="section-header">
            <h2>📈 الرسم البياني</h2>
            {info_tip("رسم بياني يوضح تحرك سعر الصرف عبر الزمن. كل خط يمثل مصدر بيانات مختلف. يمكنك التكبير والتصغير بعجلة الماوس.")}
        </div>
        """, unsafe_allow_html=True)

        fig = px.line(df, x='time', y='value', color='source',
                      labels={'time': 'الوقت', 'value': 'السعر (ل.س)', 'source': 'المصدر'})
        fig.update_layout(
            template="plotly_dark",
            xaxis_title="الوقت",
            yaxis_title="سعر الدولار (ل.س)",
            legend_title="المصدر",
            height=450,
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("📊 لم يتم تسجيل أي أسعار بعد. ستظهر البيانات هنا بمجرد أن تبدأ جامعات البيانات بالعمل وتسجيل الأسعار في InfluxDB.")

        st.markdown(f"""
        <div class="section-header">
            <h2>📖 كيف يعمل تتبع الأسعار؟</h2>
            {info_tip("شرح خطوات جمع وتخزين أسعار الصرف من المصادر المختلفة.")}
        </div>
        """, unsafe_allow_html=True)

        steps = [
            ("1️⃣ الجمع", "Celery Beat يُشغّل مهام الجمع تلقائياً حسب الجدول المحدد لكل مصدر.",
             "مثلاً: collect_web_prices كل 5 دقائق تسحب الأسعار من sp-today.com و investing.com"),
            ("2️⃣ الاستخراج", "Regex متخصص يستخرج القيم الرقمية من النصوص أو HTML.",
             "يتعرف على أنماط مثل: الدولار 14500 ل.س"),
            ("3️⃣ التخزين", "الأسعار تُحفظ في InfluxDB مع طابع زمني ووسم المصدر.",
             "كل نقطة بيانات تحتوي: السعر + المصدر + الوقت الدقيق بالميلي ثانية"),
            ("4️⃣ العرض", "لوحة التحكم تقرأ البيانات وتعرضها كرسم بياني تفاعلي.",
             "يدعم التكبير والتصغير والفلترة حسب المصدر والفترة الزمنية"),
        ]

        for title, desc, detail in steps:
            st.markdown(f"""
            <div style="padding:12px 15px; border-right:3px solid #3b82f6; margin:8px 0; direction:rtl;">
                <strong style="color:#e2e8f0;">{title}</strong>
                {info_tip(detail)}
                <br><span style="color:#94a3b8;">{desc}</span>
            </div>
            """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════
# صفحة: نماذج التنبؤ
# ══════════════════════════════════════════════════════════

elif page == "🤖 نماذج التنبؤ":
    st.markdown(f"""
    <h1 style="text-align:right;">
        🤖 نماذج التنبؤ
        {info_tip("نماذج التعلم الآلي والتعلم العميق المستخدمة للتنبؤ بسعر الصرف. النظام يستخدم أسلوب Ensemble (تكامل متعدد النماذج) لتحقيق أعلى دقة.")}
    </h1>
    """, unsafe_allow_html=True)

    # ── نماذج Baseline (المرحلة 4) ──
    st.markdown(f"""
    <div class="section-header">
        <h2>📐 نماذج Baseline (خط الأساس)</h2>
        {info_tip("نماذج تعلم آلي كلاسيكية تُستخدم كخط أساس للمقارنة. سريعة التدريب وقابلة للتفسير بسهولة لكنها أقل دقة من نماذج التعلم العميق.")}
    </div>
    """, unsafe_allow_html=True)

    baseline_models = [
        {
            "name": "XGBoost",
            "desc": "Gradient Boosting قوي للبيانات الجدولية",
            "tip": "XGBoost (eXtreme Gradient Boosting): نموذج أشجار قرار متقدم يبني أشجاراً متتالية كل واحدة تصحح أخطاء السابقة. ممتاز للبيانات الجدولية والميزات المهندسة. يُستخدم لتوقع السعر بعد 24 ساعة. المعاملات: max_depth=6, n_estimators=500, learning_rate=0.05.",
            "metrics": "MAE · RMSE · MAPE",
        },
        {
            "name": "Random Forest",
            "desc": "غابة عشوائية لتقليل الإفراط في التعلم",
            "tip": "Random Forest: مجموعة من أشجار القرار المستقلة تُدرَّب على عينات عشوائية مختلفة ثم يُؤخذ متوسط توقعاتها. أقل عرضة للـ Overfitting من XGBoost. يُستخدم كنموذج مرجعي.",
            "metrics": "MAE · RMSE · MAPE",
        },
        {
            "name": "Holt-Winters (HLT)",
            "desc": "تحليل سلاسل زمنية كلاسيكي",
            "tip": "Triple Exponential Smoothing: نموذج إحصائي كلاسيكي يحلل ثلاث مكونات: المستوى + الاتجاه + الموسمية. بسيط وسريع ولا يحتاج بيانات كثيرة. مناسب كخط أساس أولي.",
            "metrics": "MAE · RMSE",
        },
    ]

    for model in baseline_models:
        st.markdown(f"""
        <div class="metric-card">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <span>
                    <strong style="color:#e2e8f0; font-size:16px;">{model['name']}</strong>
                    {info_tip(model['tip'])}
                </span>
                {status_badge('pending')}
            </div>
            <div style="color:#94a3b8; margin-top:8px;">{model['desc']}</div>
            <div style="color:#64748b; margin-top:4px; font-size:12px;">مقاييس الأداء: {model['metrics']}</div>
        </div>
        """, unsafe_allow_html=True)

    # ── نماذج التعلم العميق (المرحلة 5) ──
    st.markdown(f"""
    <div class="section-header">
        <h2>🧠 نماذج التعلم العميق</h2>
        {info_tip("نماذج شبكات عصبية عميقة متخصصة في السلاسل الزمنية. أكثر دقة لكنها تحتاج بيانات أكثر ووقت تدريب أطول. تُفعَّل في المرحلة 5.")}
    </div>
    """, unsafe_allow_html=True)

    dl_models = [
        {
            "name": "TFT (Temporal Fusion Transformer)",
            "desc": "النموذج الرئيسي — Transformer متخصص بالسلاسل الزمنية",
            "tip": "Temporal Fusion Transformer: أحدث وأقوى نماذج التنبؤ بالسلاسل الزمنية. يدمج آلية Attention للتركيز على الفترات المهمة + Variable Selection لاختيار الميزات الأكثر تأثيراً تلقائياً + Multi-horizon للتنبؤ بآفاق زمنية متعددة (24 و 72 ساعة). الإعدادات: encoder_length=168, prediction_length=72, attention_head_size=4.",
        },
        {
            "name": "Bi-LSTM",
            "desc": "شبكة ذاكرة ثنائية الاتجاه",
            "tip": "Bidirectional LSTM: شبكة عصبية تتذكر السياق من الماضي والمستقبل معاً. تعالج السلسلة الزمنية بالاتجاهين لالتقاط أنماط أعمق. تُستخدم في فرع تحليل المشاعر لتحويل تسلسل المشاعر إلى إشارات تنبؤية."
        },
        {
            "name": "GRU",
            "desc": "شبكة بوابية أبسط وأسرع من LSTM",
            "tip": "Gated Recurrent Unit: نسخة مبسطة من LSTM بمعاملات أقل (بوابتان بدل ثلاث). أسرع في التدريب مع أداء مشابه. تُستخدم لنمذجة المكونات الفرعية بعد تفكيك OCEEMDAN."
        },
        {
            "name": "CNN-1D",
            "desc": "شبكة التفافية لاستخراج الأنماط المحلية",
            "tip": "Convolutional Neural Network 1D: تطبق فلاتر التفافية على السلسلة الزمنية لاكتشاف الأنماط المحلية والتكرارية. مفيدة خاصة لاكتشاف أنماط التقلب قصيرة المدى."
        },
    ]

    for model in dl_models:
        st.markdown(f"""
        <div class="metric-card">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <span>
                    <strong style="color:#e2e8f0; font-size:16px;">{model['name']}</strong>
                    {info_tip(model['tip'])}
                </span>
                {status_badge('pending')}
            </div>
            <div style="color:#94a3b8; margin-top:8px;">{model['desc']}</div>
        </div>
        """, unsafe_allow_html=True)

    # ── Ensemble ──
    st.markdown(f"""
    <div class="section-header">
        <h2>🔗 نموذج Ensemble (التكامل)</h2>
        {info_tip("الأسلوب التكاملي: يجمع توقعات جميع النماذج بأوزان ديناميكية مُحسَّنة لتحقيق أعلى دقة. الفكرة أن ضعف نموذج واحد يُعوَّض بقوة نموذج آخر.")}
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="metric-card" style="border-color:#3b82f6;">
        <strong style="color:#e2e8f0; font-size:16px;">⚡ Hybrid Weighted Ensemble</strong>
        {info_tip("نظام التكامل الهجين: يأخذ توقعات 3 فروع (فرع السلاسل الزمنية + فرع المشاعر + فرع Baseline) ويجمعها بأوزان ديناميكية محسَّنة بخوارزمية ZOA (Zebra Optimization). الأوزان تتكيف تلقائياً حسب أداء كل نموذج في الفترة الأخيرة.")}
        <div style="margin-top:12px;">
            <div style="color:#94a3b8;">الفروع الثلاثة:</div>
            <div style="padding:8px 15px; margin:5px 0; background:#0f172a; border-radius:8px; color:#e2e8f0;">
                🔹 فرع السلاسل الزمنية (TFT + GRU + CNN) {info_tip("يحلل الأنماط التاريخية لسعر الصرف والمؤشرات الاقتصادية للتنبؤ بالقيمة المستقبلية.")}
            </div>
            <div style="padding:8px 15px; margin:5px 0; background:#0f172a; border-radius:8px; color:#e2e8f0;">
                🔹 فرع المشاعر (Bi-LSTM + Sentiment Scores) {info_tip("يحلل مشاعر الأخبار ومنشورات تلغرام لاستشراف اتجاه السوق. المشاعر السلبية تعني ضغط بيع وارتفاع متوقع للدولار.")}
            </div>
            <div style="padding:8px 15px; margin:5px 0; background:#0f172a; border-radius:8px; color:#e2e8f0;">
                🔹 فرع Baseline (XGBoost + Random Forest) {info_tip("نماذج كلاسيكية تعمل على الميزات المهندسة. توفر استقراراً وتقلل من التقلب في التوقعات النهائية.")}
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════
# صفحة: الأحداث والأخبار
# ══════════════════════════════════════════════════════════

elif page == "📰 الأحداث والأخبار":
    st.markdown(f"""
    <h1 style="text-align:right;">
        📰 الأحداث والأخبار
        {info_tip("نظام تصنيف الأحداث: يجمع الأخبار من المصادر المختلفة ثم يصنفها حسب نوعها (عسكري، سياسي، اقتصادي، عقوبات) ويحدد تأثيرها المتوقع على سعر الصرف بوزن رقمي.")}
    </h1>
    """, unsafe_allow_html=True)

    # ── تصنيف الأحداث ──
    st.markdown(f"""
    <div class="section-header">
        <h2>🏷️ تصنيفات الأحداث</h2>
        {info_tip("كل خبر يُصنَّف تلقائياً إلى فئة ويُعطى وزن تأثير (من 0 إلى 1). الأحداث ذات الوزن العالي تؤثر أكثر على نماذج التنبؤ.")}
    </div>
    """, unsafe_allow_html=True)

    event_types = [
        {"icon": "⚔️", "name": "أحداث عسكرية", "weight": "0.9 - 1.0", "color": "#ef4444",
         "tip": "عمليات عسكرية، معارك، قصف، تغيير سيطرة. أعلى تأثير على سعر الصرف — تسبب تقلبات حادة وفورية في السوق.",
         "examples": "غارة جوية على حلب · معركة في إدلب · سيطرة على منطقة جديدة"},
        {"icon": "🏛️", "name": "أحداث سياسية", "weight": "0.7 - 0.9", "color": "#f59e0b",
         "tip": "قرارات حكومية، مفاوضات، تغييرات دبلوماسية. تؤثر على المدى المتوسط (أيام) وقد تسبب تحولات في اتجاه السعر.",
         "examples": "مفاوضات جنيف · تعيين حاكم المركزي · اعتراف دولي"},
        {"icon": "💰", "name": "أحداث اقتصادية", "weight": "0.6 - 0.8", "color": "#3b82f6",
         "tip": "بيانات اقتصادية، سياسات مالية، تغير أسعار سلع. تؤثر تدريجياً ويمكن التنبؤ باتجاهها.",
         "examples": "طباعة نقود جديدة · رفع الدعم · تراجع الصادرات"},
        {"icon": "🚫", "name": "عقوبات دولية", "weight": "0.8 - 1.0", "color": "#a855f7",
         "tip": "عقوبات أمريكية أو أوروبية جديدة أو رفع عقوبات. تأثير فوري على التدفقات المالية وسعر الصرف.",
         "examples": "عقوبات قيصر · عقوبات EU جديدة · إعفاءات إنسانية"},
        {"icon": "🌍", "name": "أحداث إقليمية", "weight": "0.4 - 0.7", "color": "#22c55e",
         "tip": "أحداث في الدول المجاورة (لبنان، تركيا، العراق) تؤثر على الاقتصاد السوري عبر التجارة والحوالات.",
         "examples": "انهيار الليرة اللبنانية · تغيير سياسة تركيا · أزمة عراقية"},
    ]

    for evt in event_types:
        st.markdown(f"""
        <div class="metric-card" style="border-right: 3px solid {evt['color']};">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <span>
                    <strong style="color:#e2e8f0;">{evt['icon']} {evt['name']}</strong>
                    {info_tip(evt['tip'])}
                </span>
                <span style="color:{evt['color']}; font-weight:600;">وزن التأثير: {evt['weight']}</span>
            </div>
            <div style="color:#64748b; margin-top:6px; font-size:12px;">أمثلة: {evt['examples']}</div>
        </div>
        """, unsafe_allow_html=True)

    # ── تحليل المشاعر ──
    st.markdown(f"""
    <div class="section-header">
        <h2>😊😐😠 تحليل المشاعر</h2>
        {info_tip("محرك تحليل المشاعر يحدد النبرة العاطفية لكل خبر: إيجابي (تفاؤل اقتصادي) · سلبي (قلق وتشاؤم) · محايد (خبر واقعي). يُستخدم كميزة إضافية في نماذج التنبؤ.")}
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(metric_card(
            "😊 إيجابي",
            "قيد الإعداد",
            "تفاؤل اقتصادي · استقرار · نمو",
            "مشاعر إيجابية: أخبار عن استقرار، تحسن اقتصادي، مفاوضات ناجحة. ترتبط عادة بانخفاض سعر الدولار (تحسن الليرة)."
        ), unsafe_allow_html=True)
    with col2:
        st.markdown(metric_card(
            "😐 محايد",
            "قيد الإعداد",
            "أخبار واقعية · تقارير وصفية",
            "مشاعر محايدة: أخبار تقريرية بدون نبرة عاطفية واضحة. تُعتبر إشارة على استقرار السوق في الفترة القادمة."
        ), unsafe_allow_html=True)
    with col3:
        st.markdown(metric_card(
            "😠 سلبي",
            "قيد الإعداد",
            "تصعيد · أزمة · عقوبات",
            "مشاعر سلبية: أخبار عن تصعيد عسكري، عقوبات جديدة، أزمات اقتصادية. ترتبط بارتفاع سعر الدولار (تراجع الليرة)."
        ), unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════
# صفحة: أداء النظام
# ══════════════════════════════════════════════════════════

elif page == "📊 أداء النظام":
    st.markdown(f"""
    <h1 style="text-align:right;">
        📊 أداء النظام
        {info_tip("مقاييس أداء شاملة لجميع مكونات النظام: من جمع البيانات إلى التنبؤ. يتم تحديث المقاييس تلقائياً ومقارنتها بالأهداف المحددة في TARGET.MD.")}
    </h1>
    """, unsafe_allow_html=True)

    # ── مقاييس النماذج ──
    st.markdown(f"""
    <div class="section-header">
        <h2>🎯 مقاييس دقة التنبؤ (الأهداف)</h2>
        {info_tip("مقاييس الأداء المستهدفة وفق خطة المشروع. ستُقارن النتائج الفعلية بهذه الأهداف بعد تدريب النماذج.")}
    </div>
    """, unsafe_allow_html=True)

    metrics_targets = [
        {"name": "MAE (متوسط الخطأ المطلق)", "target": "< 2%",
         "tip": "Mean Absolute Error: متوسط الفرق المطلق بين السعر المتوقع والفعلي. مثلاً إذا توقعنا 14500 والفعلي 14600، MAE = 100 ل.س. الهدف أقل من 2%."},
        {"name": "RMSE (جذر متوسط مربع الخطأ)", "target": "< 3%",
         "tip": "Root Mean Squared Error: مثل MAE لكن يعاقب الأخطاء الكبيرة أكثر. مفيد لاكتشاف التنبؤات البعيدة جداً عن الواقع. الهدف أقل من 3%."},
        {"name": "MAPE (متوسط نسبة الخطأ المطلق)", "target": "< 1%",
         "tip": "Mean Absolute Percentage Error: النسبة المئوية للخطأ. مقياس موحد يسهل المقارنة بين فترات مختلفة. الهدف أقل من 1%."},
        {"name": "دقة الاتجاه", "target": "> 75%",
         "tip": "Direction Accuracy: نسبة التوقعات التي أصابت اتجاه السعر (صعود/هبوط/استقرار) بشكل صحيح. حتى لو أخطأ النموذج في القيمة الدقيقة، إصابة الاتجاه مهمة لصناع القرار."},
    ]

    for metric in metrics_targets:
        col1, col2, col3 = st.columns([4, 2, 2])
        with col1:
            st.markdown(f"""
            <strong style="color:#e2e8f0;">{metric['name']}</strong>
            {info_tip(metric['tip'])}
            """, unsafe_allow_html=True)
        with col2:
            st.markdown(f"<span style='color:#3b82f6; font-weight:600;'>🎯 الهدف: {metric['target']}</span>", unsafe_allow_html=True)
        with col3:
            st.markdown(f"{status_badge('pending')}<span style='color:#64748b; margin-right:8px;'> بانتظار التدريب</span>", unsafe_allow_html=True)
        st.markdown("<hr style='border-color:#1e293b; margin:5px 0;'>", unsafe_allow_html=True)

    # ── صحة الخدمات ──
    st.markdown(f"""
    <div class="section-header">
        <h2>🏥 صحة البنية التحتية</h2>
        {info_tip("حالة كل خدمة في الوقت الفعلي مع تفاصيل الاتصال. الخدمة الصحية تعني أنها متصلة وتستجيب للطلبات.")}
    </div>
    """, unsafe_allow_html=True)

    all_services = ["postgres", "influxdb", "redis", "minio"]
    service_names = {"postgres": "PostgreSQL", "influxdb": "InfluxDB", "redis": "Redis", "minio": "MinIO"}
    service_tips = {
        "postgres": "قاعدة البيانات العلائقية — تخزن الجداول الهيكلية: raw_data, classified_events, predictions, model_metrics.",
        "influxdb": "قاعدة السلاسل الزمنية — تخزن أسعار الصرف والمؤشرات بدقة زمنية عالية (ميلي ثانية).",
        "redis": "وسيط الرسائل — يدير طابور مهام Celery (5 مهام) ويخزن النتائج المؤقتة والكاش.",
        "minio": "تخزين الكائنات — يحفظ ملفات النماذج (.pth) والبيانات الخام (JSON, CSV) بتنسيق S3.",
    }

    for svc in all_services:
        result = check_service(svc)
        col1, col2, col3 = st.columns([3, 2, 3])
        with col1:
            st.markdown(f"""
            <strong style="color:#e2e8f0;">{service_names[svc]}</strong>
            {info_tip(service_tips[svc])}
            """, unsafe_allow_html=True)
        with col2:
            st.markdown(status_badge(result["status"]), unsafe_allow_html=True)
        with col3:
            st.markdown(f"<span style='color:#64748b;'>{result['detail']}</span>", unsafe_allow_html=True)
        st.markdown("<hr style='border-color:#1e293b; margin:5px 0;'>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════
# صفحة: التنبيهات
# ══════════════════════════════════════════════════════════

elif page == "🔔 التنبيهات":
    st.markdown(f"""
    <h1 style="text-align:right;">
        🔔 نظام التنبيهات
        {info_tip("نظام إنذار آلي يراقب الأحداث المهمة ويرسل تنبيهات عبر بوت تلغرام. يشمل: تغير حاد بالسعر، خطأ تنبؤي كبير، تعطل مصدر بيانات، انحراف بيانات، تدهور أداء نموذج.")}
    </h1>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="section-header">
        <h2>📋 قواعد التنبيه</h2>
        {info_tip("كل قاعدة تحدد شرطاً معيناً. عند تحققه يُرسل تنبيه فوري إلى حساب المسؤول على تلغرام مع تفاصيل الحدث.")}
    </div>
    """, unsafe_allow_html=True)

    alert_rules = [
        {"icon": "📈", "name": "تغير حاد بالسعر", "condition": "تغير > 5% خلال ساعة",
         "severity": "عاجل 🔴",
         "tip": "يُطلَق عند تغير سعر الصرف بأكثر من 5% في ساعة واحدة. هذا يشير لحدث استثنائي (عسكري أو سياسي) يستوجب مراجعة فورية."},
        {"icon": "🎯", "name": "خطأ تنبؤي كبير", "condition": "خطأ التنبؤ > 3%",
         "severity": "تحذير 🟡",
         "tip": "يُطلَق عندما يتجاوز الفرق بين التوقع والواقع 3%. قد يعني أن النموذج يحتاج إعادة تدريب أو أن حدثاً غير متوقع وقع."},
        {"icon": "🔌", "name": "تعطل مصدر بيانات", "condition": "عدم استجابة > 60 دقيقة",
         "severity": "تحذير 🟡",
         "tip": "يُطلَق عند فشل جمع البيانات من مصدر لأكثر من ساعة. قد يكون المصدر معطل أو تم حظر الوصول. يتم المحاولة مع Exponential Backoff."},
        {"icon": "📊", "name": "انحراف البيانات (Drift)", "condition": "KL Divergence > حد",
         "severity": "إخطار 🔵",
         "tip": "Data Drift: يكشف تغيراً في توزيع البيانات الواردة مقارنة ببيانات التدريب. إذا تغير التوزيع كثيراً، النموذج قد يفقد دقته ويحتاج إعادة تدريب."},
        {"icon": "⚠️", "name": "تدهور أداء النموذج", "condition": "MAPE > 2% لـ 3 أيام",
         "severity": "تحذير 🟡",
         "tip": "Model Degradation: يُطلَق عندما يبقى خطأ النموذج مرتفعاً لعدة أيام متتالية. يشير لتغير بنيوي في السوق يستوجب إعادة تدريب أو تعديل المعاملات."},
    ]

    for rule in alert_rules:
        st.markdown(f"""
        <div class="metric-card">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <span>
                    <strong style="color:#e2e8f0;">{rule['icon']} {rule['name']}</strong>
                    {info_tip(rule['tip'])}
                </span>
                <span style="font-size:13px;">{rule['severity']}</span>
            </div>
            <div style="color:#94a3b8; margin-top:8px;">الشرط: {rule['condition']}</div>
        </div>
        """, unsafe_allow_html=True)

    # ── إعداد Telegram Bot ──
    st.markdown(f"""
    <div class="section-header">
        <h2>🤖 بوت التنبيهات (Telegram)</h2>
        {info_tip("التنبيهات تُرسل عبر بوت Telegram إلى حساب المسؤول. يجب تهيئة TELEGRAM_BOT_TOKEN و ADMIN_CHAT_ID في ملف .env لتفعيل هذه الميزة.")}
    </div>
    """, unsafe_allow_html=True)

    bot_configured = bool(os.getenv("TELEGRAM_BOT_TOKEN"))
    if bot_configured:
        st.success("✅ بوت تلغرام مهيأ وجاهز للعمل")
    else:
        st.warning("⚠️ بوت التنبيهات غير مهيأ. أضف المتغيرات التالية في ملف .env:")
        st.code("TELEGRAM_BOT_TOKEN=your_bot_token\nADMIN_CHAT_ID=your_chat_id", language="bash")


# ══════════════════════════════════════════════════════════
# صفحة: الإعدادات
# ══════════════════════════════════════════════════════════

elif page == "⚙️ الإعدادات":
    st.markdown(f"""
    <h1 style="text-align:right;">
        ⚙️ إعدادات النظام
        {info_tip("عرض الإعدادات الحالية للنظام من ملفات التهيئة (YAML). التعديل يتم مباشرة على ملفات config/ ثم إعادة تشغيل الخدمة المعنية.")}
    </h1>
    """, unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["⚙️ عام", "🤖 النماذج", "🔔 التنبيهات"])

    with tab1:
        st.markdown(f"""
        <div class="section-header">
            <h2>الإعدادات العامة</h2>
            {info_tip("إعدادات المشروع الأساسية من ملف config/settings.yaml: اسم المشروع والإصدار ومستوى تسجيل الأحداث وترددات المراقبة.")}
        </div>
        """, unsafe_allow_html=True)

        settings = {
            "اسم المشروع": ("ShamIn", "الاسم المعرِّف للنظام في السجلات والتقارير"),
            "الإصدار": ("1.0.0-beta", "إصدار تجريبي — المرحلة الأولى من التنفيذ"),
            "البيئة": ("development", "بيئة التطوير. ستُغيَّر إلى production عند الإطلاق الفعلي"),
            "مستوى السجل": ("INFO", "مستوى تسجيل الأحداث: DEBUG (تفصيلي) · INFO (عام) · WARNING (تحذيرات) · ERROR (أخطاء)"),
            "فحص الانحراف": ("كل 24 ساعة", "تردد فحص انحراف البيانات Drift Detection للتأكد من ثبات توزيع البيانات"),
            "فحص الجودة": ("كل 6 ساعات", "تردد فحص جودة البيانات: نسبة القيم المفقودة والقيم الشاذة وتحديث المصادر"),
        }

        for key, (value, tip) in settings.items():
            col1, col2 = st.columns([3, 4])
            with col1:
                st.markdown(f"""
                <strong style="color:#e2e8f0;">{key}</strong>
                {info_tip(tip)}
                """, unsafe_allow_html=True)
            with col2:
                st.markdown(f"<span style='color:#94a3b8;'>{value}</span>", unsafe_allow_html=True)
            st.markdown("<hr style='border-color:#1e293b; margin:5px 0;'>", unsafe_allow_html=True)

    with tab2:
        st.markdown(f"""
        <div class="section-header">
            <h2>إعدادات النماذج</h2>
            {info_tip("معاملات نماذج التنبؤ من ملف config/model_config.yaml. هذه المعاملات تُحسَّن لاحقاً تلقائياً بـ Optuna (Bayesian Optimization).")}
        </div>
        """, unsafe_allow_html=True)

        model_settings = {
            "TFT — طول المشفر": ("168 ساعة (7 أيام)", "عدد الساعات التاريخية التي يقرأها النموذج. 168 ساعة = أسبوع كامل من البيانات المتسلسلة."),
            "TFT — أفق التنبؤ": ("72 ساعة (3 أيام)", "عدد الساعات المستقبلية التي يتنبأ بها النموذج. يغطي 3 أيام مستقبلية."),
            "TFT — رؤوس Attention": ("4", "عدد رؤوس Attention في آلية Multi-Head Attention. كل رأس يركز على نمط زمني مختلف."),
            "XGBoost — عمق الشجرة": ("6", "عمق أقصى لكل شجرة قرار. قيمة أعلى = نموذج أعقد مع خطر Overfitting."),
            "XGBoost — عدد الأشجار": ("500", "عدد أشجار القرار المتتالية. كل شجرة تصحح أخطاء ما قبلها."),
            "XGBoost — معدل التعلم": ("0.05", "سرعة تعلم النموذج. قيمة أصغر = تعلم أبطأ لكن أدق."),
            "Ensemble — إستراتيجية الدمج": ("weighted_voting", "طريقة دمج توقعات النماذج: تصويت مرجح بأوزان ديناميكية محسنة بخوارزمية ZOA."),
            "أوزان Ensemble": ("time_series: 0.4 · sentiment: 0.3 · baseline: 0.3", "الأوزان الأولية للفروع الثلاثة. تتكيف تلقائياً حسب أداء كل فرع."),
        }

        for key, (value, tip) in model_settings.items():
            col1, col2 = st.columns([3, 4])
            with col1:
                st.markdown(f"""
                <strong style="color:#e2e8f0;">{key}</strong>
                {info_tip(tip)}
                """, unsafe_allow_html=True)
            with col2:
                st.markdown(f"<span style='color:#94a3b8;'>{value}</span>", unsafe_allow_html=True)
            st.markdown("<hr style='border-color:#1e293b; margin:5px 0;'>", unsafe_allow_html=True)

    with tab3:
        st.markdown(f"""
        <div class="section-header">
            <h2>إعدادات التنبيهات</h2>
            {info_tip("من ملف config/alerts.yaml: أنواع التنبيهات وحدودها وأوقات الإشعارات اليومية والأسبوعية.")}
        </div>
        """, unsafe_allow_html=True)

        alert_settings = {
            "حد التغير الحاد": ("5%", "نسبة التغير في السعر خلال ساعة التي تُطلق تنبيه عاجل."),
            "حد خطأ التنبؤ": ("3%", "نسبة خطأ التنبؤ التي تُطلق تنبيه تحذيري لإعادة فحص النموذج."),
            "حد تعطل المصدر": ("60 دقيقة", "المدة القصوى المسموحة دون استجابة من مصدر بيانات قبل إطلاق تنبيه."),
            "تقرير يومي": ("07:00 صباحاً", "ملخص يومي يُرسل عبر تلغرام يتضمن: آخر سعر + توقع 24 ساعة + أهم الأحداث."),
            "تقرير أسبوعي": ("الأحد 10:00 صباحاً", "تقرير شامل أسبوعي: أداء النماذج + ملخص الأحداث + إحصائيات المصادر."),
        }

        for key, (value, tip) in alert_settings.items():
            col1, col2 = st.columns([3, 4])
            with col1:
                st.markdown(f"""
                <strong style="color:#e2e8f0;">{key}</strong>
                {info_tip(tip)}
                """, unsafe_allow_html=True)
            with col2:
                st.markdown(f"<span style='color:#94a3b8;'>{value}</span>", unsafe_allow_html=True)
            st.markdown("<hr style='border-color:#1e293b; margin:5px 0;'>", unsafe_allow_html=True)
