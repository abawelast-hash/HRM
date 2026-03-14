# ============================================
# ShamIn VPS Deployment Script (PowerShell)
# نص نشر ShamIn على VPS من Windows
# ============================================

$ErrorActionPreference = "Stop"

# Configuration
$VPS_IP = "187.77.173.160"
$VPS_USER = Read-Host "Enter VPS username"
$REPO_URL = "https://github.com/abawelast-hash/HRM.git"
$APP_DIR = "/opt/shamin"

Write-Host "`n============================================" -ForegroundColor Cyan
Write-Host "  ShamIn VPS Deployment" -ForegroundColor Cyan
Write-Host "  نشر ShamIn على VPS" -ForegroundColor Cyan
Write-Host "============================================`n" -ForegroundColor Cyan

Write-Host "[INFO] Connecting to VPS: $VPS_USER@$VPS_IP" -ForegroundColor Blue

# Test SSH connection
Write-Host "`n[STEP 1] Testing SSH connection..." -ForegroundColor Yellow
try {
    ssh -o ConnectTimeout=10 "$VPS_USER@$VPS_IP" "echo 'SSH connection successful!'"
    Write-Host "[SUCCESS] SSH connection verified!" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Cannot connect to VPS. Check:" -ForegroundColor Red
    Write-Host "  - IP address: $VPS_IP" -ForegroundColor Red
    Write-Host "  - Username: $VPS_USER" -ForegroundColor Red
    Write-Host "  - SSH port 22 is open" -ForegroundColor Red
    Write-Host "  - Password/SSH key is correct" -ForegroundColor Red
    exit 1
}

# Download and execute deploy script
Write-Host "`n[STEP 2] Downloading deployment script on VPS..." -ForegroundColor Yellow

$REMOTE_COMMANDS = @"
set -e

echo '[INFO] Creating app directory...'
sudo mkdir -p $APP_DIR
sudo chown \`$(whoami):\`$(whoami) $APP_DIR

echo '[INFO] Downloading deploy.sh...'
cd $APP_DIR
curl -fsSL https://raw.githubusercontent.com/abawelast-hash/HRM/main/ShamIn/deploy.sh -o deploy.sh
chmod +x deploy.sh

echo '[INFO] Starting deployment...'
bash deploy.sh

echo ''
echo '[SUCCESS] Deployment completed!'
echo 'Access your services at:'
echo '  Dashboard: http://$VPS_IP:8501'
echo '  API:       http://$VPS_IP:8000'
echo '  API Docs:  http://$VPS_IP:8000/docs'
"@

# Execute remote commands
Write-Host "`n[INFO] Executing deployment on VPS..." -ForegroundColor Blue
Write-Host "[INFO] This may take 5-10 minutes..." -ForegroundColor Yellow
Write-Host "`n----------------------------------------`n" -ForegroundColor Gray

ssh -t "$VPS_USER@$VPS_IP" $REMOTE_COMMANDS

Write-Host "`n----------------------------------------`n" -ForegroundColor Gray

# Final verification
Write-Host "`n[STEP 3] Verifying deployment..." -ForegroundColor Yellow

Start-Sleep -Seconds 5

# Test API
$API_URL = "http://${VPS_IP}:8000/health"
try {
    $response = Invoke-WebRequest -Uri $API_URL -TimeoutSec 10
    if ($response.StatusCode -eq 200) {
        Write-Host "[SUCCESS] API is healthy!" -ForegroundColor Green
    }
} catch {
    Write-Host "[WARNING] API health check failed. May need a few more seconds..." -ForegroundColor Yellow
}

# Test Dashboard
$DASHBOARD_URL = "http://${VPS_IP}:8501"
try {
    $response = Invoke-WebRequest -Uri $DASHBOARD_URL -TimeoutSec 10
    if ($response.StatusCode -eq 200) {
        Write-Host "[SUCCESS] Dashboard is accessible!" -ForegroundColor Green
    }
} catch {
    Write-Host "[WARNING] Dashboard health check failed. May need a few more seconds..." -ForegroundColor Yellow
}

# Display summary
Write-Host "`n============================================" -ForegroundColor Cyan
Write-Host "  Deployment Summary" -ForegroundColor Cyan
Write-Host "============================================`n" -ForegroundColor Cyan

Write-Host "✅ Services deployed to: $VPS_IP`n" -ForegroundColor Green

Write-Host "📊 Access URLs:" -ForegroundColor White
Write-Host "   Dashboard:  http://${VPS_IP}:8501" -ForegroundColor Cyan
Write-Host "   API:        http://${VPS_IP}:8000" -ForegroundColor Cyan
Write-Host "   API Docs:   http://${VPS_IP}:8000/docs" -ForegroundColor Cyan
Write-Host "   InfluxDB:   http://${VPS_IP}:8086" -ForegroundColor Cyan
Write-Host "   MinIO:      http://${VPS_IP}:9001`n" -ForegroundColor Cyan

Write-Host "🔧 Management Commands:" -ForegroundColor White
Write-Host "   SSH to server:  ssh $VPS_USER@$VPS_IP" -ForegroundColor Gray
Write-Host "   View logs:      ssh $VPS_USER@$VPS_IP 'cd $APP_DIR/HRM/ShamIn && docker compose logs -f'" -ForegroundColor Gray
Write-Host "   Restart:        ssh $VPS_USER@$VPS_IP 'sudo systemctl restart shamin-*'" -ForegroundColor Gray
Write-Host "   Stop:           ssh $VPS_USER@$VPS_IP 'sudo systemctl stop shamin-*'`n" -ForegroundColor Gray

Write-Host "⚠️  Next Steps:" -ForegroundColor Yellow
Write-Host "   1. Open Dashboard: http://${VPS_IP}:8501" -ForegroundColor White
Write-Host "   2. Configure Telegram API in .env (optional)" -ForegroundColor White
Write-Host "   3. Configure SMTP for alerts (optional)" -ForegroundColor White
Write-Host "   4. Test data collection from Dashboard" -ForegroundColor White
Write-Host "`n"

Write-Host "[SUCCESS] Deployment script finished!" -ForegroundColor Green

# Ask to open browser
$openBrowser = Read-Host "`nOpen Dashboard in browser? (y/n)"
if ($openBrowser -eq "y") {
    Start-Process "http://${VPS_IP}:8501"
}
