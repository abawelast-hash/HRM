"""API endpoints for manual task execution and monitoring."""
from fastapi import APIRouter, HTTPException
from typing import Dict, List, Optional
import logging
from datetime import datetime
import os
import psycopg2
from psycopg2.extras import RealDictCursor

router = APIRouter(prefix="/tasks", tags=["Tasks"])
logger = logging.getLogger(__name__)


def get_db_connection():
    """Get PostgreSQL connection."""
    return psycopg2.connect(
        host=os.getenv('POSTGRES_HOST', 'postgres'),
        port=os.getenv('POSTGRES_PORT', '5432'),
        dbname=os.getenv('POSTGRES_DB', 'shamin_db'),
        user=os.getenv('POSTGRES_USER', 'shamin_user'),
        password=os.getenv('POSTGRES_PASSWORD', 'password')
    )


@router.post("/collect/rss")
async def trigger_rss_collection() -> Dict:
    """
    تشغيل جمع RSS يدوياً.
    
    Returns:
        Dict: نتائج الجمع والإحصائيات
    """
    try:
        from src.ingestion.scheduler import collect_rss
        
        # تشغيل المهمة فوراً (بدون Celery delay)
        result = collect_rss()
        
        return {
            "status": "success",
            "task": "rss_collection",
            "timestamp": datetime.utcnow().isoformat(),
            "result": result
        }
    except Exception as e:
        logger.error(f"Error triggering RSS collection: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/collect/web-prices")
async def trigger_web_prices_collection() -> Dict:
    """
    تشغيل جمع أسعار المواقع يدوياً.
    
    Returns:
        Dict: نتائج الجمع والإحصائيات
    """
    try:
        from src.ingestion.scheduler import collect_web_prices
        
        result = collect_web_prices()
        
        return {
            "status": "success",
            "task": "web_prices_collection",
            "timestamp": datetime.utcnow().isoformat(),
            "result": result
        }
    except Exception as e:
        logger.error(f"Error triggering web prices collection: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/collect/telegram-prices")
async def trigger_telegram_prices_collection() -> Dict:
    """
    تشغيل جمع أسعار تلغرام يدوياً.
    
    Returns:
        Dict: نتائج الجمع
    """
    try:
        from src.ingestion.scheduler import collect_telegram_prices
        
        result = collect_telegram_prices()
        
        return {
            "status": "success",
            "task": "telegram_prices_collection",
            "timestamp": datetime.utcnow().isoformat(),
            "result": result
        }
    except Exception as e:
        logger.error(f"Error triggering telegram prices collection: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/collect/telegram-news")
async def trigger_telegram_news_collection() -> Dict:
    """
    تشغيل جمع أخبار تلغرام يدوياً.
    
    Returns:
        Dict: نتائج الجمع
    """
    try:
        from src.ingestion.scheduler import collect_telegram_news
        
        result = collect_telegram_news()
        
        return {
            "status": "success",
            "task": "telegram_news_collection",
            "timestamp": datetime.utcnow().isoformat(),
            "result": result
        }
    except Exception as e:
        logger.error(f"Error triggering telegram news collection: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/collect/external-indicators")
async def trigger_external_indicators_collection() -> Dict:
    """
    تشغيل جمع المؤشرات الخارجية يدوياً.
    
    Returns:
        Dict: نتائج الجمع
    """
    try:
        from src.ingestion.scheduler import collect_external_indicators
        
        result = collect_external_indicators()
        
        return {
            "status": "success",
            "task": "external_indicators_collection",
            "timestamp": datetime.utcnow().isoformat(),
            "result": result
        }
    except Exception as e:
        logger.error(f"Error triggering external indicators collection: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/collect/all")
async def trigger_all_collections() -> Dict:
    """
    تشغيل جميع محركات الجمع معاً.
    
    Returns:
        Dict: نتائج جميع المهام
    """
    try:
        from src.ingestion.scheduler import (
            collect_rss,
            collect_web_prices,
            collect_telegram_prices,
            collect_telegram_news,
            collect_external_indicators
        )
        
        results = {
            "rss": collect_rss(),
            "web_prices": collect_web_prices(),
            "telegram_prices": collect_telegram_prices(),
            "telegram_news": collect_telegram_news(),
            "external_indicators": collect_external_indicators()
        }
        
        return {
            "status": "success",
            "task": "all_collections",
            "timestamp": datetime.utcnow().isoformat(),
            "results": results
        }
    except Exception as e:
        logger.error(f"Error triggering all collections: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats/recent")
async def get_recent_stats() -> Dict:
    """
    إحصائيات الجمع الأخيرة.
    
    Returns:
        Dict: إحصائيات من قاعدة البيانات
    """
    try:
        from src.storage.relational_db import RelationalDB
        
        db = RelationalDB()
        
        # عدد المقالات المجموعة في آخر ساعة
        rss_count = db.execute_query("""
            SELECT COUNT(*) as count 
            FROM raw_news_text 
            WHERE collected_at > NOW() - INTERVAL '1 hour'
        """)
        
        # عدد الأسعار المجموعة في آخر ساعة
        # (سيتطلب استعلام InfluxDB - placeholder حالياً)
        
        db.close()
        
        return {
            "status": "success",
            "timestamp": datetime.utcnow().isoformat(),
            "stats": {
                "rss_articles_last_hour": rss_count[0]['count'] if rss_count else 0,
                "web_prices_last_hour": 0,  # TODO: query InfluxDB
                "telegram_messages_last_hour": 0
            }
        }
    except Exception as e:
        logger.error(f"Error fetching stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/logs/recent")
async def get_recent_logs(limit: int = 50) -> Dict:
    """
    جلب آخر سجلات التشغيل.
    
    Args:
        limit: عدد السجلات
        
    Returns:
        Dict: قائمة السجلات
    """
    try:
        import os
        
        log_file = "logs/ingestion.log"
        
        if not os.path.exists(log_file):
            return {"status": "success", "logs": [], "message": "No log file found"}
        
        # قراءة آخر N سطر من ملف السجل
        with open(log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            recent_lines = lines[-limit:] if len(lines) > limit else lines
        
        return {
            "status": "success",
            "timestamp": datetime.utcnow().isoformat(),
            "logs": [line.strip() for line in recent_lines],
            "count": len(recent_lines)
        }
    except Exception as e:
        logger.error(f"Error fetching logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ===== DATA ACCESS ENDPOINTS =====

@router.get("/data/raw-texts")
async def get_raw_texts(
    source_type: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
) -> Dict:
    """
    جلب النصوص المجمعة من قاعدة البيانات.
    
    Args:
        source_type: نوع المصدر (rss, telegram, web) - اختياري
        limit: عدد السجلات (الحد الأقصى 500)
        offset: إزاحة البداية
        
    Returns:
        Dict: قائمة النصوص مع البيانات الوصفية
    """
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        limit = min(limit, 500)
        
        # بناء الاستعلام
        if source_type:
            query = "SELECT * FROM raw_texts WHERE source_type = %s ORDER BY created_at DESC LIMIT %s OFFSET %s"
            cur.execute(query, (source_type, limit, offset))
        else:
            query = "SELECT * FROM raw_texts ORDER BY created_at DESC LIMIT %s OFFSET %s"
            cur.execute(query, (limit, offset))
        
        rows = [dict(row) for row in cur.fetchall()]
        
        # Convert datetime to string for JSON serialization
        for row in rows:
            for key, value in row.items():
                if isinstance(value, datetime):
                    row[key] = value.isoformat()
        
        # عدد السجلات الإجمالي
        if source_type:
            cur.execute("SELECT COUNT(*) as total FROM raw_texts WHERE source_type = %s", (source_type,))
        else:
            cur.execute("SELECT COUNT(*) as total FROM raw_texts")
        total = cur.fetchone()['total']
        
        cur.close()
        conn.close()
        
        return {
            "status": "success",
            "timestamp": datetime.utcnow().isoformat(),
            "data": rows,
            "pagination": {
                "total": total,
                "limit": limit,
                "offset": offset,
                "has_more": offset + limit < total
            }
        }
    except Exception as e:
        if conn:
            conn.close()
        logger.error(f"Error fetching raw texts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/data/raw-texts/{text_id}")
async def get_raw_text_by_id(text_id: int) -> Dict:
    """
    جلب نص محدد بالمعرف.
    
    Args:
        text_id: معرف النص
        
    Returns:
        Dict: بيانات النص الكاملة
    """
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT * FROM raw_texts WHERE id = %s", (text_id,))
        row = cur.fetchone()
        cur.close()
        conn.close()
        
        if not row:
            raise HTTPException(status_code=404, detail="Text not found")
        
        data = dict(row)
        for key, value in data.items():
            if isinstance(value, datetime):
                data[key] = value.isoformat()
        
        return {
            "status": "success",
            "timestamp": datetime.utcnow().isoformat(),
            "data": data
        }
    except HTTPException:
        raise
    except Exception as e:
        if conn:
            conn.close()
        logger.error(f"Error fetching raw text {text_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/data/search")
async def search_raw_texts(
    q: str,
    limit: int = 50
) -> Dict:
    """
    البحث في النصوص المجمعة.
    
    Args:
        q: نص البحث
        limit: عدد النتائج (الحد الأقصى 100)
        
    Returns:
        Dict: نتائج البحث
    """
    conn = None
    try:
        if len(q) < 2:
            raise HTTPException(status_code=400, detail="Search query too short")
        
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        limit = min(limit, 100)
        
        # البحث في المحتوى والعنوان
        query = """
            SELECT * FROM raw_texts 
            WHERE content ILIKE %s OR title ILIKE %s
            ORDER BY created_at DESC 
            LIMIT %s
        """
        search_pattern = f"%{q}%"
        cur.execute(query, (search_pattern, search_pattern, limit))
        rows = [dict(row) for row in cur.fetchall()]
        
        for row in rows:
            for key, value in row.items():
                if isinstance(value, datetime):
                    row[key] = value.isoformat()
        
        cur.close()
        conn.close()
        
        return {
            "status": "success",
            "timestamp": datetime.utcnow().isoformat(),
            "query": q,
            "data": rows,
            "count": len(rows)
        }
    except HTTPException:
        raise
    except Exception as e:
        if conn:
            conn.close()
        logger.error(f"Error searching raw texts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/data/stats")
async def get_data_stats() -> Dict:
    """
    إحصائيات البيانات المجمعة.
    
    Returns:
        Dict: إحصائيات شاملة
    """
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # إجمالي النصوص
        cur.execute("SELECT COUNT(*) as total FROM raw_texts")
        total = cur.fetchone()['total']
        
        # توزيع حسب المصدر
        cur.execute("""
            SELECT source_type, COUNT(*) as count 
            FROM raw_texts 
            GROUP BY source_type
        """)
        by_source = [dict(row) for row in cur.fetchall()]
        
        # توزيع حسب اليوم (آخر 7 أيام)
        cur.execute("""
            SELECT DATE(created_at) as date, COUNT(*) as count 
            FROM raw_texts 
            WHERE created_at > NOW() - INTERVAL '7 days'
            GROUP BY DATE(created_at)
            ORDER BY date DESC
        """)
        by_day_raw = cur.fetchall()
        by_day = []
        for row in by_day_raw:
            by_day.append({
                'date': row['date'].isoformat() if row['date'] else None,
                'count': row['count']
            })
        
        # آخر عملية جمع
        cur.execute("SELECT MAX(created_at) as last FROM raw_texts")
        last_result = cur.fetchone()
        last_collected = last_result['last'] if last_result and last_result['last'] else None
        
        cur.close()
        conn.close()
        
        return {
            "status": "success",
            "timestamp": datetime.utcnow().isoformat(),
            "stats": {
                "total_texts": total,
                "by_source": by_source,
                "by_day": by_day,
                "last_collected": last_collected.isoformat() if last_collected else None
            }
        }
    except Exception as e:
        if conn:
            conn.close()
        logger.error(f"Error fetching data stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))
