#!/bin/bash
# Hermass M3 Pilot 阿里云部署脚本
# 在服务器上执行: bash deploy.sh

set -e

echo "=== Hermass M3 Pilot 部署脚本 ==="

APP_DIR="/opt/hermass"
DOMAIN="quant.supertrader.world"
REPO_URL="https://github.com/jackeyunjie/Hermass-quant-platform.git"

# 1. 安装系统依赖
echo "[1/8] 安装系统依赖..."
sudo yum install -y git nginx python3 python3-pip python3-devel gcc openssl-devel

# 2. 创建应用目录
echo "[2/8] 创建应用目录..."
sudo mkdir -p $APP_DIR
sudo chown $(whoami):$(whoami) $APP_DIR

# 3. 克隆代码
echo "[3/8] 克隆代码..."
if [ -d "$APP_DIR/.git" ]; then
    cd $APP_DIR && git pull
else
    git clone $REPO_URL $APP_DIR
fi

# 4. 安装Python依赖
echo "[4/8] 安装Python依赖..."
cd $APP_DIR
pip3 install --user -e .

# 5. 配置环境变量
echo "[5/8] 配置环境变量..."
cat > $APP_DIR/.env << 'EOF'
HERMASS_M3_INVITE_TOKENS=VFmDwizfH8kkj3Gz09lq_A,cfIPwHmW0G9rjm4rDQuHBA,AlLg1MjVVC0a6SuY-4EGOA,IjDV09cbRTk_NCw7VKZpXQ,Jlww1D1kOwJEfz4oDSkJgA
STRATEGY_LAB_STORAGE_DB=outputs/strategy_lab/web_storage.duckdb
STRATEGY_LAB_AUDIT_DB=outputs/strategy_lab/web_audit.duckdb
FOUNDATION_DB=data/p116_foundation.duckdb
STATE_CUBE_DB=data/state_cube.duckdb
EOF

# 6. 配置systemd服务
echo "[6/8] 配置systemd服务..."
sudo tee /etc/systemd/system/hermass.service > /dev/null << EOF
[Unit]
Description=Hermass Strategy Lab
After=network.target

[Service]
Type=simple
User=$(whoami)
WorkingDirectory=$APP_DIR
Environment=PYTHONPATH=$APP_DIR
EnvironmentFile=$APP_DIR/.env
ExecStart=/usr/bin/python3 -m uvicorn web.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# 7. 配置Nginx
echo "[7/8] 配置Nginx..."
sudo tee /etc/nginx/conf.d/hermass.conf > /dev/null << EOF
server {
    listen 80;
    server_name $DOMAIN;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

# 8. 启动服务
echo "[8/8] 启动服务..."
sudo systemctl daemon-reload
sudo systemctl enable hermass
sudo systemctl start hermass
sudo systemctl restart nginx

echo "=== 部署完成 ==="
echo "访问地址: http://$DOMAIN"
echo "检查状态: sudo systemctl status hermass"
