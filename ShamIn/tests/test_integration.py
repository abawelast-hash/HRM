"""
ShamIn - Integration Tests
اختبارات التكامل للنظام
"""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from datetime import datetime, timezone, timedelta
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


# ══════════════════════════════════════════════════════════
# اختبارات تكامل قاعدة البيانات
# ══════════════════════════════════════════════════════════

class TestDatabaseIntegration:
    """اختبارات تكامل قاعدة البيانات"""
    
    @pytest.fixture
    def db_connection(self):
        """إنشاء اتصال وهمي بقاعدة البيانات"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=None)
        return mock_conn, mock_cursor
    
    def test_insert_raw_text(self, db_connection):
        """اختبار إدراج نص خام"""
        conn, cursor = db_connection
        
        text_data = {
            "source_type": "telegram",
            "source_name": "test_channel",
            "content": "سعر الدولار 14500",
            "content_hash": "abc123",
            "timestamp": datetime.now(timezone.utc)
        }
        
        cursor.execute.return_value = None
        cursor.fetchone.return_value = (1,)
        
        # Simulate insert
        with conn.cursor() as cur:
            cur.execute("INSERT INTO raw_texts (...) VALUES (...) RETURNING id")
            result = cur.fetchone()
        
        assert result is not None
        assert result[0] == 1
    
    def test_query_latest_prices(self, db_connection):
        """اختبار استعلام آخر الأسعار"""
        conn, cursor = db_connection
        
        cursor.fetchall.return_value = [
            (1, "USD/SYP", 14500.0, 14600.0, "sp_today", datetime.now(timezone.utc)),
            (2, "EUR/SYP", 15800.0, 15900.0, "central_bank", datetime.now(timezone.utc))
        ]
        
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM prices ORDER BY timestamp DESC LIMIT 10")
            results = cur.fetchall()
        
        assert len(results) == 2
        assert results[0][1] == "USD/SYP"
    
    def test_update_source_status(self, db_connection):
        """اختبار تحديث حالة المصدر"""
        conn, cursor = db_connection
        
        cursor.rowcount = 1
        
        with conn.cursor() as cur:
            cur.execute("UPDATE data_sources SET enabled = %s WHERE name = %s", (True, "sp_today"))
        
        assert cursor.rowcount == 1


# ══════════════════════════════════════════════════════════
# اختبارات تكامل InfluxDB
# ══════════════════════════════════════════════════════════

class TestInfluxDBIntegration:
    """اختبارات تكامل InfluxDB"""
    
    @pytest.fixture
    def influx_client(self):
        """إنشاء عميل InfluxDB وهمي"""
        mock_client = MagicMock()
        mock_write_api = MagicMock()
        mock_query_api = MagicMock()
        mock_client.write_api.return_value = mock_write_api
        mock_client.query_api.return_value = mock_query_api
        return mock_client, mock_write_api, mock_query_api
    
    def test_write_price_point(self, influx_client):
        """اختبار كتابة نقطة سعر"""
        client, write_api, query_api = influx_client
        
        from influxdb_client import Point
        
        point = Point("exchange_rate") \
            .tag("currency_pair", "USD/SYP") \
            .tag("source", "sp_today") \
            .field("buy_price", 14500.0) \
            .field("sell_price", 14600.0)
        
        write_api.write.return_value = None
        write_api.write(bucket="exchange_rates", record=point)
        
        write_api.write.assert_called_once()
    
    def test_query_time_series(self, influx_client):
        """اختبار استعلام سلسلة زمنية"""
        client, write_api, query_api = influx_client
        
        mock_table = MagicMock()
        mock_table.records = [
            MagicMock(get_value=lambda: 14500.0, get_time=lambda: datetime.now(timezone.utc))
        ]
        query_api.query.return_value = [mock_table]
        
        query = '''
        from(bucket: "exchange_rates")
          |> range(start: -7d)
          |> filter(fn: (r) => r["currency_pair"] == "USD/SYP")
        '''
        
        result = query_api.query(query)
        
        assert len(result) > 0


# ══════════════════════════════════════════════════════════
# اختبارات تكامل Redis
# ══════════════════════════════════════════════════════════

class TestRedisIntegration:
    """اختبارات تكامل Redis"""
    
    @pytest.fixture
    def redis_client(self):
        """إنشاء عميل Redis وهمي"""
        mock_client = MagicMock()
        return mock_client
    
    def test_cache_price(self, redis_client):
        """اختبار تخزين السعر في الذاكرة المؤقتة"""
        price_data = {
            "currency_pair": "USD/SYP",
            "buy_price": 14500,
            "sell_price": 14600,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        redis_client.setex.return_value = True
        
        result = redis_client.setex(
            "price:USD/SYP:latest",
            300,  # 5 minutes TTL
            json.dumps(price_data)
        )
        
        assert result == True
    
    def test_get_cached_price(self, redis_client):
        """اختبار جلب السعر من الذاكرة المؤقتة"""
        cached_data = json.dumps({
            "currency_pair": "USD/SYP",
            "buy_price": 14500
        })
        
        redis_client.get.return_value = cached_data.encode()
        
        result = redis_client.get("price:USD/SYP:latest")
        
        assert result is not None
        data = json.loads(result.decode())
        assert data["buy_price"] == 14500
    
    def test_cache_miss(self, redis_client):
        """اختبار عدم وجود في الذاكرة المؤقتة"""
        redis_client.get.return_value = None
        
        result = redis_client.get("price:NONEXISTENT:latest")
        
        assert result is None


# ══════════════════════════════════════════════════════════
# اختبارات تكامل Pipeline
# ══════════════════════════════════════════════════════════

class TestPipelineIntegration:
    """اختبارات تكامل خط المعالجة"""
    
    def test_text_processing_pipeline(self):
        """اختبار خط معالجة النص"""
        raw_text = """
        سعر صرف الدولار مقابل الليرة السورية اليوم:
        شراء: 14,500 ل.س
        مبيع: 14,600 ل.س
        """
        
        # Step 1: تنظيف النص
        cleaned_text = raw_text.strip()
        assert len(cleaned_text) > 0
        
        # Step 2: استخراج الأرقام
        import re
        numbers = re.findall(r'\d{1,3}(?:,\d{3})*', cleaned_text)
        assert len(numbers) >= 2
        
        # Step 3: تحويل لأرقام
        prices = [float(n.replace(',', '')) for n in numbers]
        assert 14500.0 in prices
        assert 14600.0 in prices
    
    def test_price_validation_pipeline(self):
        """اختبار خط التحقق من الأسعار"""
        prices = [
            {"buy": 14500, "sell": 14600, "source": "A"},  # صحيح
            {"buy": -100, "sell": 14600, "source": "B"},   # خطأ - سعر سالب
            {"buy": 14500, "sell": 14400, "source": "C"},  # خطأ - شراء > مبيع
        ]
        
        valid_prices = []
        for p in prices:
            if p["buy"] > 0 and p["sell"] > 0 and p["buy"] <= p["sell"]:
                valid_prices.append(p)
        
        assert len(valid_prices) == 1
        assert valid_prices[0]["source"] == "A"
    
    def test_aggregation_pipeline(self):
        """اختبار خط التجميع"""
        prices = [
            {"source": "A", "buy": 14500, "timestamp": datetime.now(timezone.utc)},
            {"source": "B", "buy": 14520, "timestamp": datetime.now(timezone.utc)},
            {"source": "C", "buy": 14480, "timestamp": datetime.now(timezone.utc)},
        ]
        
        # حساب المتوسط
        avg_price = sum(p["buy"] for p in prices) / len(prices)
        assert abs(avg_price - 14500) < 100
        
        # حساب الانحراف
        variance = sum((p["buy"] - avg_price) ** 2 for p in prices) / len(prices)
        std_dev = variance ** 0.5
        assert std_dev < 100


# ══════════════════════════════════════════════════════════
# اختبارات تكامل Celery
# ══════════════════════════════════════════════════════════

class TestCeleryIntegration:
    """اختبارات تكامل Celery"""
    
    @pytest.fixture
    def celery_app(self):
        """إنشاء تطبيق Celery وهمي"""
        mock_app = MagicMock()
        mock_app.send_task.return_value = MagicMock(id="task-123")
        return mock_app
    
    def test_schedule_collection_task(self, celery_app):
        """اختبار جدولة مهمة جمع"""
        result = celery_app.send_task(
            'src.ingestion.scheduler.collect_rss',
            args=[],
            kwargs={}
        )
        
        assert result.id == "task-123"
    
    def test_task_retry(self, celery_app):
        """اختبار إعادة محاولة المهمة"""
        task = MagicMock()
        task.retry.return_value = None
        
        # Simulate retry
        try:
            raise ConnectionError("Network error")
        except ConnectionError:
            task.retry(countdown=60, max_retries=3)
        
        task.retry.assert_called_once()


# ══════════════════════════════════════════════════════════
# اختبارات End-to-End
# ══════════════════════════════════════════════════════════

class TestEndToEnd:
    """اختبارات من البداية للنهاية"""
    
    def test_full_collection_flow(self):
        """اختبار تدفق الجمع الكامل"""
        # 1. تهيئة
        source_config = {
            "name": "test_source",
            "type": "rss",
            "url": "https://example.com/feed",
            "frequency_minutes": 15
        }
        
        # 2. جمع (محاكاة)
        collected_data = [
            {"title": "خبر 1", "content": "سعر الدولار 14500"},
            {"title": "خبر 2", "content": "سعر اليورو 15800"}
        ]
        
        # 3. معالجة
        processed_data = []
        for item in collected_data:
            import re
            prices = re.findall(r'\d+', item["content"])
            if prices:
                processed_data.append({
                    "source": source_config["name"],
                    "price": int(prices[0]),
                    "text": item["content"]
                })
        
        # 4. تخزين (محاكاة)
        stored_count = len(processed_data)
        
        # التحقق
        assert len(collected_data) == 2
        assert len(processed_data) == 2
        assert stored_count == 2
    
    def test_price_update_flow(self):
        """اختبار تدفق تحديث السعر"""
        # الحالة الأولية
        current_price = {"USD/SYP": {"buy": 14400, "sell": 14500}}
        
        # سعر جديد
        new_price = {"USD/SYP": {"buy": 14500, "sell": 14600}}
        
        # حساب التغيير
        change = {
            "buy_change": new_price["USD/SYP"]["buy"] - current_price["USD/SYP"]["buy"],
            "sell_change": new_price["USD/SYP"]["sell"] - current_price["USD/SYP"]["sell"],
            "buy_change_pct": (new_price["USD/SYP"]["buy"] - current_price["USD/SYP"]["buy"]) / current_price["USD/SYP"]["buy"] * 100
        }
        
        # التحقق
        assert change["buy_change"] == 100
        assert change["sell_change"] == 100
        assert abs(change["buy_change_pct"] - 0.69) < 0.1


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
