#!/bin/bash

################################################################################
# ShamIn Automated Deployment Script
# نص نشر تلقائي لنظام ShamIn
#
# Usage: bash deploy.sh [OPTIONS]
# Options:
#   --skip-docker     Skip Docker installation
#   --skip-setup      Skip database setup
#   --clean           Clean install (remove old data)
################################################################################

set -e  # Exit on error

# ============================================
# Configuration
# ============================================

APP_NAME="shamin"
APP_DIR="/opt/shamin"
REPO_URL="https://github.com/abawelast-hash/HRM.git"
BRANCH="main"
CURRENT_USER=$(whoami)

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ============================================
# Helper Functions
# ============================================

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_command() {
    if command -v $1 &> /dev/null; then
        log_success "$1 is installed"
        return 0
    else
        log_warning "$1 is not installed"
        return 1
    fi
}

# ============================================
# Parse Arguments
# ============================================

SKIP_DOCKER=false
SKIP_SETUP=false
CLEAN_INSTALL=false

for arg in "$@"; do
    case $arg in
        --skip-docker)
            SKIP_DOCKER=true
            shift
            ;;
        --skip-setup)
            SKIP_SETUP=true
            shift
            ;;
        --clean)
            CLEAN_INSTALL=true
            shift
            ;;
        *)
            ;;
    esac
done

# ============================================
# Step 1: System Update
# ============================================

log_info "Step 1: Updating system packages..."
sudo apt update && sudo apt upgrade -y
sudo apt install -y curl wget git vim htop net-tools
log_success "System updated successfully"

# ============================================
# Step 2: Install Docker
# ============================================

if [ "$SKIP_DOCKER" = false ]; then
    log_info "Step 2: Installing Docker..."
    
    if check_command docker; then
        log_info "Docker already installed, skipping..."
    else
        # Remove old versions
        sudo apt remove -y docker docker-engine docker.io containerd runc 2>/dev/null || true
        
        # Install Docker
        curl -fsSL https://get.docker.com -o get-docker.sh
        sudo sh get-docker.sh
        rm get-docker.sh
        
        # Add user to docker group
        sudo usermod -aG docker $CURRENT_USER
        
        log_success "Docker installed successfully"
        log_warning "You may need to log out and back in for Docker group changes to take effect"
    fi
    
    # Verify Docker Compose
    if ! check_command "docker compose"; then
        log_error "Docker Compose not found. Please install it manually."
        exit 1
    fi
else
    log_info "Step 2: Skipping Docker installation (--skip-docker)"
fi

# ============================================
# Step 3: Setup Firewall
# ============================================

log_info "Step 3: Configuring firewall..."

if command -v ufw &> /dev/null; then
    sudo ufw allow 22/tcp   # SSH
    sudo ufw allow 80/tcp   # HTTP
    sudo ufw allow 443/tcp  # HTTPS
    sudo ufw allow 8000/tcp # API
    sudo ufw allow 8501/tcp # Dashboard
    
    # Enable UFW if not already enabled
    sudo ufw --force enable 2>/dev/null || true
    
    log_success "Firewall configured"
else
    log_warning "UFW not found, skipping firewall setup"
fi

# ============================================
# Step 4: Create App Directory
# ============================================

log_info "Step 4: Setting up application directory..."

if [ "$CLEAN_INSTALL" = true ] && [ -d "$APP_DIR" ]; then
    log_warning "Removing old installation (--clean)..."
    sudo rm -rf "$APP_DIR"
fi

sudo mkdir -p "$APP_DIR"
sudo chown $CURRENT_USER:$CURRENT_USER "$APP_DIR"
log_success "Application directory ready: $APP_DIR"

# ============================================
# Step 5: Clone/Update Repository
# ============================================

log_info "Step 5: Cloning/updating repository..."

if [ -d "$APP_DIR/HRM" ]; then
    log_info "Repository exists, pulling latest changes..."
    cd "$APP_DIR/HRM"
    git fetch origin
    git checkout $BRANCH
    git pull origin $BRANCH
else
    log_info "Cloning repository..."
    cd "$APP_DIR"
    git clone "$REPO_URL"
    cd HRM
    git checkout $BRANCH
fi

cd "$APP_DIR/HRM/ShamIn"
log_success "Repository ready at: $(pwd)"

# ============================================
# Step 6: Setup Environment File
# ============================================

log_info "Step 6: Setting up environment file..."

if [ ! -f .env ]; then
    log_info "Creating .env from .env.example..."
    cp .env.example .env
    
    # Generate random passwords
    POSTGRES_PASS=$(openssl rand -base64 24 | tr -d "=+/" | cut -c1-24)
    INFLUX_PASS=$(openssl rand -base64 24 | tr -d "=+/" | cut -c1-24)
    INFLUX_TOKEN=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-32)
    MINIO_ACCESS=$(openssl rand -base64 16 | tr -d "=+/" | cut -c1-16)
    MINIO_SECRET=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-32)
    SECRET_KEY=$(openssl rand -base64 48 | tr -d "=+/" | cut -c1-48)
    
    # Update .env with generated passwords
    sed -i "s/POSTGRES_PASSWORD=.*/POSTGRES_PASSWORD=$POSTGRES_PASS/" .env
    sed -i "s/INFLUXDB_PASSWORD=.*/INFLUXDB_PASSWORD=$INFLUX_PASS/" .env
    sed -i "s/INFLUXDB_TOKEN=.*/INFLUXDB_TOKEN=$INFLUX_TOKEN/" .env
    sed -i "s/MINIO_ACCESS_KEY=.*/MINIO_ACCESS_KEY=$MINIO_ACCESS/" .env
    sed -i "s/MINIO_SECRET_KEY=.*/MINIO_SECRET_KEY=$MINIO_SECRET/" .env
    sed -i "s/SECRET_KEY=.*/SECRET_KEY=$SECRET_KEY/" .env
    
    log_success ".env file created with auto-generated passwords"
    log_warning "IMPORTANT: Save these credentials securely!"
    echo "POSTGRES_PASSWORD=$POSTGRES_PASS"
    echo "INFLUXDB_TOKEN=$INFLUX_TOKEN"
    echo "MINIO_ACCESS_KEY=$MINIO_ACCESS"
    echo "MINIO_SECRET_KEY=$MINIO_SECRET"
else
    log_info ".env already exists, skipping..."
fi

# ============================================
# Step 7: Start Docker Services
# ============================================

log_info "Step 7: Starting Docker services..."

# Stop any running services
docker compose down 2>/dev/null || true

# Start infrastructure services first
log_info "Starting infrastructure services (postgres, influxdb, redis, minio)..."
docker compose up -d postgres influxdb redis minio

# Wait for services to be healthy
log_info "Waiting for services to be ready (30 seconds)..."
sleep 30

# Check health
docker compose ps

log_success "Infrastructure services started"

# ============================================
# Step 8: Initialize Databases
# ============================================

if [ "$SKIP_SETUP" = false ]; then
    log_info "Step 8: Initializing databases..."
    
    # Wait a bit more for databases to be fully ready
    sleep 10
    
    # Setup PostgreSQL
    log_info "Setting up PostgreSQL..."
    docker compose exec -T postgres psql -U shamin_user -d shamin_db <<EOF
CREATE TABLE IF NOT EXISTS raw_texts (
    id SERIAL PRIMARY KEY,
    source VARCHAR(100) NOT NULL,
    text TEXT NOT NULL,
    url VARCHAR(500),
    timestamp TIMESTAMP NOT NULL,
    metadata JSONB,
    hash VARCHAR(32) UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS data_sources (
    id SERIAL PRIMARY KEY,
    type VARCHAR(50) NOT NULL,
    name VARCHAR(200) NOT NULL,
    config JSONB NOT NULL,
    enabled BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_raw_texts_hash ON raw_texts(hash);
CREATE INDEX IF NOT EXISTS idx_raw_texts_timestamp ON raw_texts(timestamp);
CREATE INDEX IF NOT EXISTS idx_raw_texts_source ON raw_texts(source);
CREATE INDEX IF NOT EXISTS idx_data_sources_enabled ON data_sources(enabled);
EOF
    
    if [ $? -eq 0 ]; then
        log_success "PostgreSQL initialized"
    else
        log_error "PostgreSQL initialization failed"
        exit 1
    fi
    
    # InfluxDB is auto-initialized via environment variables
    log_success "InfluxDB initialized automatically"
    
else
    log_info "Step 8: Skipping database setup (--skip-setup)"
fi

# ============================================
# Step 9: Start Application Services
# ============================================

log_info "Step 9: Starting application services..."

docker compose up -d api dashboard celery-worker celery-beat

sleep 10
docker compose ps

log_success "Application services started"

# ============================================
# Step 10: Create Systemd Services
# ============================================

log_info "Step 10: Creating systemd services..."

# Dashboard service
sudo tee /etc/systemd/system/shamin-dashboard.service > /dev/null <<EOF
[Unit]
Description=ShamIn Dashboard (Streamlit)
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
User=$CURRENT_USER
WorkingDirectory=$APP_DIR/HRM/ShamIn
ExecStart=/usr/bin/docker compose up -d dashboard
ExecStop=/usr/bin/docker compose stop dashboard
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# API service
sudo tee /etc/systemd/system/shamin-api.service > /dev/null <<EOF
[Unit]
Description=ShamIn API (FastAPI)
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
User=$CURRENT_USER
WorkingDirectory=$APP_DIR/HRM/ShamIn
ExecStart=/usr/bin/docker compose up -d api
ExecStop=/usr/bin/docker compose stop api
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Celery Worker service
sudo tee /etc/systemd/system/shamin-celery.service > /dev/null <<EOF
[Unit]
Description=ShamIn Celery Worker
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
User=$CURRENT_USER
WorkingDirectory=$APP_DIR/HRM/ShamIn
ExecStart=/usr/bin/docker compose up -d celery-worker
ExecStop=/usr/bin/docker compose stop celery-worker
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Celery Beat service
sudo tee /etc/systemd/system/shamin-beat.service > /dev/null <<EOF
[Unit]
Description=ShamIn Celery Beat (Scheduler)
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
User=$CURRENT_USER
WorkingDirectory=$APP_DIR/HRM/ShamIn
ExecStart=/usr/bin/docker compose up -d celery-beat
ExecStop=/usr/bin/docker compose stop celery-beat
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd and enable services
sudo systemctl daemon-reload
sudo systemctl enable shamin-dashboard shamin-api shamin-celery shamin-beat

log_success "Systemd services created and enabled"

# ============================================
# Step 11: Setup Backup Cron Job
# ============================================

log_info "Step 11: Setting up backup cron job..."

BACKUP_DIR="$APP_DIR/backups"
mkdir -p "$BACKUP_DIR"

# Add cron job for daily backups at 2 AM
(crontab -l 2>/dev/null; echo "0 2 * * * cd $APP_DIR/HRM/ShamIn && docker compose exec -T postgres pg_dump -U shamin_user shamin_db > $BACKUP_DIR/postgres_\$(date +\%Y\%m\%d).sql") | crontab -

log_success "Backup cron job installed"

# ============================================
# Step 12: Health Checks
# ============================================

log_info "Step 12: Running health checks..."

sleep 5

# Check API
if curl -s http://localhost:8000/health > /dev/null; then
    log_success "API is healthy"
else
    log_warning "API health check failed"
fi

# Check Dashboard
if curl -s http://localhost:8501/_stcore/health > /dev/null; then
    log_success "Dashboard is healthy"
else
    log_warning "Dashboard health check failed"
fi

# Check containers
RUNNING_CONTAINERS=$(docker compose ps --services --filter "status=running" | wc -l)
log_info "Running containers: $RUNNING_CONTAINERS/8"

# ============================================
# Deployment Summary
# ============================================

echo ""
echo "============================================"
log_success "🎉 Deployment completed successfully!"
echo "============================================"
echo ""
echo "📊 Service URLs:"
echo "   Dashboard: http://$(hostname -I | awk '{print $1}'):8501"
echo "   API:       http://$(hostname -I | awk '{print $1}'):8000"
echo "   API Docs:  http://$(hostname -I | awk '{print $1}'):8000/docs"
echo ""
echo "🐳 Docker Services:"
docker compose ps
echo ""
echo "📁 Application Directory: $APP_DIR/HRM/ShamIn"
echo "📁 Backup Directory:      $BACKUP_DIR"
echo ""
echo "🔧 Management Commands:"
echo "   View logs:        cd $APP_DIR/HRM/ShamIn && docker compose logs -f"
echo "   Restart services: sudo systemctl restart shamin-*"
echo "   Stop services:    sudo systemctl stop shamin-*"
echo "   Update app:       cd $APP_DIR/HRM/ShamIn && git pull && docker compose up -d --build"
echo ""
echo "⚠️  Next Steps:"
echo "   1. Configure Telegram API in .env (TELEGRAM_API_ID, TELEGRAM_API_HASH)"
echo "   2. Configure SMTP for alerts in .env (SMTP_*)"
echo "   3. Test data collection from Dashboard"
echo "   4. Review logs: docker compose logs -f"
echo ""
log_success "Deployment script finished!"
