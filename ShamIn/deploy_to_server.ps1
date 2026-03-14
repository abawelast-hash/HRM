# ============================================
# ShamIn Remote Deployment Script (PowerShell)
# نشر ShamIn على خادم VPS من Windows
# ============================================

$ErrorActionPreference = "Stop"

# ============================================
# Configuration
# ============================================

$SERVER_IP = "187.77.173.160"
$SERVER_USER = "root"
$SERVER_PASSWORD = "Goolbx512@@@"
$APP_DIR = "/opt/shamin"
$REPO_URL = "https://github.com/abawelast-hash/HRM.git"

Write-Host "`n============================================" -ForegroundColor Cyan
Write-Host "  ShamIn Remote Deployment" -ForegroundColor Cyan
Write-Host "  Server: $SERVER_IP" -ForegroundColor Cyan
Write-Host "============================================`n" -ForegroundColor Cyan

# ============================================
# Step 1: Check SSH Client
# ============================================

Write-Host "[INFO] Checking SSH client..." -ForegroundColor Blue

try {
    $sshVersion = ssh -V 2>&1
    Write-Host "[SUCCESS] SSH is available: $sshVersion" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] SSH client not found!" -ForegroundColor Red
    Write-Host "[INFO] Installing OpenSSH Client..." -ForegroundColor Yellow
    
    # Try to install OpenSSH (requires admin)
    try {
        Add-WindowsCapability -Online -Name OpenSSH.Client~~~~0.0.1.0
        Write-Host "[SUCCESS] OpenSSH Client installed" -ForegroundColor Green
    } catch {
        Write-Host "[ERROR] Failed to install SSH. Please install manually:" -ForegroundColor Red
        Write-Host "  Settings -> Apps -> Optional Features -> Add OpenSSH Client" -ForegroundColor Yellow
        exit 1
    }
}

# ============================================
# Step 2: Test Connection
# ============================================

Write-Host "`n[INFO] Testing connection to server..." -ForegroundColor Blue

# Create expect-like script for password authentication
$testCommand = "echo 'Connection successful'"
$sshCommand = "sshpass -p '$SERVER_PASSWORD' ssh -o StrictHostKeyChecking=no $SERVER_USER@$SERVER_IP '$testCommand'"

# Since we don't have sshpass on Windows, we'll use plink or manual connection
Write-Host "[INFO] Please enter password when prompted: $SERVER_PASSWORD" -ForegroundColor Yellow

try {
    ssh -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" "echo 'Connection test successful'"
    Write-Host "[SUCCESS] Connection to server successful" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Connection failed. Please check:" -ForegroundColor Red
    Write-Host "  1. Server IP: $SERVER_IP" -ForegroundColor Yellow
    Write-Host "  2. Username: $SERVER_USER" -ForegroundColor Yellow
    Write-Host "  3. Password: $SERVER_PASSWORD" -ForegroundColor Yellow
    Write-Host "  4. Firewall allows SSH (port 22)" -ForegroundColor Yellow
    exit 1
}

# ============================================
# Step 3: Upload deployment script
# ============================================

Write-Host "`n[INFO] Uploading deployment script to server..." -ForegroundColor Blue

$localScriptPath = ".\deploy.sh"
$remoteScriptPath = "/tmp/deploy.sh"

if (-Not (Test-Path $localScriptPath)) {
    Write-Host "[ERROR] deploy.sh not found in current directory!" -ForegroundColor Red
    exit 1
}

try {
    # Use SCP to copy the file
    scp -o StrictHostKeyChecking=no "$localScriptPath" "$SERVER_USER@${SERVER_IP}:$remoteScriptPath"
    Write-Host "[SUCCESS] Deployment script uploaded" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Failed to upload script" -ForegroundColor Red
    exit 1
}

# ============================================
# Step 4: Execute deployment script
# ============================================

Write-Host "`n[INFO] Executing deployment script on server..." -ForegroundColor Blue
Write-Host "[INFO] This will take 5-10 minutes..." -ForegroundColor Yellow
Write-Host "[INFO] You will see the deployment progress below...`n" -ForegroundColor Yellow

$deployCommands = @"
chmod +x /tmp/deploy.sh
bash /tmp/deploy.sh
"@

try {
    ssh -t "$SERVER_USER@$SERVER_IP" $deployCommands
    Write-Host "`n[SUCCESS] Deployment script executed" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Deployment failed" -ForegroundColor Red
    Write-Host "[INFO] Check the logs above for details" -ForegroundColor Yellow
    exit 1
}

# ============================================
# Step 5: Verify deployment
# ============================================

Write-Host "`n[INFO] Verifying deployment..." -ForegroundColor Blue

$verifyCommands = @"
echo '=== Docker Containers ==='
cd $APP_DIR/HRM/ShamIn && docker compose ps

echo ''
echo '=== Systemd Services ==='
systemctl status shamin-* --no-pager | grep -E '(Active|Loaded)'

echo ''
echo '=== API Health Check ==='
curl -s http://localhost:8000/health || echo 'API not ready yet'

echo ''
echo '=== Dashboard Health Check ==='
curl -s http://localhost:8501/_stcore/health || echo 'Dashboard not ready yet'
"@

try {
    ssh "$SERVER_USER@$SERVER_IP" $verifyCommands
} catch {
    Write-Host "[WARNING] Some health checks failed" -ForegroundColor Yellow
}

# ============================================
# Step 6: Configure Telegram API (Optional)
# ============================================

Write-Host "`n[INFO] Do you want to configure Telegram API now? (y/n): " -ForegroundColor Yellow -NoNewline
$configureTelegram = Read-Host

if ($configureTelegram -eq 'y') {
    Write-Host "`nEnter Telegram API credentials (from https://my.telegram.org):" -ForegroundColor Yellow
    Write-Host "API ID: " -NoNewline
    $apiId = Read-Host
    Write-Host "API Hash: " -NoNewline
    $apiHash = Read-Host
    Write-Host "Phone Number (with country code, e.g., +963xxxxxxxxx): " -NoNewline
    $phone = Read-Host
    
    $telegramConfig = @"
sed -i 's/TELEGRAM_API_ID=.*/TELEGRAM_API_ID=$apiId/' $APP_DIR/HRM/ShamIn/.env
sed -i 's/TELEGRAM_API_HASH=.*/TELEGRAM_API_HASH=$apiHash/' $APP_DIR/HRM/ShamIn/.env
sed -i 's/TELEGRAM_PHONE=.*/TELEGRAM_PHONE=$phone/' $APP_DIR/HRM/ShamIn/.env
echo '[SUCCESS] Telegram API configured'

# Restart services to apply changes
cd $APP_DIR/HRM/ShamIn && docker compose restart celery-worker celery-beat
"@
    
    try {
        ssh "$SERVER_USER@$SERVER_IP" $telegramConfig
        Write-Host "[SUCCESS] Telegram API configured and services restarted" -ForegroundColor Green
    } catch {
        Write-Host "[ERROR] Failed to configure Telegram API" -ForegroundColor Red
    }
}

# ============================================
# Deployment Summary
# ============================================

Write-Host "`n============================================" -ForegroundColor Cyan
Write-Host "  Deployment Completed Successfully!" -ForegroundColor Green
Write-Host "============================================`n" -ForegroundColor Cyan

Write-Host "Service URLs:" -ForegroundColor White
Write-Host "  Dashboard: http://$SERVER_IP:8501" -ForegroundColor Yellow
Write-Host "  API:       http://$SERVER_IP:8000" -ForegroundColor Yellow
Write-Host "  API Docs:  http://$SERVER_IP:8000/docs" -ForegroundColor Yellow
Write-Host "  InfluxDB:  http://$SERVER_IP:8086" -ForegroundColor Yellow
Write-Host "  MinIO:     http://$SERVER_IP:9001" -ForegroundColor Yellow

Write-Host "`nManagement Commands:" -ForegroundColor White
Write-Host "  View logs:        ssh $SERVER_USER@$SERVER_IP 'cd $APP_DIR/HRM/ShamIn && docker compose logs -f'" -ForegroundColor Gray
Write-Host "  Restart services: ssh $SERVER_USER@$SERVER_IP 'sudo systemctl restart shamin-*'" -ForegroundColor Gray
Write-Host "  Stop services:    ssh $SERVER_USER@$SERVER_IP 'sudo systemctl stop shamin-*'" -ForegroundColor Gray

Write-Host "`nNext Steps:" -ForegroundColor White
Write-Host "  1. Open Dashboard: http://$SERVER_IP:8501" -ForegroundColor Yellow
Write-Host "  2. Go to '🔄 تشغيل ومراقبة' page" -ForegroundColor Yellow
Write-Host "  3. Click '▶️ تشغيل جميع المحركات'" -ForegroundColor Yellow
Write-Host "  4. Watch data collection in real-time!" -ForegroundColor Yellow

Write-Host "`n[INFO] Opening Dashboard in browser..." -ForegroundColor Blue
Start-Sleep -Seconds 2
Start-Process "http://$SERVER_IP:8501"

Write-Host "`n[SUCCESS] Deployment script finished!`n" -ForegroundColor Green
