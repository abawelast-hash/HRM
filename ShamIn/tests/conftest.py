"""
ShamIn - Test Configuration
ملف إعدادات pytest المشترك لجميع الاختبارات
"""

import pytest
import asyncio
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime, timezone

# إضافة مسار المشروع
sys.path.insert(0, str(Path(__file__).parent.parent))

# ══════════════════════════════════════════════════════════
# إعدادات البيئة للاختبارات
# ══════════════════════════════════════════════════════════

@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """إعداد متغيرات البيئة للاختبارات"""
    os.environ.setdefault("POSTGRES_HOST", "localhost")
    os.environ.setdefault("POSTGRES_PORT", "5432")
    os.environ.setdefault("POSTGRES_DB", "shamin_test_db")
    os.environ.setdefault("POSTGRES_USER", "shamin_user")
    os.environ.setdefault("POSTGRES_PASSWORD", "test_password")
    os.environ.setdefault("INFLUXDB_URL", "http://localhost:8086")
    os.environ.setdefault("INFLUXDB_TOKEN", "test_token")
    os.environ.setdefault("INFLUXDB_ORG", "shamin_org")
    os.environ.setdefault("INFLUXDB_BUCKET", "test_bucket")
    os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
    os.environ.setdefault("TELEGRAM_API_ID", "12345")
    os.environ.setdefault("TELEGRAM_API_HASH", "test_hash")
    os.environ.setdefault("TELEGRAM_PHONE", "+1234567890")
    os.environ.setdefault("ENVIRONMENT", "test")
    os.environ.setdefault("LOG_LEVEL", "DEBUG")
    yield


# ══════════════════════════════════════════════════════════
# Fixtures للـ Event Loop
# ══════════════════════════════════════════════════════════

@pytest.fixture(scope="session")
def event_loop():
    """إنشاء event loop للاختبارات غير المتزامنة"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# ══════════════════════════════════════════════════════════
# Fixtures للبيانات الوهمية
# ══════════════════════════════════════════════════════════

@pytest.fixture
def sample_raw_text():
    """بيانات نص خام للاختبار"""
    return {
        "source_type": "telegram",
        "source_name": "test_channel",
        "content": "سعر الدولار اليوم 14500 ليرة سورية",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "metadata": {
            "channel_id": "123456",
            "message_id": "789"
        }
    }


@pytest.fixture
def sample_price_data():
    """بيانات سعر للاختبار"""
    return {
        "currency_pair": "USD/SYP",
        "buy_price": 14500.0,
        "sell_price": 14600.0,
        "source": "sp_today",
        "location": "Damascus",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@pytest.fixture
def sample_rss_feed():
    """بيانات RSS للاختبار"""
    return {
        "name": "test_feed",
        "url": "https://example.com/feed",
        "category": "news",
        "language": "ar"
    }


@pytest.fixture
def sample_telegram_channel():
    """بيانات قناة تلغرام للاختبار"""
    return {
        "name": "test_channel",
        "channel": "@test_channel",
        "type": "prices",
        "frequency_minutes": 5
    }


# ══════════════════════════════════════════════════════════
# Fixtures للمحاكاة (Mocks)
# ══════════════════════════════════════════════════════════

@pytest.fixture
def mock_postgres_connection():
    """محاكاة اتصال PostgreSQL"""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
    mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=None)
    mock_cursor.execute.return_value = None
    mock_cursor.fetchall.return_value = []
    mock_cursor.fetchone.return_value = None
    return mock_conn


@pytest.fixture
def mock_influxdb_client():
    """محاكاة عميل InfluxDB"""
    mock_client = MagicMock()
    mock_write_api = MagicMock()
    mock_query_api = MagicMock()
    mock_client.write_api.return_value = mock_write_api
    mock_client.query_api.return_value = mock_query_api
    return mock_client


@pytest.fixture
def mock_redis_client():
    """محاكاة عميل Redis"""
    mock_client = MagicMock()
    mock_client.get.return_value = None
    mock_client.set.return_value = True
    mock_client.delete.return_value = 1
    return mock_client


@pytest.fixture
def mock_telegram_client():
    """محاكاة عميل Telegram"""
    mock_client = AsyncMock()
    mock_client.get_messages.return_value = []
    mock_client.get_entity.return_value = MagicMock(id=123456)
    return mock_client


@pytest.fixture
def mock_http_response():
    """محاكاة استجابة HTTP"""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = "<html><body>Test</body></html>"
    mock_response.json.return_value = {"status": "ok"}
    return mock_response


# ══════════════════════════════════════════════════════════
# Fixtures للمسارات
# ══════════════════════════════════════════════════════════

@pytest.fixture
def project_root():
    """مسار جذر المشروع"""
    return Path(__file__).parent.parent


@pytest.fixture
def config_dir(project_root):
    """مسار مجلد الإعدادات"""
    return project_root / "config"


@pytest.fixture
def data_dir(project_root):
    """مسار مجلد البيانات"""
    return project_root / "data"


# ══════════════════════════════════════════════════════════
# Fixtures للتطبيق
# ══════════════════════════════════════════════════════════

@pytest.fixture
def test_client():
    """عميل اختبار FastAPI"""
    try:
        from fastapi.testclient import TestClient
        from src.presentation.api.main import app
        return TestClient(app)
    except ImportError:
        pytest.skip("FastAPI not available")


# ══════════════════════════════════════════════════════════
# أدوات مساعدة
# ══════════════════════════════════════════════════════════

def assert_valid_price(price_data: dict):
    """التحقق من صحة بيانات السعر"""
    required_fields = ["currency_pair", "buy_price", "sell_price", "source", "timestamp"]
    for field in required_fields:
        assert field in price_data, f"Missing field: {field}"
    assert price_data["buy_price"] > 0, "Buy price must be positive"
    assert price_data["sell_price"] > 0, "Sell price must be positive"


def assert_valid_text(text_data: dict):
    """التحقق من صحة بيانات النص"""
    required_fields = ["source_type", "source_name", "content", "timestamp"]
    for field in required_fields:
        assert field in text_data, f"Missing field: {field}"
    assert len(text_data["content"]) > 0, "Content cannot be empty"
