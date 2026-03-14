"""PostgreSQL client using SQLAlchemy."""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os


_engine = None
_SessionLocal = None


def get_engine():
    global _engine
    if _engine is None:
        url = os.getenv('POSTGRES_URL', 'postgresql://shamin_user:password@localhost:5432/shamin_db')
        _engine = create_engine(url, pool_pre_ping=True, pool_size=10)
    return _engine


def get_session():
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(bind=get_engine())
    return _SessionLocal()
