# ShamIn — SYP/USD Exchange Rate Forecaster

نظام ذكي لتوقع سعر صرف الليرة السورية مقابل الدولار الأمريكي باستخدام التعلم العميق وتحليل المشاعر.

## Overview

ShamIn combines multiple data sources (Telegram channels, RSS feeds, web scrapers) with advanced ML models (TFT, XGBoost, LSTM) to forecast the SYP/USD exchange rate with 24h and 72h horizons.

## Architecture

```
Data Collection → Processing → Feature Engineering → Prediction → Dashboard
(Telegram/RSS/Web)  (Arabic NLP)   (Technical + Sentiment)  (TFT/Hybrid)   (Streamlit/API)
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| ML Core | PyTorch, PyTorch Lightning, PyTorch Forecasting (TFT) |
| Baseline | XGBoost, HLT/ARIMA, statsmodels |
| NLP | CAMeL Tools, Farasa, arabic-reshaper |
| Data Collection | Telethon, feedparser, BeautifulSoup, Selenium |
| Storage | PostgreSQL 16, InfluxDB 2.7, MinIO |
| Queue | Celery + Redis 7 |
| API | FastAPI + Uvicorn |
| Dashboard | Streamlit + Plotly |
| MLOps | Optuna, MLflow, SHAP |

## Quick Start

```bash
# 1. Clone and setup
cd ShamIn
python -m venv venv
venv\Scripts\activate      # Windows
pip install -r requirements.txt

# 2. Configure environment
copy .env.example .env
# Edit .env with your credentials

# 3. Start infrastructure
docker-compose up -d

# 4. Initialize databases
python scripts/setup_db.py
python scripts/setup_influxdb.py
python scripts/setup_minio.py
```

## Project Structure

```
ShamIn/
├── config/          # YAML configuration files
├── src/
│   ├── ingestion/   # Data collectors (Telegram, RSS, Web)
│   ├── processing/  # Arabic NLP, price extraction, features
│   ├── prediction/  # ML models (TFT, XGBoost, LSTM, Hybrid)
│   ├── storage/     # Database clients (Postgres, InfluxDB, MinIO)
│   ├── presentation/# Dashboard (Streamlit), API (FastAPI), Alerts
│   ├── monitoring/  # Drift detection, health checks
│   └── utils/       # Config loader, logging, utilities
├── data/            # Local data storage
├── scripts/         # Setup and maintenance scripts
├── tests/           # Unit tests
├── notebooks/       # Jupyter experiments
└── docs/            # Documentation
```

## License

Private — All rights reserved.
