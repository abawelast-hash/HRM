@echo off
REM ============================================
REM ShamIn Local Deployment Script (Windows)
REM نص نشر محلي لنظام ShamIn على Windows
REM ============================================

echo.
echo ============================================
echo   ShamIn Local Deployment
echo   نشر محلي لنظام ShamIn
echo ============================================
echo.

REM Check if Docker is installed
where docker >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Docker is not installed!
    echo [ERROR] Please install Docker Desktop from: https://www.docker.com/products/docker-desktop
    pause
    exit /b 1
)

echo [INFO] Docker is installed
docker --version

REM Check if Docker Compose is available
docker compose version >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Docker Compose is not available!
    pause
    exit /b 1
)

echo [INFO] Docker Compose is available
docker compose version

REM Navigate to ShamIn directory
cd /d "%~dp0"
echo [INFO] Current directory: %CD%

REM Check if .env exists
if not exist .env (
    echo [INFO] Creating .env from .env.example...
    copy .env.example .env
    echo [WARNING] Please edit .env and configure your credentials!
    echo [WARNING] Press any key after editing .env to continue...
    pause
)

echo.
echo [INFO] Starting infrastructure services...
docker compose down
docker compose up -d postgres influxdb redis minio

echo [INFO] Waiting for services to be ready (30 seconds)...
timeout /t 30 /nobreak

echo.
echo [INFO] Checking infrastructure health...
docker compose ps

echo.
echo [INFO] Initializing PostgreSQL database...
docker compose exec -T postgres psql -U shamin_user -d shamin_db < scripts\schema.sql 2>nul
if %errorlevel% neq 0 (
    echo [WARNING] Database initialization might have failed. Trying manual setup...
    docker compose exec postgres psql -U shamin_user -d shamin_db -c "CREATE TABLE IF NOT EXISTS raw_texts (id SERIAL PRIMARY KEY, source VARCHAR(100), text TEXT, url VARCHAR(500), timestamp TIMESTAMP, metadata JSONB, hash VARCHAR(32) UNIQUE, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);"
    docker compose exec postgres psql -U shamin_user -d shamin_db -c "CREATE TABLE IF NOT EXISTS data_sources (id SERIAL PRIMARY KEY, type VARCHAR(50), name VARCHAR(200), config JSONB, enabled BOOLEAN DEFAULT true, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);"
)

echo [SUCCESS] PostgreSQL initialized

echo.
echo [INFO] Starting application services...
docker compose up -d api dashboard celery-worker celery-beat

timeout /t 10 /nobreak

echo.
echo [INFO] Checking all services...
docker compose ps

echo.
echo ============================================
echo [SUCCESS] Deployment completed!
echo ============================================
echo.
echo Service URLs:
echo   Dashboard: http://localhost:8501
echo   API:       http://localhost:8000
echo   API Docs:  http://localhost:8000/docs
echo   InfluxDB:  http://localhost:8086
echo   MinIO:     http://localhost:9001
echo.
echo Management Commands:
echo   View logs:        docker compose logs -f
echo   Stop services:    docker compose down
echo   Restart services: docker compose restart
echo   Update app:       git pull ^&^& docker compose up -d --build
echo.
echo Next Steps:
echo   1. Configure Telegram API in .env
echo   2. Configure SMTP for alerts in .env
echo   3. Open Dashboard: http://localhost:8501
echo   4. Test data collection
echo.

REM Ask if user wants to view logs
echo.
set /p VIEW_LOGS="Do you want to view logs now? (y/n): "
if /i "%VIEW_LOGS%"=="y" (
    docker compose logs -f
)

pause
