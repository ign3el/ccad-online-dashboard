#!/bin/bash

# ================= CONFIGURATION =================
# Set this to your CCAD project folder name on the VPS
PROJECT_NAME="ccad-online-dashboard"
PROJECT_PATH="/www/wwwroot/CCAD Online Dashboard"
LOG_FILE="$PROJECT_PATH/deploy.log"
BRANCH="main"
# =================================================

# 1. SETUP LOGGING
# Create log file if it doesn't exist and set permissions
if [ ! -f "$LOG_FILE" ]; then 
    touch "$LOG_FILE"
    chown www:www "$LOG_FILE"
    chmod 666 "$LOG_FILE"
fi

# Redirect all output to the log file
exec > >(tee -a "$LOG_FILE") 2>&1

echo " "
echo "============================================================"
echo "🚀 DEPLOYMENT STARTED: $PROJECT_NAME"
echo "🕒 Time: $(date '+%Y-%m-%d %H:%M:%S')"
echo "============================================================"

# 2. FIX PERMISSIONS & GIT SAFETY
echo "🔧 Fixing permissions and git safety..."
git config --global --add safe.directory "$PROJECT_PATH"

if [ -d "$PROJECT_PATH" ]; then
    cd "$PROJECT_PATH"
else
    echo "❌ ERROR: Directory $PROJECT_PATH not found!"
    exit 1
fi

# Ensure www user owns files before pull
chown -R www:www "$PROJECT_PATH"

# 3. PULL CODE
if [ -d ".git" ]; then
    echo "📥 Pulling latest code from GitHub ($BRANCH)..."
    sudo -u www git fetch origin $BRANCH
    sudo -u www git reset --hard origin/$BRANCH
    echo "✔ Code synced successfully."
else
    echo "⚠ No .git folder found. Skipping pull."
fi

# 4. DOCKER BUILD
echo "🐳 Docker Build Started (Port 5101)..."

# Stop and remove old containers/orphans
/usr/bin/docker compose down --remove-orphans

# Build and start new ones
/usr/bin/docker compose up -d --build --remove-orphans

# Check status
if [ $? -eq 0 ]; then
    echo "✔ Containers Built Successfully."
else
    echo "❌ ERROR: Docker Build Failed. Check logs above."
    exit 1
fi

# 5. CLEANUP & PERMISSIONS FIX
echo "🧹 Cleaning up and fixing media/database permissions..."
/usr/bin/docker image prune -f

# IMPORTANT: Ensure the backend can write to these folders after Docker starts
chown -R www:www "$PROJECT_PATH/instance"
chown -R www:www "$PROJECT_PATH/uploads"
chmod -R 777 "$PROJECT_PATH/instance" "$PROJECT_PATH/uploads"

echo "============================================================"
echo "✅ DEPLOYMENT FINISHED"
echo "============================================================"
echo " "
echo "🔧 Finalizing permissions..."
echo " "

# Redundant sudo check to match edusmart script style
sudo chmod -R 777 "$PROJECT_PATH/instance"
sudo chmod -R 777 "$PROJECT_PATH/uploads"
echo "Deployment complete and permissions updated!"

echo "============================================================"
echo "✅ PERMISSIONS FIXED"
echo "============================================================"
echo " "
