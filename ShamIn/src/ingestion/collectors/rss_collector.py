"""RSS Feed Collector — جامع خلاصات RSS بميزات متقدمة."""
import feedparser
import logging
from typing import Dict, List, Optional
from datetime import datetime, timezone
import hashlib
import time
import random
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import asyncio

logger = logging.getLogger(__name__)


class RSSCollector:
    """جامع خلاصات RSS مع إعادة محاولة وتخزين مباشر."""
    
    def __init__(self, storage_db=None):
        """
        Args:
            storage_db: اتصال PostgreSQL لتخزين البيانات مباشرة
        """
        self.storage_db = storage_db
        self.session = self._create_session()
        
    def _create_session(self) -> requests.Session:
        """إنشاء جلسة HTTP مع إعادة محاولة تلقائية."""
        session = requests.Session()
        retry = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST"]
        )
        adapter = HTTPAdapter(max_retries=retry)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        return session
    
    def _generate_id(self, entry: Dict) -> str:
        """توليد معرف فريد للمقالة بناءً على الرابط."""
        link = entry.get('link', '')
        return hashlib.md5(link.encode('utf-8')).hexdigest()
    
    def _parse_published_date(self, entry: Dict) -> Optional[datetime]:
        """استخراج تاريخ النشر من المقالة."""
        # محاولة published أو updated
        for date_field in ['published_parsed', 'updated_parsed']:
            if date_field in entry and entry[date_field]:
                try:
                    return datetime(*entry[date_field][:6], tzinfo=timezone.utc)
                except:
                    pass
        
        # محاولة published أو updated كنص
        for date_field in ['published', 'updated']:
            if date_field in entry and entry[date_field]:
                try:
                    from dateutil import parser
                    return parser.parse(entry[date_field])
                except:
                    pass
        
        # إذا فشل كل شيء، استخدم الوقت الحالي
        return datetime.now(timezone.utc)
    
    def collect_feed(self, feed_config: Dict) -> Dict:
        """
        جمع مقالات من خلاصة RSS واحدة.
        
        Args:
            feed_config: {
                'name': 'اسم المصدر',
                'url': 'رابط RSS',
                'category': 'التصنيف',
                'language': 'ar'
            }
        
        Returns:
            Dict: {
                'source': str,
                'success': bool,
                'articles_count': int,
                'articles': List[Dict],
                'error': Optional[str]
            }
        """
        source_name = feed_config.get('name', 'unknown')
        feed_url = feed_config.get('url', '')
        category = feed_config.get('category', 'general')
        
        logger.info(f"📰 جمع RSS من {source_name}: {feed_url}")
        
        result = {
            'source': source_name,
            'success': False,
            'articles_count': 0,
            'articles': [],
            'error': None
        }
        
        try:
            # جلب RSS مع timeout
            response = self.session.get(feed_url, timeout=30)
            response.raise_for_status()
            
            # تحليل RSS
            feed = feedparser.parse(response.content)
            
            if feed.get('bozo', 0) == 1:
                # خطأ في التحليل
                error = str(feed.get('bozo_exception', 'Unknown parsing error'))
                logger.warning(f"⚠️ خطأ في تحليل RSS من {source_name}: {error}")
                result['error'] = f"Parse error: {error}"
                return result
            
            # استخراج المقالات
            articles = []
            for entry in feed.entries:
                try:
                    article = {
                        'id': self._generate_id(entry),
                        'source': source_name,
                        'category': category,
                        'title': entry.get('title', '').strip(),
                        'content': entry.get('summary', entry.get('description', '')).strip(),
                        'link': entry.get('link', ''),
                        'published_at': self._parse_published_date(entry),
                        'collected_at': datetime.now(timezone.utc),
                        'language': feed_config.get('language', 'ar'),
                        'raw_data': {
                            'author': entry.get('author', ''),
                            'tags': [tag.get('term', '') for tag in entry.get('tags', [])],
                        }
                    }
                    
                    # التحقق من وجود محتوى
                    if article['title'] or article['content']:
                        articles.append(article)
                        
                        # تخزين مباشر في قاعدة البيانات
                        if self.storage_db:
                            self._store_article(article)
                    
                except Exception as e:
                    logger.error(f"خطأ في معالجة مقالة من {source_name}: {e}")
                    continue
            
            result['success'] = True
            result['articles_count'] = len(articles)
            result['articles'] = articles
            
            logger.info(f"✅ تم جمع {len(articles)} مقالة من {source_name}")
            
        except requests.exceptions.Timeout:
            error = "Timeout: انتهت مهلة الاتصال"
            logger.error(f"❌ {source_name}: {error}")
            result['error'] = error
            
        except requests.exceptions.RequestException as e:
            error = f"Request error: {str(e)}"
            logger.error(f"❌ {source_name}: {error}")
            result['error'] = error
            
        except Exception as e:
            error = f"Unexpected error: {str(e)}"
            logger.error(f"❌ {source_name}: {error}")
            result['error'] = error
        
        return result
    
    def collect_all(self, feeds: List[Dict], delay: tuple = (2, 5)) -> List[Dict]:
        """
        جمع مقالات من جميع الخلاصات بتأخير عشوائي.
        
        Args:
            feeds: قائمة إعدادات الخلاصات
            delay: (min_seconds, max_seconds) تأخير عشوائي بين الطلبات
        
        Returns:
            List[Dict]: نتائج الجمع لكل خلاصة
        """
        results = []
        
        for i, feed in enumerate(feeds):
            result = self.collect_feed(feed)
            results.append(result)
            
            # تأخير عشوائي لتجنب الحظر (إلا في الخلاصة الأخيرة)
            if i < len(feeds) - 1:
                sleep_time = random.uniform(*delay)
                logger.debug(f"⏳ انتظار {sleep_time:.1f} ثانية...")
                time.sleep(sleep_time)
        
        # إحصائيات إجمالية
        total_articles = sum(r['articles_count'] for r in results)
        successful = sum(1 for r in results if r['success'])
        failed = len(results) - successful
        
        logger.info(f"📊 الإحصائيات: {successful}/{len(results)} نجح | "
                   f"{total_articles} مقالة إجمالاً | {failed} فشل")
        
        return results
    
    def _store_article(self, article: Dict):
        """تخزين مقالة في PostgreSQL."""
        if not self.storage_db:
            return
        
        try:
            import psycopg2
            import os
            import json
            
            conn = psycopg2.connect(
                host=os.getenv("POSTGRES_HOST", "postgres"),
                port=os.getenv("POSTGRES_PORT", "5432"),
                database=os.getenv("POSTGRES_DB", "shamin_db"),
                user=os.getenv("POSTGRES_USER", "shamin_user"),
                password=os.getenv("POSTGRES_PASSWORD", "")
            )
            cur = conn.cursor()
            
            # إدخال في جدول raw_texts
            cur.execute("""
                INSERT INTO raw_texts (
                    source_type, title, content, url, metadata, created_at
                )
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT DO NOTHING
            """, (
                'rss',
                article['title'],
                article['content'],
                article['link'],
                json.dumps({
                    'source': article['source'],
                    'language': article['language'],
                    'published_at': str(article['published_at']) if article['published_at'] else None,
                    'raw_data': article['raw_data']
                }),
                article['collected_at']
            ))
            
            conn.commit()
            cur.close()
            conn.close()
            
        except Exception as e:
            logger.error(f"خطأ في تخزين المقالة: {e}")
    
    def close(self):
        """إغلاق الجلسة."""
        self.session.close()
