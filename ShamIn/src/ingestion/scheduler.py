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
    import asyncio
    from src.utils.config import get_sources
    from src.ingestion.collectors.rss_collector import RSSCollector

    sources = get_sources()
    results = []

    async def _run():
        for src_cfg in sources.get('rss_sources', []):
            if not src_cfg.get('active', True):
                continue
            collector = RSSCollector(src_cfg['name'], src_cfg['url'])
            items = await collector.collect_with_retry()
            results.append({'source': src_cfg['name'], 'count': len(items)})

    asyncio.run(_run())
    return results


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
    import asyncio
    from src.utils.config import get_sources
    from src.ingestion.collectors.web_scraper import WebScraper

    sources = get_sources()
    results = []

    async def _run():
        for src_cfg in sources.get('price_sources', []):
            if not src_cfg.get('active', True):
                continue
            parser_config = src_cfg.get('parser_config', {})
            scraper = WebScraper(src_cfg['name'], src_cfg['url'], parser_config)
            items = await scraper.collect_with_retry()
            results.append({'source': src_cfg['name'], 'count': len(items)})

    asyncio.run(_run())
    return results


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
