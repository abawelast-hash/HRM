"""Pydantic schemas for raw ingestion data."""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
import uuid


class RawDataItem(BaseModel):
    """Unified schema for all collected data."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    source: str
    source_type: str  # rss, telegram, web, api
    timestamp: datetime
    raw_text: str
    raw_numeric: Optional[float] = None
    language: str = "ar"
    metadata: Dict[str, Any] = Field(default_factory=dict)
    content_hash: str


class CollectionResult(BaseModel):
    """Result of a collection run."""
    source: str
    source_type: str
    collected_count: int
    duplicates_skipped: int = 0
    errors: int = 0
    duration_seconds: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)
