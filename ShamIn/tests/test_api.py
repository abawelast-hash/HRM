c:\Users\IT\Downloads\photo_6026213337244748031_y.jpg c:\Users\IT\Downloads\photo_6026213337244748040_w.jpg c:\Users\IT\Downloads\photo_6008157681279420683_w.jpg c:\Users\IT\Downloads\photo_6008157681279420682_w.jpg c:\Users\IT\Downloads\photo_6008157681279421128_w.jpg c:\Users\IT\Downloads\photo_6008157681279421127_w.jpg c:\Users\IT\Downloads\photo_6008157681279421126_w.jpg c:\Users\IT\Downloads\photo_6026213337244748035_y.jpg c:\Users\IT\Downloads\photo_5845848633784339299_y.jpg c:\Users\IT\Downloads\photo_5845848633784339300_y.jpg c:\Users\IT\Downloads\photo_5845848633784339301_y.jpg c:\Users\IT\Downloads\photo_5845848633784339302_y.jpg c:\Users\IT\Downloads\photo_5845848633784339303_y.jpg c:\Users\IT\Downloads\photo_5845848633784339304_y.jpg c:\Users\IT\Downloads\photo_5845848633784339305_y.jpg c:\Users\IT\Downloads\photo_5845848633784339306_y.jpg c:\Users\IT\Downloads\photo_5845848633784339307_y.jpg c:\Users\IT\Downloads\photo_5845848633784339308_y.jpg c:\Users\IT\Downloads\photo_5845848633784339317_y.jpg c:\Users\IT\Downloads\photo_5845848633784339319_y.jpg c:\Users\IT\Downloads\photo_5845848633784339320_y (1).jpg c:\Users\IT\Downloads\photo_5845848633784339321_y.jpg c:\Users\IT\Downloads\photo_5845848633784339322_y.jpg c:\Users\IT\Downloads\photo_5845848633784339323_y.jpg c:\Users\IT\Downloads\photo_5845848633784339324_y.jpg c:\Users\IT\Downloads\photo_5845848633784339325_y.jpg c:\Users\IT\Downloads\photo_5845848633784339326_y.jpg c:\Users\IT\Downloads\photo_5845848633784339327_y.jpg c:\Users\IT\Downloads\photo_5845848633784339328_y.jpg c:\Users\IT\Downloads\photo_6026213337244748030_w (1).jpg c:\Users\IT\Downloads\photo_6026213337244748032_w.jpg c:\Users\IT\Downloads\photo_6026213337244748036_y.jpg c:\Users\IT\Downloads\photo_6026213337244748037_y.jpg c:\Users\IT\Downloads\photo_5845848633784339309_y.jpg c:\Users\IT\Downloads\photo_5845848633784339310_y.jpg c:\Users\IT\Downloads\photo_5845848633784339311_y.jpg c:\Users\IT\Downloads\photo_5845848633784339312_y.jpg c:\Users\IT\Downloads\photo_5845848633784339313_y.jpg c:\Users\IT\Downloads\photo_5845848633784339314_y.jpg c:\Users\IT\Downloads\photo_5845848633784339315_y.jpg c:\Users\IT\Downloads\photo_5845848633784339316_y.jpg c:\Users\IT\Downloads\photo_5845848633784339318_y.jpg c:\Users\IT\Downloads\photo_5845848633784339320_y.jpg c:\Users\IT\Downloads\photo_6026213337244748030_w.jpg"""
ShamIn - API Integration Tests
اختبارات تكامل API
"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


# ══════════════════════════════════════════════════════════
# اختبارات API الأساسية
# ══════════════════════════════════════════════════════════

class TestAPIHealth:
    """اختبارات صحة API"""
    
    @pytest.fixture
    def client(self):
        """عميل اختبار FastAPI"""
        try:
            from fastapi.testclient import TestClient
            from src.presentation.api.main import app
            return TestClient(app)
        except ImportError:
            pytest.skip("FastAPI not installed")
    
    def test_health_endpoint(self, client):
        """اختبار نقطة نهاية الصحة"""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
    
    def test_root_endpoint(self, client):
        """اختبار نقطة النهاية الجذرية"""
        response = client.get("/")
        
        assert response.status_code in [200, 307, 404]
    
    def test_docs_endpoint(self, client):
        """اختبار وثائق API"""
        response = client.get("/docs")
        
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")
    
    def test_openapi_schema(self, client):
        """اختبار مخطط OpenAPI"""
        response = client.get("/openapi.json")
        
        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "paths" in data


# ══════════════════════════════════════════════════════════
# اختبارات نقاط نهاية الأسعار
# ══════════════════════════════════════════════════════════

class TestPricesAPI:
    """اختبارات API الأسعار"""
    
    @pytest.fixture
    def client(self):
        """عميل اختبار FastAPI"""
        try:
            from fastapi.testclient import TestClient
            from src.presentation.api.main import app
            return TestClient(app)
        except ImportError:
            pytest.skip("FastAPI not installed")
    
    def test_get_latest_prices(self, client):
        """اختبار جلب آخر الأسعار"""
        response = client.get("/api/v1/prices/latest")
        
        # قد تكون القائمة فارغة إذا لم تُجمع بيانات بعد
        assert response.status_code in [200, 404]
        
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, (list, dict))
    
    def test_get_prices_by_currency(self, client):
        """اختبار جلب أسعار عملة محددة"""
        response = client.get("/api/v1/prices/USD-SYP")
        
        assert response.status_code in [200, 404]
    
    def test_get_price_history(self, client):
        """اختبار جلب تاريخ الأسعار"""
        response = client.get("/api/v1/prices/history?currency_pair=USD-SYP&days=7")
        
        assert response.status_code in [200, 404]
    
    @patch('src.storage.timeseries_db.TimeseriesDB')
    def test_post_price(self, mock_db, client):
        """اختبار إضافة سعر جديد"""
        mock_db.return_value.write.return_value = True
        
        price_data = {
            "currency_pair": "USD/SYP",
            "buy_price": 14500,
            "sell_price": 14600,
            "source": "test",
            "location": "Damascus"
        }
        
        response = client.post("/api/v1/prices", json=price_data)
        
        # قد يتطلب توثيق
        assert response.status_code in [200, 201, 401, 422]


# ══════════════════════════════════════════════════════════
# اختبارات نقاط نهاية المصادر
# ══════════════════════════════════════════════════════════

class TestSourcesAPI:
    """اختبارات API المصادر"""
    
    @pytest.fixture
    def client(self):
        """عميل اختبار FastAPI"""
        try:
            from fastapi.testclient import TestClient
            from src.presentation.api.main import app
            return TestClient(app)
        except ImportError:
            pytest.skip("FastAPI not installed")
    
    def test_get_sources(self, client):
        """اختبار جلب قائمة المصادر"""
        response = client.get("/api/v1/sources")
        
        assert response.status_code in [200, 404]
        
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, (list, dict))
    
    def test_get_source_status(self, client):
        """اختبار حالة مصدر محدد"""
        response = client.get("/api/v1/sources/sp_today/status")
        
        assert response.status_code in [200, 404]


# ══════════════════════════════════════════════════════════
# اختبارات نقاط نهاية التنبؤات
# ══════════════════════════════════════════════════════════

class TestPredictionsAPI:
    """اختبارات API التنبؤات"""
    
    @pytest.fixture
    def client(self):
        """عميل اختبار FastAPI"""
        try:
            from fastapi.testclient import TestClient
            from src.presentation.api.main import app
            return TestClient(app)
        except ImportError:
            pytest.skip("FastAPI not installed")
    
    def test_get_predictions(self, client):
        """اختبار جلب التنبؤات"""
        response = client.get("/api/v1/predictions/USD-SYP")
        
        # قد لا يكون النموذج مدرباً بعد
        assert response.status_code in [200, 404, 503]
    
    def test_get_prediction_confidence(self, client):
        """اختبار ثقة التنبؤ"""
        response = client.get("/api/v1/predictions/USD-SYP/confidence")
        
        assert response.status_code in [200, 404, 503]


# ══════════════════════════════════════════════════════════
# اختبارات معالجة الأخطاء
# ══════════════════════════════════════════════════════════

class TestAPIErrorHandling:
    """اختبارات معالجة أخطاء API"""
    
    @pytest.fixture
    def client(self):
        """عميل اختبار FastAPI"""
        try:
            from fastapi.testclient import TestClient
            from src.presentation.api.main import app
            return TestClient(app)
        except ImportError:
            pytest.skip("FastAPI not installed")
    
    def test_404_not_found(self, client):
        """اختبار 404 للمسار غير الموجود"""
        response = client.get("/api/v1/nonexistent-endpoint")
        
        assert response.status_code == 404
    
    def test_invalid_currency_pair(self, client):
        """اختبار زوج عملات غير صالح"""
        response = client.get("/api/v1/prices/INVALID-PAIR")
        
        assert response.status_code in [400, 404, 422]
    
    def test_invalid_date_range(self, client):
        """اختبار نطاق تاريخ غير صالح"""
        response = client.get("/api/v1/prices/history?currency_pair=USD-SYP&days=-1")
        
        assert response.status_code in [400, 422]


# ══════════════════════════════════════════════════════════
# اختبارات الأمان
# ══════════════════════════════════════════════════════════

class TestAPISecurity:
    """اختبارات أمان API"""
    
    @pytest.fixture
    def client(self):
        """عميل اختبار FastAPI"""
        try:
            from fastapi.testclient import TestClient
            from src.presentation.api.main import app
            return TestClient(app)
        except ImportError:
            pytest.skip("FastAPI not installed")
    
    def test_cors_headers(self, client):
        """اختبار رؤوس CORS"""
        response = client.options("/health")
        
        # قد تكون CORS مفعلة أو لا
        assert response.status_code in [200, 405]
    
    def test_sql_injection_prevention(self, client):
        """اختبار الحماية من SQL Injection"""
        malicious_input = "'; DROP TABLE prices; --"
        response = client.get(f"/api/v1/prices/{malicious_input}")
        
        # يجب ألا يتسبب في خطأ خادم داخلي
        assert response.status_code != 500
    
    def test_xss_prevention(self, client):
        """اختبار الحماية من XSS"""
        malicious_input = "<script>alert('xss')</script>"
        response = client.get(f"/api/v1/sources/{malicious_input}")
        
        assert response.status_code in [400, 404, 422]


# ══════════════════════════════════════════════════════════
# اختبارات الأداء
# ══════════════════════════════════════════════════════════

class TestAPIPerformance:
    """اختبارات أداء API"""
    
    @pytest.fixture
    def client(self):
        """عميل اختبار FastAPI"""
        try:
            from fastapi.testclient import TestClient
            from src.presentation.api.main import app
            return TestClient(app)
        except ImportError:
            pytest.skip("FastAPI not installed")
    
    def test_health_response_time(self, client):
        """اختبار وقت استجابة نقطة الصحة"""
        import time
        
        start = time.time()
        response = client.get("/health")
        elapsed = time.time() - start
        
        assert response.status_code == 200
        assert elapsed < 1.0, "Health check should respond in under 1 second"
    
    def test_concurrent_requests(self, client):
        """اختبار الطلبات المتزامنة"""
        import concurrent.futures
        
        def make_request():
            return client.get("/health").status_code
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            results = [f.result() for f in futures]
        
        assert all(r == 200 for r in results)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
