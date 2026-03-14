"""API endpoints for manual task execution and monitoring."""
from fastapi import APIRouter, HTTPException
from typing import Dict, List, Optional
import logging
from datetime import datetime

router = APIRouter(prefix="/tasks", tags=["Tasks"])
logger = logging.getLogger(__name__)


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
