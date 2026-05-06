# MindPrism — DigitalOcean 部署

> 在 DigitalOcean 上的四个分级（10 / 100 / 1,000 / 10,000 QPS）。价格来自 [digitalocean.com/pricing](https://www.digitalocean.com/pricing) 2026 年 5 月。所有档位**用同一份代码** — 区别在于多少容器，跑在多少主机，nginx 后面怎么编排。
>
> 容器细节看 `deployment-docker.md`，跨档的 nginx + scale-out 看 `infrastructure.md`。

---

## 0. 容量模型 — 1 QPS 是什么

MindPrism 的热端点成本差异巨大：

| 端点 | 类型 | 热路径 | DB 成本 | 延迟预算 |
| --- | --- | --- | --- | --- |
| `GET /` (landing) | Next ISR HTML | 静态资产 | 0 | ≤ 100ms TTFB |
| `GET /archetypes(/[cell])` | Next ISR | 静态（10 分钟 revalidate） | 0 | ≤ 100ms TTFB |
| `GET /api/v3/archetypes(/...)` | FastAPI 读 | `cells.json` LRU 缓存 | 0 | ≤ 30ms |
| `GET /api/v3/payment/price` | FastAPI 读 | 1 行 count | 1 SELECT | ≤ 30ms |
| `POST /api/v3/assessment/start` | FastAPI 写 | 1 INSERT | 1 INSERT | ≤ 80ms |
| `POST /api/v3/assessment/submit` | FastAPI 写 + 评分 | 评分数学（CPU ~5–15ms） | 1 UPDATE + 1 INSERT | ≤ 200ms |
| `GET /api/v3/assessment/{id}/results` | FastAPI 读 | 1 行 + cell 缓存 | 1 SELECT | ≤ 50ms |
| `POST /api/v3/payment/razorpay/order` | FastAPI 写 + 出站 HTTPS | Razorpay API（300–800ms） | 1 UPDATE | ≤ 1s |
| `POST /api/v3/payment/razorpay/verify` | FastAPI 写 | HMAC | 1 UPDATE | ≤ 50ms |
| `POST /api/v3/payment/webhook/razorpay` | FastAPI 写 | HMAC | 1 UPDATE | ≤ 50ms |
| `GET /api/v3/report/{id}` | FastAPI 读 | 1 行 + cell + 5+ careers | 1 SELECT | ≤ 100ms |
| `GET /s/{code}` | FastAPI 读 + 302 | 1 SELECT + 1 UPDATE | 2 ops | ≤ 30ms |
| `GET /api/og/[id]` | Next nodejs 运行时，回调后端 | 1 后端 GET | 1 SELECT | ≤ 600ms |

容量计算用以下"平均请求结构"：

```
landing/archetypes (CDN + ISR)  60%   ← ~0 后端成本
quiz reads                      20%   ← p95 < 30ms 后端
quiz writes (start + submit)    10%   ← p95 < 200ms 后端
paywall + report                 8%   ← p95 < 100ms 后端
share + OG                       2%   ← p95 < 600ms 或 < 30ms
```

0.5 vCPU 的 1 个 uvicorn worker 大概能扛 75 RPS；2 worker on 1 vCPU → 约 150 RPS 平均结构。

---

## 1. Tier 0 "Bootstrap" — 10 QPS，**≤ $20/月**

**目标：** 周末上线 / 前 50 用户 / 朋友圈分享。单 $12 Droplet 用 Docker 跑**全部** — 同一份 compose 后期可拆。

### 架构

```
                 Cloudflare CDN（免费）
                          │
                          ▼
            ┌─────────────────────────────┐
            │  单 Droplet  s-1vcpu-2gb    │  $12/月
            │  Ubuntu 24.04 + Docker      │
            │                             │
            │  docker-compose.prod.yml    │
            │  ├── nginx :80,443          │
            │  ├── frontend :3000         │
            │  ├── backend  :3001         │
            │  └── (host) MySQL 8         │  ← 通过 deploy/install_mysql_prod.sh
            │                             │
            │  /var/MindPrism/prod/logs/  │  ← bind mount 进容器
            └─────────────────────────────┘
                       │
                       ▼
            ┌─────────────────────────────┐
            │  Spaces (S3 兼容)            │  $5/月（250 GB + 1 TB egress）
            │  PDF 报告 + OG 卡           │
            └─────────────────────────────┘
```

### 价格

| 项目 | 成本 (USD) | 来源 |
| --- | --- | --- |
| Droplet `s-1vcpu-2gb` | **$12** | DO 官价 — 4 容器 + MySQL 最小 RAM |
| 备份（Droplet 20%） | $2.40 | 每周备份，4 周保留 |
| Spaces 对象存储 | $5 | S3 兼容，含 CDN |
| **合计** | **≈ $19.40 / 月** | 在 $20 预算内 |

> **为什么不用 App Platform？** App Platform 最小档（`basic-xxs`）是 $12/月每 service；至少要 2 个，预算就破。Droplet 给我们 4 容器 + 宿主机 MySQL 都装得下，代价是自己升级 OS。

### 一步步部署

```bash
# 全新 Ubuntu 24.04 Droplet（root）
apt-get update -qq && apt-get install -y git docker.io docker-compose-v2

# 1. clone 代码
git clone https://github.com/<your-org>/mindprism.git /opt/mindprism
cd /opt/mindprism

# 2. 装宿主机 MySQL
MYSQL_ROOT_PASSWORD='strong-pwd-here' \
MYSQL_PASSWORD='another-strong-pwd' \
sudo bash deploy/install_mysql_prod.sh

# 3. 编辑 env/prod.env（粘贴上一步打印的 DATABASE_URL，加 FRONTEND_URL、API_PUBLIC_URL、NEXT_PUBLIC_*、RAZORPAY_*、JWT_SECRET）
nano env/prod.env

# 4. 启动
sudo bash deploy/start_docker.sh prod

# 5. 验证
curl -I http://localhost            # 通过 nginx → frontend → 200
curl -s http://localhost/api/health # → {"status":"ok",...}
```

### 容量校验
- nginx + frontend + backend 在 1 vCPU / 2 GB；后端 `gunicorn -w 2` → ~150 RPS 平均
- 10 QPS 目标 = 7% 利用率，留巨大余量
- 同机 MySQL：8.0 InnoDB 默认设置扛 500+ TPS，50× 余量
- 内存预算：nginx 30MB + frontend 250MB + backend 200MB + MySQL 350MB ≈ 830MB，1.2GB 留给 OS/page cache

### 运维
- **备份：** DO 镜像级备份 + 夜间 cron 跑 `mysqldump > /var/MindPrism/prod/logs/db-$(date).sql.gz`
- **监控：** 免费 DO Monitoring + Uptime check；CPU > 75% / 磁盘 > 80% / 5xx > 1% 报警
- **TLS：** `sudo bash deploy/install_letsencrypt.sh www.mindprism.in` 一键

---

## 2. Tier 1 "Launch" — 100 QPS，约 5,000 日完成

### 增量

- Droplet 升 **`s-2vcpu-4gb` ($24)** 拿 2 vCPU
- **同 Droplet 横向 scale**：`bash deploy/scale.sh prod backend=2 frontend=2` — nginx 通过 docker DNS round-robin，无需改 nginx 配置

### 价格

| 项目 | $ |
| --- | --- |
| Droplet `s-2vcpu-4gb` | $24 |
| 备份 (20%) | $4.80 |
| Spaces 250 GB | $5 |
| **合计** | **≈ $33.80 / 月** |

### 容量
- 4 后端 worker → ~600 RPS
- 100 QPS = 17% 利用率

---

## 3. Tier 2 "Growth" — 1,000 QPS，约 100,000 日完成

### 架构

```
                       Cloudflare CDN
                             │
                             ▼
                    ┌────────────────┐
                    │ DO Load Balancer│  $12/月
                    └───────┬────────┘
                            │
          ┌─────────────────┼─────────────────┐
          ▼                                   ▼
┌─────────────────────┐               ┌─────────────────────┐
│ Droplet s-2vcpu-4gb │               │ Droplet s-2vcpu-4gb │
│ frontend × 2        │               │ frontend × 2        │
│ backend × 2         │               │ backend × 2         │
│ nginx (内网)        │               │ nginx (内网)        │
│ ($24/月)            │               │ ($24/月)            │
└─────────────────────┘               └──────────┬──────────┘
                                                 │
                                  ┌──────────────┼──────────────┐
                                  ▼                             ▼
                       ┌──────────────────┐          ┌──────────────────┐
                       │ Managed MySQL    │          │ Managed Valkey   │
                       │ Production tier  │          │ (Redis 兼容)     │
                       │ 4 GB / 2 vCPU /  │          │ 1 GB / 1 vCPU    │
                       │ 38 GB / standby  │          │ ($30/月)         │
                       │ ($120/月)        │          └──────────────────┘
                       └──────────────────┘
                       ┌──────────────────┐
                       │ Spaces 1 TB      │  $25/月
                       └──────────────────┘
```

### 价格

| 项目 | $ |
| --- | --- |
| 2× Droplet `s-2vcpu-4gb` | $48 |
| DO Load Balancer | $12 |
| Managed MySQL production w/ standby | $120 |
| Managed Valkey 1 GB | $30 |
| Spaces 1 TB | $25 |
| 带宽溢出（约 1 TB/月，$0.01/GB） | ~$50 |
| **合计** | **≈ $285 / 月** |

### 缓存策略

| Key | TTL | 真相源 |
| --- | --- | --- |
| `archetypes:list` | 10 min | `content/cells.py` LRU + Valkey |
| `archetypes:detail:{cell}` | 10 min | 同上 |
| `payment:price` | 30 s | `_current_price()` |
| `careers:for_cell:{cell}` | 10 min | `careers.py` LRU |
| `ratelimit:{ip}:{minute}` | 60 s | counter |

---

## 4. Tier 3 "Scale" — 10,000 QPS，约 1M 日完成

### 架构

```
                        Cloudflare Enterprise（付费）
                            │ TLS + DDoS + WAF + 图像缩放
                            ▼
                    ┌──────────────────┐
                    │ Global LB（DO）  │   3 region: BLR1 / SGP1 / FRA1
                    └──┬───────────────┘
                       │
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
   ┌────────┐    ┌────────┐    ┌────────┐
   │ DOKS   │    │ DOKS   │    │ DOKS   │   托管 Kubernetes，每 region 一个集群
   │ BLR1   │    │ SGP1   │    │ FRA1   │
   │ active │    │ active │    │ passive│
   │ 6×4vCPU│    │ 6×4vCPU│    │ 6×4vCPU│
   │ 8GB    │    │ 8GB    │    │ 8GB    │
   └────────┘    └────────┘    └────────┘
   每集群跑：
     - Next.js Deployment ×8（HPA 4–16）
     - FastAPI Deployment ×8（HPA 4–24）
     - Valkey StatefulSet 3 节点 sentinel
     - Nginx ingress 带限速注解
     - Prometheus + Grafana

   共享：
     - DO Managed MySQL production-xl-2tb / 8 vCPU / 32 GB / 每 region 只读副本
     - DO Spaces 5 TB + CDN
     - DO Container Registry
```

### 容量
- 48 后端 worker × ~150 RPS = ~7,200 RPS BLR1；SGP1 active 加 50% = ~10,800 RPS — 8% 余量

### 价格

| 项目 | $/月 |
| --- | --- |
| DOKS 控制面 | 0 |
| Worker — BLR1 (4 vCPU/8 GB × 6) | $384 |
| Worker — SGP1 × 6 | $384 |
| Worker — FRA1 × 6 (passive) | $384 |
| Managed MySQL production-xl 8vCPU/32GB/200GB w/ standby | $570 |
| 只读副本 × 2 | $1,140 |
| Managed Valkey 4GB w/ standby | $90 |
| Global LB | $36 |
| Spaces 5 TB + CDN | $50 |
| 带宽溢出（30 TB/月） | $300 |
| Cloudflare Enterprise | ~$2,000+ |
| Container Registry | $5 |
| **DO 子合计** | **≈ $3,343 / 月** |
| **总计（含 CF Ent.）** | **≈ $5,300+ / 月** |

---

## 5. 成本梯度汇总

| 档位 | 日完成 | QPS 峰值 | 月费 | 上手时间 |
| --- | --- | --- | --- | --- |
| Bootstrap | 500 | 10 | **≤ $20** | ~30 min |
| Launch | 5,000 | 100 | $34 | ~2 小时 |
| Growth | 100,000 | 1,000 | $285 | ~1 天 |
| Scale | 1,000,000 | 10,000 | $3,343 (DO) + $2,000+ (CF) | ~1 周 + 2 周 soak |

价格源：[DigitalOcean 公开定价](https://www.digitalocean.com/pricing)。

---

## 6. 上线前检查清单（任意档位）

- [ ] `env/prod.env` 已填，且**绝不**提交（已 gitignore）
- [ ] `RAZORPAY_KEY_ID` 是 `rzp_live_*`，webhook secret 已轮换
- [ ] `JWT_SECRET` 是长随机串，**不**用 dev 默认
- [ ] `OAUTH_STATE_SECRET` 已设
- [ ] CORS 仅允许 `FRONTEND_URL`（不放 `*`）
- [ ] DO Spaces 公开读策略仅 `*.pdf` 文件夹
- [ ] Cloudflare 缓存规则：`/api/*` bypass、`/static/*` 1h、`/api/og/*` 5m
- [ ] DO Monitoring 报警：CPU>80% / RAM>85% / 5xx>1%
- [ ] Razorpay sandbox smoke 通过（`python -m scripts.razorpay_sandbox_smoke`）
- [ ] CI 全绿
- [ ] Lighthouse a11y ≥ 0.9（error）
- [ ] `/var/MindPrism/prod/logs/` 可写 + 夜间归档 cron
