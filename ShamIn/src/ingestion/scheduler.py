"""Celery scheduler for data collection tasks."""
from celery import Celery
from celery.schedules import crontab
import os

app = Celery(
    'shamin',
    broker=os.getenv('REDIS_URL', 'redis://localhost:6379/0'),
    backend=os.getenv('REDIS_URL', 'redis://localhost:6379/0'),
)

app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)

# Beat schedule
app.conf.beat_schedule = {
    'collect-rss-every-15min': {
        'task': 'src.ingestion.scheduler.collect_rss',
        'schedule': 900.0,  # 15 minutes
    },
    'collect-telegram-prices-every-5min': {
        'task': 'src.ingestion.scheduler.collect_telegram_prices',
        'schedule': 300.0,  # 5 minutes
    },
    'collect-telegram-news-every-5min': {
        'task': 'src.ingestion.scheduler.collect_telegram_news',
        'schedule': 300.0,
    },
    'collect-web-prices-every-5min': {
        'task': 'src.ingestion.scheduler.collect_web_prices',
        'schedule': 300.0,
    },
    'collect-external-indicators-hourly': {
        'task': 'src.ingestion.scheduler.collect_external_indicators',
        'schedule': 3600.0,  # 1 hour
    },
}


@app.task(bind=True, max_retries=3, default_retry_delay=60)
def collect_rss(self):
    """Collect from all RSS sources."""
    import logging
    import yaml
    from src.ingestion.collectors.rss_collector import RSSCollector
    
    logger = logging.getLogger(__name__)
    logger.info("📰 Starting RSS collection task...")
    
    try:
        # Load sources configuration
        with open('config/sources.yaml', 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        rss_sources = config.get('rss_sources', [])
        feeds_list = []
        
        # Support both list and dict formats
        if isinstance(rss_sources, list):
            # List format (current)
            for source in rss_sources:
                if source.get('active', True):
                    feeds_list.append({
                        'name': source['name'],
                        'url': source['url'],
                        'category': source.get('category', 'general'),
                        'language': source.get('language', 'ar')
                    })
        else:
            # Dict format (for future compatibility)
            for name, details in rss_sources.items():
                if details.get('enabled', True):
                    feeds_list.append({
                        'name': name,
                        'url': details['url'],
                        'category': details.get('category', 'general'),
                        'language': details.get('language', 'ar')
                    })
        
        if not feeds_list:
            logger.warning("⚠️ No RSS sources configured")
            return {'status': 'no_sources', 'count': 0}
        
        # Collect from all sources
        collector = RSSCollector(storage_db=True)
        results = collector.collect_all(feeds_list, delay=(2, 5))
        collector.close()
        
        # Calculate statistics
        total_articles = sum(r['articles_count'] for r in results)
        successful = sum(1 for r in results if r['success'])
        
        logger.info(f"✅ RSS collection completed: {total_articles} articles from {successful}/{len(results)} sources")
        
        return {
            'status': 'success',
            'sources_total': len(results),
            'sources_successful': successful,
            'articles_collected': total_articles,
            'details': [{'source': r['source'], 'count': r['articles_count'], 'success': r['success']} for r in results]
        }
        
    except Exception as e:
        logger.error(f"❌ Error in RSS collection task: {e}", exc_info=True)
        raise self.retry(exc=e)


@app.task(bind=True, max_retries=3, default_retry_delay=120)
def collect_telegram_prices(self):
    """Collect from Telegram price channels."""
    return {'status': 'pending_setup', 'message': 'Configure Telegram credentials first'}


@app.task(bind=True, max_retries=3, default_retry_delay=120)
def collect_telegram_news(self):
    """Collect from Telegram news channels."""
    return {'status': 'pending_setup', 'message': 'Configure Telegram credentials first'}


@app.task(bind=True, max_retries=3, default_retry_delay=60)
def collect_web_prices(self):
    """Scrape exchange rates from websites."""
    import logging
    from src.ingestion.collectors.web_scraper import WebScraper
    
    logger = logging.getLogger(__name__)
    logger.info("💰 Starting web prices collection task...")
    
    try:
        # Create scraper with InfluxDB storage
        scraper = WebScraper(storage_db=True)
        
        # Collect from all supported websites
        results = scraper.collect_all(delay=(3, 7))
        scraper.close()
        
        # Calculate statistics
        successful = len([r for r in results if r.get('success', False)])
        total = len(results)
        
        logger.info(f"✅ Web prices collection completed: {successful}/{total} sources successful")
        
        return {
            'status': 'success',
            'sources_total': total,
            'sources_successful': successful,
            'prices_collected': successful,
            'details': [{'source': r['source'], 'price': r.get('price'), 'success': r.get('success')} for r in results]
        }
        
    except Exception as e:
        logger.error(f"❌ Error in web prices collection task: {e}", exc_info=True)
        raise self.retry(exc=e)


@app.task(bind=True, max_retries=3, default_retry_delay=300)
def collect_external_indicators(self):
    """Collect external economic indicators."""
    import asyncio
    from src.utils.config import get_sources
    from src.ingestion.collectors.api_collector import APICollector

    sources = get_sources()
    results = []

    async def _run():
        for src_cfg in sources.get('external_apis', []):
            if not src_cfg.get('active', True):
                continue
            collector = APICollector(
                src_cfg['name'],
                src_cfg.get('metric', src_cfg['name']),
                src_cfg.get('endpoint', src_cfg.get('url', '')),
            )
            try:
                items = await collector.collect_with_retry()
                results.append({'source': src_cfg['name'], 'count': len(items)})
            except Exception as e:
                results.append({'source': src_cfg['name'], 'error': str(e)})

    asyncio.run(_run())
    return results
