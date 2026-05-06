# MindPrism — 基础设施与水平扩展

> nginx、前端池、后端池怎么拼在一起 — 以及如何把每个池从 1 → N，无需重写。配合 `deployment-digitalocean.md`（不同档位的成本配方）和 `deployment-docker.md`（容器细节）一起读。

---

## 1. 拓扑

```
                                ┌────────────────────────┐
                                │  Cloudflare（免费 CDN）│
                                └───────────┬────────────┘
                                            │ TLS 在边缘终结
                                            ▼
                              ┌──────────────────────────┐
                              │  nginx（每台主机 1 个）    │
                              │  /etc/nginx/nginx.conf   │
                              │  conf.d/mindprism.*.conf │
                              └──────────┬────────┬──────┘
                                         │        │
              upstream mindprism_frontend│        │upstream mindprism_backend
                                         │        │
              ┌──────────────────────────┘        └──────────────────────────┐
              │                                                              │
   ┌──────────┴──────────┐                                          ┌────────┴───────────┐
   │  Next.js × N        │                                          │  FastAPI × M       │
   │  （3000 端口）       │                                          │  gunicorn 2 worker │
   │  静态资产 +          │                                          │  /api/v3/*         │
   │  /api/og/[id]       │                                          │  /s/{code}         │
   └─────────────────────┘                                          └─────────┬──────────┘
                                                                              │
                                                            mysql+pymysql DSN │
                                                                              ▼
                                                              ┌───────────────────────┐
                                                              │  MySQL 8              │
                                                              │  dev：容器内          │
                                                              │  prod：宿主进程       │
                                                              │  growth：托管 DB      │
                                                              └───────────────────────┘
```

**关键不变量。** 前端与后端都**无状态**；磁盘上只有日志。任何需要跨请求存活的状态都在 MySQL（高级别再加 Valkey）。这就是为什么我们能"再多 4 个后端 pod"而不影响其他部分。

---

## 2. nginx 配置 — 每个 block 的作用

`nginx/` 三个文件**跨档位完全相同** — 只有 upstream 池变化：

```
nginx/
├── nginx.conf                      ← 全局：worker、gzip、log_format、限速 zone、cache 库
└── conf.d/
    ├── _proxy_common.inc           ← 共享 `proxy_set_header`、超时、`proxy_next_upstream` 重试
    ├── mindprism.dev.conf          ← dev 站：/api/* → backend、/ → frontend
    └── mindprism.prod.conf         ← prod 站：+ HTTPS + CSP + LE 证书
```

prod 比 dev 多了：
- `:443 ssl http2` server，Let's Encrypt 证书路径
- HSTS、CSP（Razorpay 兼容）、Permissions-Policy 头
- HTTP→HTTPS 重定向
- `/docs` Swagger UI 返回 404
- 支付 webhook 不限速

### 热路径

| 路径模式 | upstream | 特殊处理 |
| --- | --- | --- |
| `/api/v3/payment/webhook/razorpay` | backend | **不限速**（已签名） |
| `/api/v3/payment/*`、`/api/v3/auth/*`、`/api/auth/*` | backend | `pay_zone` (5 r/s, burst 10) |
| `/api/*`（默认） | backend | `api_zone` (30 r/s, burst 60) |
| `/s/{code}` | backend | `api_zone` |
| `/api/og/{id}` | frontend（Next route） | nginx 缓存 5 分钟，`proxy_cache_lock` |
| `/_next/static`、`/favicon.ico`、`/robots.txt`、`/sitemap.xml` | frontend | nginx 缓存 1 天，`Cache-Control: immutable` |
| `/` 与其他 | frontend | 直通 |

---

## 3. 三级扩展

### A. 同主机加副本（1 host，更多 replica）

延迟一上来，**第一件事**做这个。零 nginx 配置改动 — Docker Compose 内置 DNS 会 round-robin 解析 service name。

```bash
# 同主机加 backend 副本：
sudo bash deploy/scale.sh prod backend=3
docker compose -f docker-compose.prod.yml ps
```

容量：1 vCPU 主机 → 约 150 RPS（`backend=2`）。`s-2vcpu-4gb` ($24/月) 的 `backend=4` 翻倍到约 600 RPS。

### B. 多主机（multi-Droplet）

单 Droplet 饱和后。新开 Droplet **只**跑 backend container（无 nginx、无 frontend），把它们的内网 IP 加到 nginx upstream。务必用 DigitalOcean VPC 或 Tailscale 做内网网格 — backend `:3001` 不应公网暴露。

```nginx
# nginx/conf.d/mindprism.prod.conf
upstream mindprism_backend {
    least_conn;
    server backend:3001 max_fails=3 fail_timeout=15s;     # 本机容器
    server 10.114.0.11:3001 max_fails=3 fail_timeout=15s; # 第 2 台 Droplet
    server 10.114.0.12:3001 max_fails=3 fail_timeout=15s; # 第 3 台
    server 10.114.0.13:3001 backup;                       # 冷备
    keepalive 64;
}
```

`nginx -s reload`（无中断 — 老 worker drain）。

### C. 多 region（区域 active-active）

单 region 长尾延迟开始痛。DO Global LB 在前；每个 region 跑自己的 DOKS 集群（或 Droplet 池）。DB 层：BLR1 主 + SGP1 只读副本。Razorpay webhook 只指向单 region（BLR1），避免重复确认竞争。

这是 **Tier 3**，详见 `deployment-digitalocean.md`。

---

## 4. 大规模日志

每个容器写 `/var/MindPrism/<env>/logs/` 通过宿主机 bind mount。`services/logging_setup.py`：

- 每流一个文件（`app.log`、`error.log`、`access.log`）
- 旋转：午夜（`TimedRotatingFileHandler when=midnight`）
- 归档到 `logs/history/app.log.YYYY-MM-DD`
- `LOG_RETENTION_DAYS=30` 后自动删除

超过 1 主机时，把日志运到中央存储。两种路径：

| 路径 | 成本 | 评判 |
| --- | --- | --- |
| **DO Monitoring + Logtail** | $0.20 / GB ingest | 最简单，journald 或 filebeat 一行接入 |
| **自建 Loki + Promtail** | 自维护 | 控制力强，运维成本高 |

无论哪条路，每主机的文件 rotate 给你 2 天本地窗口，就算运输坏了也能查。

---

## 5. 常见 scale-out 错误（与解法）

| 错误 | 危害 | 解法 |
| --- | --- | --- |
| 把 JWT 黑名单存内存 | A 副本看不到 B 副本的登出 | 移到 Valkey / 托管缓存 |
| Razorpay order 在 A 创建，verify 命中 B | 我们 verify 路径用 `payment_txn_id` 查 assessment，**不**严格需要粘性；但限速计数器需要 | DO LB sticky-cookie 配 `/api/v3/payment/`；或把限速计数器移到 Valkey |
| nginx `proxy_pass` 用裸 IP，无 DNS TTL | Compose IP 在 `down/up` 后会变 | 用 service name (`backend:3001`)，nginx 自动重新解析 |
| 两个副本写同一个 log 文件 | 行交错 | 我们 bind-mount `/var/MindPrism/$ENV → /var/MindPrism/$ENV` 让每容器有自己 pid；日志同一文件但 `[svc-name]` 标签由 logging_setup 注入。聚合器按 `(host, container_id, ts)` 去重 |
| 多主机 LE 续期 | 只有 LB 主机能回 ACME challenge | certbot 跑在 LB 主机，证书复制到其他主机；或改用 DNS-01 |

---

## 6. 健康检查 + 就绪

| 端点 | 作用 |
| --- | --- |
| `GET /api/health`（backend） | 返回 `{status:"ok",service:"mindprism"}` — docker / nginx 健康检查使用 |
| `HEAD /`（frontend） | 200 = 就绪 |
| `GET /` 通过 nginx | 端到端检查 |

Docker compose 携带：
- `backend.healthcheck` → `curl /api/health`，30s 间隔
- `frontend.healthcheck` → `wget /`，30s 间隔
- `mysql.healthcheck` → `mysqladmin ping`，5s 间隔，20 retries

副本失败健康检查时，nginx 的 `max_fails=3 fail_timeout=15s` 会把它从池中拿掉，直到下个健康窗口。
