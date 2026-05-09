# Virtual-Human Linux 部署指南

## 一、环境要求

- **OS**: Ubuntu 22.04+ / CentOS 8+ / Debian 12+
- **Python**: 3.11+（sentence-transformers 对 3.12 支持有限，推荐 3.11）
- **Node.js**: 18+（前端构建）
- **Nginx**: 1.18+（反向代理 + 静态文件）
- **Git**: 2.30+

## 二、服务器准备

### 1. 安装系统依赖

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip nodejs npm nginx git
```

### 2. 创建部署目录

```bash
sudo mkdir -p /opt/virtual-human
sudo chown $USER:$USER /opt/virtual-human
cd /opt/virtual-human
git clone https://github.com/yunduomenghuale/Virtual-Human.git .
```

## 三、后端部署

### 1. 创建虚拟环境

```bash
cd /opt/virtual-human/backend
python3 -m venv venv
source venv/bin/activate
```

### 2. 安装依赖

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

> **常见问题**: `sentence-transformers` 首次运行时会下载 `BAAI/bge-small-zh-v1.5` 模型（约 100MB）。国内服务器建议先配置 HuggingFace 镜像：
> ```bash
> export HF_ENDPOINT=https://hf-mirror.com
> ```
> 或在 `.env` 中设置 `HF_ENDPOINT=https://hf-mirror.com`。

### 3. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env，至少修改以下项：
# DJANGO_SECRET_KEY          -> 随机强密码
# DJANGO_DEBUG=False         -> 关闭调试模式
# DJANGO_ALLOWED_HOSTS       -> 你的域名或IP
# TEXT_LLM_API_KEY           -> 阿里云 DashScope API Key
# VISION_LLM_API_KEY         -> 同上（如不单独配置）
# EMBEDDING_API_KEY          -> 同上（如不单独配置）
# BASE_URL                   -> 生产环境域名，如 https://your-domain.com
# WECHAT_WEBHOOK_URL         -> （可选）企业微信机器人
```

### 4. 数据库迁移

```bash
python manage.py migrate
```

### 5. 创建管理员账号

```bash
python manage.py createsuperuser
```

### 6. 收集静态文件

```bash
python manage.py collectstatic --noinput
```

## 四、前端部署

### 1. 构建前端

```bash
cd /opt/virtual-human/frontend
npm install
npm run build
```

### 2. 将前端产物复制到 Django 静态文件目录

```bash
cp -r /opt/virtual-human/frontend/dist/* /opt/virtual-human/backend/staticfiles/
```

> 说明：本项目前端路由使用 history 模式，Django 已配置 fallback，访问根路径时会自动返回 `index.html`。

## 五、Nginx 配置

复制 `nginx.conf.example` 到 Nginx 配置目录：

```bash
sudo cp /opt/virtual-human/nginx.conf.example /etc/nginx/sites-available/virtual-human
sudo ln -sf /etc/nginx/sites-available/virtual-human /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

> 如果使用 HTTPS，建议用 `certbot` 自动配置 SSL：
> ```bash
> sudo apt install -y certbot python3-certbot-nginx
> sudo certbot --nginx -d your-domain.com
> ```

## 六、Gunicorn 服务配置

### 方法一：systemd（推荐）

创建服务文件：

```bash
sudo tee /etc/systemd/system/virtual-human.service > /dev/null << 'EOF'
[Unit]
Description=Virtual-Human Django Backend
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/opt/virtual-human/backend
Environment="PATH=/opt/virtual-human/backend/venv/bin"
ExecStart=/opt/virtual-human/backend/venv/bin/gunicorn config.wsgi:application --workers 4 --bind 127.0.0.1:8000 --timeout 120 --access-logfile - --error-logfile -
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable virtual-human
sudo systemctl start virtual-human
```

### 方法二：Supervisor

```bash
sudo apt install -y supervisor
sudo tee /etc/supervisor/conf.d/virtual-human.conf > /dev/null << 'EOF'
[program:virtual-human]
command=/opt/virtual-human/backend/venv/bin/gunicorn config.wsgi:application --workers 4 --bind 127.0.0.1:8000 --timeout 120
directory=/opt/virtual-human/backend
user=www-data
autostart=true
autorestart=true
stderr_logfile=/var/log/virtual-human.err.log
stdout_logfile=/var/log/virtual-human.out.log
environment=PATH="/opt/virtual-human/backend/venv/bin"
EOF

sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start virtual-human
```

## 七、验证部署

```bash
# 检查 Gunicorn 是否运行
curl http://127.0.0.1:8000/api/auth/login/

# 检查 Nginx 是否正常工作
curl http://your-domain.com/

# 查看日志
sudo journalctl -u virtual-human -f
```

## 八、更新部署

代码更新后执行：

```bash
cd /opt/virtual-human
git pull origin master

# 后端
cd backend
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
sudo systemctl restart virtual-human

# 前端
cd ../frontend
npm install
npm run build
cp -r dist/* ../backend/staticfiles/
```

## 九、常见问题排查

### 1. 静态文件 404

- 确认已执行 `python manage.py collectstatic`
- 确认 Nginx 配置中的 `location /static/` 路径正确
- 确认目录权限：`sudo chown -R www-data:www-data /opt/virtual-human/backend/staticfiles`

### 2. Media 文件上传失败

- 确认目录存在且有写权限：`sudo chown -R www-data:www-data /opt/virtual-human/backend/data`
- 如果通过 Nginx 代理 media，确认 `location /media/` 配置正确

### 3.  sentence-transformers 模型下载慢/失败

- 配置 HuggingFace 镜像：`HF_ENDPOINT=https://hf-mirror.com`
- 或设置 `USE_MOCK_EMBEDDING=True`（仅演示用，会损失 RAG 精度）

### 4. CORS 错误

- 生产环境建议将 `CORS_ALLOW_ALL_ORIGINS = True` 改为只允许特定域名
- 或在 Nginx 层配置 CORS

### 5. 内存不足（小规格服务器）

- Gunicorn workers 数量根据 CPU 核心数调整，一般 `workers = 2 * CPU核心数 + 1`
- 内存 < 2GB 的服务器建议 `workers=2`

### 6. 大模型 API 调用超时

- Gunicorn 默认 timeout 30s，已配置为 120s
- 如果生成报告等长耗时操作仍超时，可继续增大 `--timeout`

## 十、安全建议

1. **修改默认 SECRET_KEY**：生产环境必须使用随机生成的强密码
2. **关闭 DEBUG 模式**：`DJANGO_DEBUG=False`
3. **配置 HTTPS**：使用 certbot 自动申请 Let's Encrypt 证书
4. **限制 ALLOWED_HOSTS**：不要写 `*`，只填写实际域名
5. **定期备份 SQLite 数据库**：`backend/db.sqlite3` 和 `backend/data/` 目录
6. **API Key 保护**：不要在代码仓库中提交真实的 `.env` 文件
