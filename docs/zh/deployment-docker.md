# MindPrism — 容器部署指南

Docker（推荐）+ 原生（无 Docker）两种路径，dev / prod 双环境。

> 配合 `deployment-digitalocean.md`（成本档位）、`infrastructure.md`（nginx scale-out）、`runbook-payments.md`（Razorpay 上线）一起读。

---

## 0. 共用目录布局（Docker / 原生通用）

| 宿主路径 | 用途 |
| --- | --- |
| `/var/MindPrism/dev/logs/` | dev 当天日志（`app.log`、`access.log`、`error.log`） |
| `/var/MindPrism/dev/logs/history/` | 旋转归档，后缀 `app.log.YYYY-MM-DD` |
| `/var/MindPrism/dev/logs/nginx/` | nginx access + error 日志（Docker 时） |
| `/var/MindPrism/prod/logs/...` | prod 同上 |
| `/etc/nginx/conf.d/` | nginx 配置（原生部署） |
| `/etc/letsencrypt/` | LE 证书（prod TLS） |

日志由 FastAPI 通过 `services/logging_setup.py` 输出。午夜旋转，30 天保留（`LOG_RETENTION_DAYS`）。

---

## 1. Docker — dev

`docker-compose.dev.yml` 在私有网络 `mindprism-dev` 上拉起 4 个容器：

| 服务 | 镜像 | 端口 | 备注 |
| --- | --- | --- | --- |
| **mysql**    | mysql:8.0           | 127.0.0.1:3307 | 密码 `mindprism_dev`；数据卷 `mindprism-dev-mysql` |
| **backend**  | mindprism-backend:dev | 127.0.0.1:3001 | gunicorn 2 worker；FastAPI |
| **frontend** | mindprism-frontend:dev | 127.0.0.1:3000 | next start（生产构建） |
| **nginx**    | nginx:1.27-alpine   | 80             | 反向代理 + 缓存 + 限速 |

### 启动

```bash
git clone <repo> mindprism && cd mindprism
sudo bash deploy/start_docker.sh dev
# 等 healthcheck 全绿
curl -I http://localhost                 # 200 → 通过 nginx 到 frontend
curl  http://localhost/api/health        # {"status":"ok",...}
```

### 关闭

```bash
sudo bash deploy/stop_docker.sh dev               # 停服务，保留数据卷
sudo bash deploy/stop_docker.sh dev --volumes     # 同时清空 mysql 数据
```

### 排查

```bash
docker compose -f docker-compose.dev.yml logs -f backend
docker compose -f docker-compose.dev.yml exec mysql mysql -uroot -p
sudo tail -f /var/MindPrism/dev/logs/app.log
```

---

## 2. Docker — prod

`docker-compose.prod.yml` **只**跑 nginx + frontend + backend。MySQL 在宿主机（通过 `deploy/install_mysql_prod.sh` 安装），通过 `host.docker.internal` 访问（Linux 20.10+ 支持，需 compose `extra_hosts: host.docker.internal:host-gateway`）。

### 一次性主机准备

```bash
# 1. 装宿主 MySQL
MYSQL_ROOT_PASSWORD='strong-pwd' \
MYSQL_PASSWORD='another-strong-pwd' \
sudo bash deploy/install_mysql_prod.sh
# （打印 DATABASE_URL，粘进 env/prod.env）

# 2. 编辑 env/prod.env (DATABASE_URL、RAZORPAY_*、JWT_SECRET 等)
nano env/prod.env

# 3. （可选）签 TLS 证书
sudo bash deploy/install_letsencrypt.sh www.mindprism.in
```

### 启动 + 扩展

```bash
sudo bash deploy/start_docker.sh prod                        # 初始 1×1
sudo bash deploy/scale.sh        prod backend=3 frontend=2   # 扩展副本
docker compose -f docker-compose.prod.yml ps
```

`nginx` 在 scale 后**不需要 reload** — Docker Compose 的 DNS 在每次解析时返回当前所有副本，nginx 配置用主机名（`server backend:3001`）而非固定 IP，所以新副本自动进池。

### 无中断升级

```bash
git pull
sudo bash deploy/start_docker.sh prod --build       # 重建镜像
docker compose -f docker-compose.prod.yml up -d --no-deps backend frontend
```

Compose 默认 `restart: unless-stopped` + nginx upstream `max_fails=3 fail_timeout=15s` 给出平滑滚动重启。

---

## 3. 原生 — dev

无 Docker 的笔记本场景：

```bash
# 需要：Python 3.11、Node 20+、可选宿主机 MySQL 8
bash deploy/start_native.sh dev
# 没有 MySQL 时回退到 sqlite:///./mindprism_dev.db
# （提前设 DATABASE_URL 指向 MySQL 也行）
```

原生 start 脚本**不**跑 nginx；前端通过 `NEXT_PUBLIC_API_URL` 直接连后端。

需要"更接近 prod"的体验：

```bash
sudo bash deploy/install_nginx.sh dev
sudo systemctl reload nginx
```

---

## 4. 原生 — prod

如果已有主机（如 Ubuntu Droplet）想要裸金属性能 / 可观测性。等同 Docker prod，只是没有 Docker。

```bash
# 1. 装宿主 MySQL
sudo bash deploy/install_mysql_prod.sh

# 2. 装 nginx + 拷贝配置
sudo bash deploy/install_nginx.sh prod

# 3. 启动后端 + 前端（前台；真实 prod 用 systemd）
bash deploy/start_native.sh prod
```

### systemd 集成（推荐 prod-native）

`/etc/systemd/system/mindprism-backend.service`：

```ini
[Unit]
Description=MindPrism backend (FastAPI)
After=network.target mysql.service
Wants=mysql.service

[Service]
Type=simple
User=mindprism
WorkingDirectory=/opt/mindprism/backend
EnvironmentFile=/opt/mindprism/backend/.env
ExecStart=/opt/mindprism/.venv/bin/gunicorn main:app \
  --bind 0.0.0.0:3001 \
  --workers ${GUNICORN_WORKERS} \
  --worker-class uvicorn.workers.UvicornWorker \
  --timeout 60 --keep-alive 5 \
  --access-logfile - --error-logfile -
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

`/etc/systemd/system/mindprism-frontend.service`：

```ini
[Unit]
Description=MindPrism frontend (Next.js)
After=network.target

[Service]
Type=simple
User=mindprism
WorkingDirectory=/opt/mindprism/frontend
EnvironmentFile=/opt/mindprism/frontend/.env.local
ExecStart=/usr/bin/npm run start
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

启用：

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now mindprism-backend mindprism-frontend
```

---

## 5. 环境变量（完整）

| 变量 | 层级 | 默认 | 用途 |
| --- | --- | --- | --- |
| `APP_ENV` | core | `dev` | `dev` / `stage` / `prod` |
| `DATABASE_URL` | core | sqlite | SQLAlchemy URL；prod 用 `mysql+pymysql://...` |
| `LOG_ROOT` | core | `/var/MindPrism` | 日志根目录 |
| `LOG_RETENTION_DAYS` | core | `30` | 历史归档保留天数 |
| `FRONTEND_URL` | core | `http://localhost:3000` | CORS 白名单 + 回调宿主 |
| `API_PUBLIC_URL` | core | `http://localhost:3001` | `/s/{code}` 短链解析的目标 |
| `JWT_SECRET` | core | dev 默认 | **prod 必须覆盖** |
| `OAUTH_STATE_SECRET` | core | 空 | Twitter/Telegram CSRF |
| `PAYMENT_MODE` | payment | `mock` | 单驱动后兼容；可选 `razorpay` |
| `PAYMENT_DEFAULT_DRIVER` | payment | 空 | 多驱动模式下推荐项 |
| `PAYMENT_DRIVERS_ENABLED` | payment | 空 | comma 列表，例如 `razorpay,upi,cashfree,mock` |
| `RAZORPAY_KEY_ID` / `_SECRET` / `_WEBHOOK_SECRET` | payment | 空 | Razorpay 凭证 |
| `CASHFREE_CLIENT_ID` / `_SECRET` / `_WEBHOOK_SECRET` / `_API_BASE` | payment | 空 / sandbox URL | Cashfree 凭证 |
| `PAYU_MERCHANT_KEY` / `_SALT` / `_API_BASE` | payment | 空 / 测试 URL | PayU 凭证 |
| `UPI_VPA` / `UPI_DISPLAY_NAME` | payment | 空 / "MindPrism" | 直接 UPI 直链 |
| `ALLOW_FREE_REPORT` | paywall | dev=true / prod=false | dev 看预览，prod 强制付费 |
| `PROMO_MAX_REDEMPTIONS` | pricing | 1000 | 早鸟名额 cap |
| `PRICE_FULL_INR` / `PRICE_PROMO_INR` | pricing | 99 / 49 | 显示价 |
| `GOOGLE_CLIENT_ID` / `_SECRET` | auth | 空 | Google OAuth |
| `META_APP_ID` / `_SECRET` | auth | 空 | WhatsApp OAuth |
| `FACEBOOK_APP_ID` / `_SECRET` | auth | 空 | Facebook OAuth |
| `NEXT_PUBLIC_API_URL` | frontend | `http://localhost:3001` | 浏览器侧 API 基础 URL |
| `NEXT_PUBLIC_SITE_URL` | frontend | `http://localhost:3000` | OG metadata + sitemap |

中央源文件：`env/dev.env` + `env/prod.env`。部署脚本读这俩生成 `backend/.env` 与 `frontend/.env.local`。

---

## 6. 镜像构建矩阵

| 镜像 | 基础 | 大小（压缩） | 层 |
| --- | --- | --- | --- |
| `mindprism-backend` | python:3.11-slim | ~280 MB | apt + pip + app |
| `mindprism-frontend` | node:20-alpine | ~200 MB | deps → builder → runtime（多阶段） |
| `nginx` | nginx:1.27-alpine | 23 MB | 上游镜像 |
| `mysql` (dev only) | mysql:8.0 | 600 MB | 上游镜像 |

CLI 上可传 build 参数：

```bash
docker compose -f docker-compose.prod.yml build \
  --build-arg NEXT_PUBLIC_API_URL=https://api.mindprism.in \
  --build-arg NEXT_PUBLIC_SITE_URL=https://mindprism.in
```

---

## 7. 备份 + 恢复

### MySQL — dev（容器内）

```bash
# Dump
docker compose -f docker-compose.dev.yml exec mysql \
  mysqldump -uroot -pmindprism_dev mindprism_dev | gzip \
  > /var/MindPrism/dev/logs/db-$(date +%F).sql.gz

# Restore
gunzip -c db-2026-05-06.sql.gz | docker compose -f docker-compose.dev.yml exec -T mysql \
  mysql -uroot -pmindprism_dev mindprism_dev
```

### MySQL — prod（宿主机）

```bash
mysqldump -u mindprism -p mindprism_prod | gzip \
  > /var/MindPrism/prod/logs/db-$(date +%F).sql.gz
```

cron 定时：

```cron
# /etc/cron.d/mindprism-mysqldump
0 2 * * *   mindprism   mysqldump -u mindprism -p"$MYSQL_PASSWORD" mindprism_prod | gzip > /var/MindPrism/prod/logs/history/db-$(date +\%F).sql.gz
0 3 * * *   mindprism   find /var/MindPrism/prod/logs/history -name 'db-*.sql.gz' -mtime +30 -delete
```

---

## 8. 故障排查

| 现象 | 可能原因 | 修复 |
| --- | --- | --- |
| `host.docker.internal` 在容器中无法解析 | Docker 太老 / 非 Linux | 加 `--add-host=host.docker.internal:host-gateway`；macOS 自动 |
| `MySQL 1130: Host '...' is not allowed to connect` | bind-address 仅 `127.0.0.1` | `MYSQL_BIND_HOST=0.0.0.0` 重跑 install（仅在防火墙背后） |
| `nginx: bind() to 0.0.0.0:80 failed` | 宿主 nginx 已在跑 | `sudo systemctl stop nginx` 后再 `start_docker.sh` |
| 后端日志缺失 | `LOG_ROOT` 容器内不可写 | 确认 bind mount：`/var/MindPrism/$ENV` 存在且 `chmod 0775` |
| `502 Bad Gateway` 在 / | frontend / backend 之一不健康 | `docker compose ps`；`docker compose logs <svc>` |
| Razorpay verify 失败但签名规则匹配 | `RAZORPAY_KEY_SECRET` 在副本间不一致 | 确认所有 backend 副本读同一份 env |
| Letsencrypt 续期失败 | 80 端口不可达 / DNS 未指向 | `nslookup mindprism.in` + `ufw status` |
