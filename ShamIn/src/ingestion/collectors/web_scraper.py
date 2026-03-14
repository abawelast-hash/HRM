"""Web Scraper — جامع أسعار من المواقع الإلكترونية."""
import logging
import re
from typing import Dict, List, Optional
from datetime import datetime, timezone
import hashlib
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup
import time
import random

logger = logging.getLogger(__name__)


class WebScraper:
    """
    جامع أسعار صرف من مواقع إلكترونية.
    
    يدعم:
    - sp-today.com (الليرة اليوم)
    - investing.com/currencies/usd-syp
    - banquecentrale.gov.sy (البنك المركزي)
    """
    
    def __init__(self, storage_db=None):
        """
        Args:
            storage_db: اتصال TimeSeries DB (InfluxDB) لتخزين الأسعار
        """
        self.storage_db = storage_db
        self.session = self._create_session()
        
        # أنماط regex لاستخراج الأرقام
        self.number_pattern = re.compile(r'[\d,]+(?:\.\d+)?')
        
    def _create_session(self) -> requests.Session:
        """إنشاء جلسة HTTP مع User-Agent وإعادة محاولة."""
        session = requests.Session()
        retry = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"]
        )
        adapter = HTTPAdapter(max_retries=retry)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ar,en-US;q=0.9,en;q=0.8',
        })
        return session
    
    def _extract_numbers(self, text: str) -> List[float]:
        """استخراج جميع الأرقام من نص."""
        matches = self.number_pattern.findall(text)
        numbers = []
        for match in matches:
            try:
                # إزالة الفواصل وتحويل إلى float
                num = float(match.replace(',', ''))
                numbers.append(num)
            except ValueError:
                continue
        return numbers
    
    def scrape_sp_today(self) -> Optional[Dict]:
        """
        جمع سعر من sp-today.com (الليرة اليوم).
        
        Returns:
            Dict أو None: {
                'source': 'sp-today',
                'price': float,
                'timestamp': datetime,
                'location': str,
                'success': bool
            }
        """
        url = "https://sp-today.com/"
        logger.info(f"🌐 جمع سعر من sp-today.com")
        
        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # البحث عن div الأسعار - التركيب يعتمد على بنية الموقع
            # محاولة 1: البحث عن class="price" أو "rate"
            price_elem = soup.find(class_=re.compile(r'price|rate|value', re.I))
            
            if not price_elem:
                # محاولة 2: البحث في النص عن "الدولار" + رقم
                text = soup.get_text()
                # البحث عن نمط: "الدولار 14500" أو "USD 14,500"
                pattern = r'(?:الدولار|USD|دولار)[:\s]+?([\d,]+)'
                match = re.search(pattern, text, re.I)
                if match:
                    price_str = match.group(1).replace(',', '')
                    price = float(price_str)
                else:
                    # محاولة 3: أخذ أول رقم كبير في الصفحة (> 1000)
                    numbers = self._extract_numbers(text)
                    large_numbers = [n for n in numbers if 1000 < n < 100000]
                    if large_numbers:
                        price = large_numbers[0]
                    else:
                        logger.warning("⚠️ لم يتم العثور على سعر في sp-today.com")
                        return None
            else:
                price_text = price_elem.get_text()
                numbers = self._extract_numbers(price_text)
                if numbers:
                    price = numbers[0]
                else:
                    logger.warning("⚠️ لم يتم استخراج رقم من عنصر السعر")
                    return None
            
            result = {
                'source': 'sp-today',
                'price': price,
                'timestamp': datetime.now(timezone.utc),
                'location': 'دمشق',
                'success': True,
                'url': url
            }
            
            logger.info(f"✅ sp-today: {price:,.0f} ل.س")
            
            # تخزين في InfluxDB
            if self.storage_db:
                self._store_price(result)
            
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ خطأ في جمع من sp-today: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ خطأ غير متوقع في sp-today: {e}")
            return None
    
    def scrape_investing_com(self) -> Optional[Dict]:
        """
        جمع سعر من investing.com (USD/SYP).
        
        Returns:
            Dict أو None
        """
        url = "https://www.investing.com/currencies/usd-syp"
        logger.info(f"🌐 جمع سعر من investing.com")
        
        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # البحث عن السعر - investing.com عادة يستخدم data-test="instrument-price-last"
            price_elem = soup.find(attrs={'data-test': 'instrument-price-last'})
            
            if not price_elem:
                # محاولة بديلة: class="instrument-price"
                price_elem = soup.find(class_=re.compile(r'instrument-price', re.I))
            
            if not price_elem:
                logger.warning("⚠️ لم يتم العثور على عنصر السعر في investing.com")
                return None
            
            price_text = price_elem.get_text().strip()
            numbers = self._extract_numbers(price_text)
            
            if not numbers:
                logger.warning("⚠️ لم يتم استخراج رقم من investing.com")
                return None
            
            price = numbers[0]
            
            result = {
                'source': 'investing-com',
                'price': price,
                'timestamp': datetime.now(timezone.utc),
                'location': 'رسمي',
                'success': True,
                'url': url
            }
            
            logger.info(f"✅ investing.com: {price:,.0f} ل.س")
            
            # تخزين في InfluxDB
            if self.storage_db:
                self._store_price(result)
            
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ خطأ في جمع من investing.com: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ خطأ غير متوقع في investing.com: {e}")
            return None
    
    def scrape_central_bank(self) -> Optional[Dict]:
        """
        جمع السعر الرسمي من البنك المركزي السوري.
        
        Returns:
            Dict أو None
        """
        url = "http://www.banquecentrale.gov.sy/"
        logger.info(f"🌐 جمع سعر من البنك المركزي السوري")
        
        try:
            # البنك المركزي قد يكون بطيئاً
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # البحث عن جدول النشرة الرسمية
            text = soup.get_text()
            
            # البحث عن نمط "USD" أو "الدولار" + رقم
            pattern = r'(?:USD|دولار|الدولار)[:\s]+?([\d,]+(?:\.\d+)?)'
            matches = re.findall(pattern, text, re.I)
            
            if matches:
                price_str = matches[0].replace(',', '')
                price = float(price_str)
            else:
                # محاولة أخذ أول رقم معقول
                numbers = self._extract_numbers(text)
                reasonable = [n for n in numbers if 100 < n < 100000]
                if reasonable:
                    price = reasonable[0]
                else:
                    logger.warning("⚠️ لم يتم العثور على سعر في موقع البنك المركزي")
                    return None
            
            result = {
                'source': 'central-bank-sy',
                'price': price,
                'timestamp': datetime.now(timezone.utc),
                'location': 'رسمي',
                'success': True,
                'url': url
            }
            
            logger.info(f"✅ البنك المركزي: {price:,.2f} ل.س")
            
            # تخزين في InfluxDB
            if self.storage_db:
                self._store_price(result)
            
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ خطأ في جمع من البنك المركزي: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ خطأ غير متوقع في البنك المركزي: {e}")
            return None
    
    def collect_all(self, delay: tuple = (3, 7)) -> List[Dict]:
        """
        جمع أسعار من جميع المواقع المدعومة.
        
        Args:
            delay: (min, max) ثواني تأخير بين الطلبات
        
        Returns:
            List[Dict]: قائمة النتائج
        """
        scrapers = [
            self.scrape_sp_today,
            self.scrape_investing_com,
            self.scrape_central_bank,
        ]
        
        results = []
        
        for scraper_func in scrapers:
            result = scraper_func()
            if result:
                results.append(result)
            
            # تأخير عشوائي
            if scraper_func != scrapers[-1]:
                sleep_time = random.uniform(*delay)
                logger.debug(f"⏳ انتظار {sleep_time:.1f} ثانية...")
                time.sleep(sleep_time)
        
        # إحصائيات
        successful = len(results)
        logger.info(f"📊 تم جمع {successful}/3 أسعار بنجاح")
        
        return results
    
    def _store_price(self, price_data: Dict):
        """تخزين سعر في InfluxDB."""
        if not self.storage_db:
            return
        
        try:
            from src.storage.timeseries_db import TimeSeriesDB
            
            tsdb = TimeSeriesDB()
            tsdb.write_price(
                measurement="exchange_rates",
                price=price_data['price'],
                source=price_data['source'],
                location=price_data.get('location', 'unknown'),
                timestamp=price_data['timestamp']
            )
            tsdb.close()
            
        except Exception as e:
            logger.error(f"خطأ في تخزين السعر من {price_data['source']}: {e}")
    
    def close(self):
        """إغلاق الجلسة."""
        self.session.close()
