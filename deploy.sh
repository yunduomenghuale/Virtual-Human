#!/bin/bash
set -euo pipefail

# Virtual-Human Linux 一键部署脚本
# 用法: sudo bash deploy.sh [域名] [API_KEY]
# 示例: sudo bash deploy.sh demo.example.com sk-xxxx

DOMAIN=${1:-}
API_KEY=${2:-}
DEPLOY_DIR="/opt/virtual-human"
SERVICE_USER="www-data"

# ===================== 颜色输出 =====================
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

info()  { echo -e "${GREEN}[INFO]${NC}  $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*"; exit 1; }

# ===================== 检查权限 =====================
if [[ $EUID -ne 0 ]]; then
   error "请使用 sudo 运行此脚本"
fi

# ===================== 检查参数 =====================
if [[ -z "$DOMAIN" ]]; then
    warn "未提供域名，将使用服务器 IP 作为访问地址"
    DOMAIN=$(curl -s ifconfig.me || hostname -I | awk '{print $1}')
fi

if [[ -z "$API_KEY" ]]; then
    warn "未提供 DashScope API Key，部署完成后请手动修改 ${DEPLOY_DIR}/backend/.env"
fi

info "开始部署 Virtual-Human 到 ${DEPLOY_DIR}，域名: ${DOMAIN}"

# ===================== 安装系统依赖 =====================
info "安装系统依赖..."
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq python3 python3-venv python3-pip nodejs npm nginx git curl \
    build-essential libgl1 libglib2.0-0 || error "安装系统依赖失败"

# 确保 Node.js 版本 >= 18
NODE_MAJOR=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
if [[ "$NODE_MAJOR" -lt 18 ]]; then
    info "Node.js 版本过低，正在升级..."
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
    apt-get install -y -qq nodejs
fi

# ===================== 克隆代码 =====================
if [[ -d "${DEPLOY_DIR}/.git" ]]; then
    info "代码已存在，执行 git pull..."
    cd "${DEPLOY_DIR}"
    git pull origin master || warn "git pull 失败，可能无网络或分支不存在"
else
    info "克隆代码仓库..."
    rm -rf "${DEPLOY_DIR}"
    git clone https://github.com/yunduomenghuale/Virtual-Human.git "${DEPLOY_DIR}" || error "克隆仓库失败"
fi

chown -R "${SERVICE_USER}:${SERVICE_USER}" "${DEPLOY_DIR}"

# ===================== 后端部署 =====================
info "配置后端..."
cd "${DEPLOY_DIR}/backend"

# 创建虚拟环境
if [[ ! -d "venv" ]]; then
    python3 -m venv venv
fi
source venv/bin/activate
pip install -q --upgrade pip
pip install -q -r requirements.txt || error "pip 安装失败"

# 生成 .env
if [[ ! -f ".env" ]]; then
    info "生成 .env 配置文件..."
    SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(50))")
    cat > .env <<EOF
DJANGO_SECRET_KEY=${SECRET_KEY}
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=${DOMAIN},127.0.0.1,localhost

TEXT_LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
TEXT_LLM_API_KEY=${API_KEY}
TEXT_LLM_MODEL=qwen-vl-plus
FAST_LLM_MODEL=qwen-turbo

VISION_LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
VISION_LLM_API_KEY=${API_KEY}
VISION_LLM_MODEL=qwen-vl-plus

EMBEDDING_LOCAL_MODEL=BAAI/bge-small-zh-v1.5
EMBEDDING_MODEL=text-embedding-v3
USE_MOCK_EMBEDDING=False

HF_ENDPOINT=https://hf-mirror.com

BASE_URL=https://${DOMAIN}
WECHAT_WEBHOOK_URL=
EOF
fi

# 数据库迁移
python manage.py migrate --run-syncdb

# 收集静态文件
python manage.py collectstatic --noinput

# 创建超级用户（如果不存在）
DJANGO_SUPERUSER_USERNAME=admin \
DJANGO_SUPERUSER_PASSWORD=admin123456 \
DJANGO_SUPERUSER_EMAIL=admin@${DOMAIN} \
python manage.py createsuperuser --noinput 2>/dev/null || warn "管理员账号可能已存在，默认密码 admin123456"

# ===================== 前端部署 =====================
info "构建前端..."
cd "${DEPLOY_DIR}/frontend"
npm install -q
npm run build || error "前端构建失败"

# 复制到 Django staticfiles
cp -r "${DEPLOY_DIR}/frontend/dist/"* "${DEPLOY_DIR}/backend/staticfiles/"

# ===================== Nginx 配置 =====================
info "配置 Nginx..."
cat > /etc/nginx/sites-available/virtual-human <<EOF
server {
    listen 80;
    server_name ${DOMAIN};

    client_max_body_size 50M;
    proxy_read_timeout 120s;
    proxy_connect_timeout 120s;
    proxy_send_timeout 120s;

    # 前端静态文件
    location / {
        root ${DEPLOY_DIR}/backend/staticfiles;
        try_files \$uri /index.html;
    }

    # Django 静态文件
    location /static/ {
        alias ${DEPLOY_DIR}/backend/staticfiles/;
        expires 7d;
        add_header Cache-Control "public, immutable";
    }

    # 媒体文件
    location /media/ {
        alias ${DEPLOY_DIR}/backend/data/;
        expires 7d;
    }

    # API 代理到 Gunicorn
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    # Admin
    location /admin/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

ln -sf /etc/nginx/sites-available/virtual-human /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t || error "Nginx 配置测试失败"
systemctl restart nginx

# ===================== Gunicorn Systemd 服务 =====================
info "配置 Gunicorn 服务..."
cat > /etc/systemd/system/virtual-human.service <<EOF
[Unit]
Description=Virtual-Human Django Backend
After=network.target

[Service]
User=${SERVICE_USER}
Group=${SERVICE_USER}
WorkingDirectory=${DEPLOY_DIR}/backend
Environment="PATH=${DEPLOY_DIR}/backend/venv/bin"
ExecStart=${DEPLOY_DIR}/backend/venv/bin/gunicorn config.wsgi:application \
    --workers 4 \
    --bind 127.0.0.1:8000 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile -
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable virtual-human
systemctl restart virtual-human

# ===================== 完成 =====================
info "部署完成！"
echo ""
echo "========================================"
echo "  访问地址: http://${DOMAIN}"
echo "  管理后台: http://${DOMAIN}/admin/"
echo "  管理员账号: admin / admin123456"
echo "========================================"
echo ""

if command -v certbot &> /dev/null && [[ -n "${1:-}" ]]; then
    info "检测到域名已配置，建议运行 certbot 自动配置 HTTPS:"
    echo "  certbot --nginx -d ${DOMAIN}"
fi
