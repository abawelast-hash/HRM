"""ShamIn - PostgreSQL table creation script."""
from sqlalchemy import (
    create_engine, Column, Integer, String, Text,
    DateTime, Float, Boolean,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import declarative_base
import uuid
from datetime import datetime


Base = declarative_base()


class Source(Base):
    __tablename__ = 'sources'

    id = Column(Integer, primary_key=True)
    name = Column(String(255), unique=True, nullable=False)
    type = Column(String(50), nullable=False)  # rss, telegram, web, api
    url = Column(Text)
    frequency_minutes = Column(Integer, default=15)
    is_active = Column(Boolean, default=True)
    last_fetch = Column(DateTime)
    config = Column(JSONB)
    created_at = Column(DateTime, default=datetime.utcnow)


class RawNews(Base):
    __tablename__ = 'raw_news'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_id = Column(Integer, nullable=False)
    source_type = Column(String(50), nullable=False)
    timestamp = Column(DateTime, nullable=False, index=True)
    raw_text = Column(Text, nullable=False)
    raw_numeric = Column(Float)
    language = Column(String(10))
    content_hash = Column(String(64), unique=True, index=True)  # SHA-256
    metadata = Column(JSONB)
    created_at = Column(DateTime, default=datetime.utcnow)


class ProcessedNews(Base):
    __tablename__ = 'processed_news'

    id = Column(UUID(as_uuid=True), primary_key=True)
    cleaned_text = Column(Text)
    extracted_price = Column(Float)
    event_category = Column(String(50))  # military, political, economic, social
    event_weight = Column(Float)
    sentiment = Column(String(20))  # positive, negative, neutral
    sentiment_score = Column(Float)  # -1 to 1
    embedding_vector = Column(JSONB)
    processing_timestamp = Column(DateTime, default=datetime.utcnow)
    processing_version = Column(String(20))


class Prediction(Base):
    __tablename__ = 'predictions'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    prediction_timestamp = Column(DateTime, nullable=False, index=True)
    horizon_hours = Column(Integer, nullable=False)  # 24 or 72

    predicted_price = Column(Float, nullable=False)
    predicted_direction = Column(String(20))  # up, down, stable
    confidence = Column(Float)  # 0-1

    # Quantiles (from TFT)
    q05 = Column(Float)
    q25 = Column(Float)
    q50 = Column(Float)
    q75 = Column(Float)
    q95 = Column(Float)

    # Explanation
    top_features = Column(JSONB)
    shap_values = Column(JSONB)
    contributing_events = Column(JSONB)

    # Actuals (filled later)
    actual_price = Column(Float)
    actual_direction = Column(String(20))

    # Evaluation
    error_mae = Column(Float)
    error_mape = Column(Float)
    direction_correct = Column(Boolean)

    model_version = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)


class ModelPerformance(Base):
    __tablename__ = 'model_performance'

    id = Column(Integer, primary_key=True)
    model_name = Column(String(100), nullable=False)
    model_version = Column(String(50), nullable=False)
    evaluation_date = Column(DateTime, nullable=False, index=True)

    mae = Column(Float)
    rmse = Column(Float)
    mape = Column(Float)
    r2_score = Column(Float)
    directional_accuracy = Column(Float)

    test_samples = Column(Integer)
    horizon_hours = Column(Integer)
    dataset_version = Column(String(50))

    backtest_windows = Column(Integer)
    avg_mae = Column(Float)
    std_mae = Column(Float)

    hyperparameters = Column(JSONB)
    created_at = Column(DateTime, default=datetime.utcnow)


class ClassifiedEvent(Base):
    __tablename__ = 'classified_events'

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    category = Column(String(50), nullable=False)
    title = Column(Text)
    description = Column(Text)
    weight = Column(Float, default=0.5)
    decay_applied = Column(Boolean, default=False)
    source = Column(String(255))
    impact_score = Column(Float)


class DriftMonitoring(Base):
    __tablename__ = 'drift_monitoring'

    id = Column(Integer, primary_key=True)
    check_timestamp = Column(DateTime, nullable=False, index=True)
    drift_type = Column(String(50))  # data_drift, concept_drift
    feature_name = Column(String(100))
    ks_statistic = Column(Float)
    p_value = Column(Float)
    is_drift_detected = Column(Boolean)
    recommendation = Column(Text)


def create_all_tables(database_url: str):
    engine = create_engine(database_url)
    Base.metadata.create_all(engine)
    print("✅ All tables created successfully")


if __name__ == "__main__":
    import os
    db_url = os.getenv(
        'POSTGRES_URL',
        'postgresql://shamin_user:password@localhost:5432/shamin_db'
    )
    create_all_tables(db_url)
