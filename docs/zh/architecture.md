# MindPrism — 系统架构

> 系统设计、运行时拓扑、代码布局，以及关键决策。先读 `product.md` 了解产品目标，再读这份了解工程实现。

```
                ┌──────────────────────────────────────────────┐
                │  Next.js 16（前端）                          │
                │  ─────────────────────                       │
                │  • SSR + ISR + Edge OG（`/api/og/[id]`）     │
                │  • RSC 用于 landing/archetypes；client 组件   │
                │    用于 /test, /payment, /results, /report   │
                │  • i18n via useSyncExternalStore + ls        │
                │  • Razorpay JS SDK（页内 modal）              │
                └────────┬─────────────────────────────────────┘
                         │ JSON over HTTPS
              ┌──────────┴──────────────────────┐
              │  FastAPI（后端）                 │
              │  ─────────────                  │
              │  • /api/v3/assessment/*         │
              │  • /api/v3/payment/* (mock + Razorpay + Cashfree + PayU + UPI) │
              │  • /api/v3/report/* （付费）   │
              │  • /api/v3/archetypes/*         │
              │  • /s/{code} 短链 + /api/share/{id}/og.png stub │
              │  • /api/auth/* (Google / Facebook / WhatsApp /  │
              │     Twitter / Telegram / email)                 │
              └────────┬────────────────┬───────┘
                       │                │
        ┌──────────────┴──┐   ┌─────────┴─────────────┐
        │ SQLAlchemy 2.0  │   │ 多支付驱动注册表       │
        │ + SQLite (dev)  │   │ Razorpay / Cashfree /  │
        │ + MySQL (prod)  │   │ PayU / UPI / Mock     │
        └─────────────────┘   └────────────────────────┘
```

## 1. 仓库布局

```
my_good_ipip/                       （历史仓库名；conda env: my_good_ipip）
│
├── backend/                        FastAPI 应用
│   ├── main.py                     app 工厂、路由挂载、生命周期
│   ├── config.py                   Pydantic Settings（.env）
│   ├── database.py                 引擎、会话、schema 迁移；支持 SQLite + MySQL
│   ├── models.py                   Assessment / UserProfile / ShortLink
│   ├── schemas.py                  Pydantic v2 请求 / 响应模型
│   ├── routers/
│   │   ├── assessment_v3.py        demographic / start / submit / state / results / milestone / attach-profile
│   │   ├── payment_v3.py           providers / price / create-intent / razorpay/order / razorpay/verify / webhook / verify / upi/confirm / webhook/cashfree
│   │   ├── report_v3.py            付费报告 + dev preview 网关
│   │   ├── archetypes.py           公开 list + detail
│   │   ├── share.py                短链重定向 + OG stub
│   │   ├── auth.py                 OAuth (Google/FB/WA/X/TG) + email
│   │   └── assessment.py / payment.py / report.py     # v1 legacy
│   ├── services/
│   │   ├── scoring/                modular: riasec / ocean / holland_code / archetype
│   │   ├── payment/                base.PaymentDriver + Mock + Razorpay + Cashfree + PayU + UPI Intent + factory
│   │   ├── milestone_copy.py       Q10/20/30/40 池（en / hi）
│   │   ├── jwt_service.py          token 签发 + Bearer 依赖
│   │   ├── oauth_service.py        OAuth provider auth-url + code-exchange
│   │   ├── logging_setup.py        TimedRotatingFileHandler 中央日志
│   │   ├── ai_report.py            (legacy) GPT-4o 报告生成
│   │   └── pdf_generator.py        WeasyPrint + Jinja2
│   ├── content/                    24 cells + ~78 careers
│   ├── questions/                  demographic / RIASEC / IPIP / interest pool / selector
│   ├── scripts/
│   │   └── razorpay_sandbox_smoke.py
│   └── tests/                      pytest，197 个，in-memory SQLite
│
├── frontend/                       Next.js 16 + React 19 + Tailwind 4
│   ├── app/                        landing / archetypes / test / results / payment / report / api/og
│   ├── components/                 SiteHeader / SiteFooter / LangToggle / TableOfContents /
│   │                               RazorpayCheckoutButton / PaymentMethodPicker / UPIPayPanel /
│   │                               UnlockAuthModal / Toast / RadarChart
│   ├── lib/
│   │   ├── v3-api.ts               typed v3 fetcher
│   │   ├── razorpay.ts             SDK 懒加载
│   │   ├── i18n/                   strings.ts + LangContext.tsx
│   │   └── hooks/                  useAssessmentProgress / useDigitKey
│   ├── e2e/                        Playwright（smoke + a11y / axe）
│   ├── playwright.config.ts        port 3100
│   ├── lighthouserc.cjs            Lighthouse CI
│   └── vitest.config.ts            happy-dom + Storage polyfill
│
├── nginx/                          nginx.conf + dev/prod conf + _proxy_common.inc
├── deploy/                         一键 docker / native / install_mysql / install_nginx / install_letsencrypt
├── docker-compose.{dev,prod}.yml
├── docs/
│   ├── README.md                   双语文档索引
│   ├── en/                         英文文档
│   ├── zh/                         中文文档
│   └── superpowers/                历史 spec/plan
├── env/                            dev.env / stage.env / prod.env
├── .env.example
└── .github/workflows/ci.yml        pytest matrix + frontend + e2e + lighthouse
```

## 2. 关键数据模型

### `Assessment`（中心表）

| 列 | 用途 |
| --- | --- |
| `id` | UUID 主键 |
| `created_at` | timestamp |
| `demographic` | JSON，Q1-5 答案 |
| `question_set_version` | `"v3_45_hybrid"` |
| `question_ids` | JSON list（用于 `/state` resume） |
| `selection_seed` | 每用户随机种子 |
| `answers` | JSON map `qid → 1..5` |
| `completed` | bool |
| `paid` | bool |
| `riasec_scores` | JSON `{R: int, ...}` |
| `ocean_scores` | JSON `{openness: 0-100, ...}` |
| `ocean_percentiles` | JSON |
| `holland_code` | 3 字母，例如 `"IAC"` |
| `archetype_cell` | 2 字母，例如 `"IA"` |
| `payment_provider` | `mock | razorpay | cashfree | payu | upi | stripe | wechat` |
| `payment_status` | `pending | confirmed | failed | refunded | awaiting_review` |
| `payment_txn_id` | 驱动的 order/intent id |
| `payment_amount_inr` | int |
| `share_code` | 8 字符短链 code |
| `pdf_path` | 可选，WeasyPrint 输出路径 |
| `report_data` | JSON 缓存（含 UPI 用户备注等） |
| `profile_session_token` | 可选 FK，post-login 关联 `UserProfile` |

迁移：`init_db()` 启动时调用 `_ensure_columns()`、`_ensure_indexes()`，方言感知（SQLite PRAGMA / MySQL INFORMATION_SCHEMA）。v1 不引 Alembic；首次非加列变更时引入。

### `UserProfile`

OAuth 身份行；`session_token` 索引（旧版兼容）；`email` 唯一索引。JWT 在 OAuth 回调时签发。

### `ShortLink`

`code → assessment_id + canonical_url`，`clicks` 计数，`created_at`。FK 含 `ON DELETE CASCADE`。

## 3. 题目 + 评分流水线

```
                                                    ┌──────────────────────┐
                                                    │ services/scoring/    │
                                                    ├──────────────────────┤
demographic 答案 (Q1-5) ─┐                          │ riasec.compute_*     │
                          ▼                         │ ocean.compute_*      │
                   questions/selector.py            │ holland_code.compute │
                   _select_45_questions()           │ archetype.derive     │
                          │                         └────────┬─────────────┘
                          │  RIASEC 24（手工挑选 4/类）
                          │  IPIP/interest 16（动态、按 demographic 标签）── 原始得分
                          ▼                                                   ▼
              POST /api/v3/assessment/start  ←—————— 通过 /state 恢复       │
                          │                                                   │
                          ▼                                                   ▼
              POST /api/v3/assessment/submit  ──────────► (likert 1..5) ───► 得分 → cell + holland_code + MAST 触发
                          │
                          ▼
              composed `/results` payload  ─►  cells.get_cell_content + careers.get_careers_for_cell
```

- **确定性。** `selection_seed`（`/start` 处随机 16 字节）驱动 selector 与 milestone 文案；同 seed → 同顺序 / 同鼓励语。便于 debug、A/B 重放、e2e 测试。
- **兼容性。** `services/scoring_legacy.py` 与 `questions/question_bank.py` 是废弃 shim；Phase 5 删除。

## 4. 支付子系统

### 驱动注册表
`services/payment/` 定义 `PaymentDriver` Protocol，5 个方法：`create_payment_intent`、`verify_payment`、`verify_webhook_signature`，外加 Razorpay-only 的 `create_order` + `verify_checkout_signature`。注册表 `DRIVER_FACTORIES` 对每个驱动 lazy 实例化。

| 驱动 | 用于 | 模式 |
| --- | --- | --- |
| `MockDriver` | dev / CI | 永远成功；重定向到 `/payment/success?mock=true` |
| `RazorpayDriver` | test + prod | Order + Checkout SDK（首选）+ 兼容 payment-link |
| `CashfreeDriver` | test + prod | Order + JS SDK |
| `PayUDriver` | test + prod | 表单 POST 重定向 + SHA-512 hash |
| `UPIIntentDriver` | test + prod | NPCI deep link + segno PNG QR；手工对账 |

`get_payment_driver(name=None)` 按 id 选取；`list_provider_infos()` 返回 UI metadata 给前端 picker。

`PAYMENT_DRIVERS_ENABLED` 配置 comma 列表；`PAYMENT_DEFAULT_DRIVER`（或回退 `PAYMENT_MODE`）决定推荐项。

### 前端流程（Razorpay 模式）

```
1. POST /api/v3/payment/create-intent {provider:"razorpay"}
   → { order_id, key_id, amount_paise, client_payload }
2. lib/razorpay.loadRazorpayCheckout()  → 注入 checkout.razorpay.com/v1/checkout.js
3. openRazorpayCheckout({ ... handler })  → 页内 modal，用户支付
4. handler({ order_id, payment_id, sig }) → POST /api/v3/payment/razorpay/verify
5. router.push(/payment/success?...)
6. （独立）Razorpay 推送 payment.captured / order.paid 给 /webhook/razorpay
   后端按 payment_txn_id 匹配并双重确认。
```

### Mock / Cashfree / PayU / UPI 流程

- **Mock**：`payment_url` 直接重定向到 `/payment/success`
- **Cashfree**：返回 `paymentSessionId` + `order_id`，前端用 `cashfree.js` SDK 打开 modal
- **PayU**：返回 `form_url` + `fields`（含 SHA-512 hash），前端构造表单并 POST 到 PayU
- **UPI Intent**：返回 `upi://pay?...` deep link + PNG QR data URL；用户付完点 "I've paid" → `awaiting_review` 状态由运维手工对账确认

### Webhook 事件
- `payment_link.paid`（旧 payment-link 流程）
- `order.paid`（Order 流程）
- `payment.captured`（按 `order_id` 或 `payment_link_id` 匹配）
- Cashfree `PAYMENT_SUCCESS_WEBHOOK` / `ORDER_PAID`
- 未知事件 → 200 + `matched: false`

### 价格
`promo_active = paid_count < PROMO_MAX_REDEMPTIONS`，默认 cap 1000；早鸟价 ₹49，标准价 ₹99，env 驱动。

### dev/prod 付费墙
- `ALLOW_FREE_REPORT`：dev 默认 True（unpaid 也返回 `is_preview=True`），prod 默认 False（402 直到付费）
- `ALLOW_FREE_REPORT=true|false` 显式覆盖

## 5. 认证子系统

| Provider | 规范 |
| --- | --- |
| 邮箱 + 密码 | bcrypt，注册 + 登录 |
| Google OAuth | OAuth 2.0 code flow → `/api/auth/google/callback` |
| Facebook | 同上；`/api/auth/facebook/callback` |
| WhatsApp（Meta） | 同上；`/api/auth/whatsapp/callback` |
| Twitter（X） | OAuth 2.0 PKCE；`/api/auth/twitter/callback` |
| Telegram | login widget 回调（`/api/auth/telegram/callback`） |

每次回调发 JWT。前端把 OAuth 后的下一站路径暂存于 `sessionStorage`（`lib/oauth-return.ts`），所以登录回来落到 `/payment` 而不是 `/profile`。

## 6. 前端渲染模式

| 路由 | 模式 | 原因 |
| --- | --- | --- |
| `/` | RSC + Client islands | 分享链入口首屏要快 |
| `/archetypes` | ISR（10 min） | 内容稳定 |
| `/archetypes/[cell]` | ISR（10 min） | 长尾 SEO |
| `/test` | Client | localStorage、键盘快捷键、IntersectionObserver |
| `/results/[id]` | Client（数据 fetch）+ server `generateMetadata` | per-id OG metadata |
| `/api/og/[id]` | Edge `ImageResponse` | 始终新鲜的分享图 |
| `/payment`, `/report/[id]` | Client | Razorpay SDK + Bearer auth |
| `/sitemap.xml`, `/robots.txt` | Static（10m revalidate） | SEO |

## 7. i18n

- `STRINGS = { en, hi }` 字面量字典在 `lib/i18n/strings.ts`
- `LangProvider` 用 `useSyncExternalStore` over `localStorage`；reload 后语言保持，且永不违反 React 19 `set-state-in-effect` 规则
- `STRINGS["en"]` / `STRINGS["hi"]` 键对齐由 Vitest 测试自动验证
- 内容字段（`label_hi`、`name_hi`）在 `lang === "hi"` 时优先使用；缺失则回退英文（product.md 已说明）

## 8. 测试金字塔

| 层 | 工具 | 数量 | 位置 |
| --- | --- | --- | --- |
| 后端单测 + API | pytest + httpx TestClient + in-memory SQLite + StaticPool | **197** | `backend/tests/` |
| 后端覆盖率门禁 | pytest-cov，`--cov-fail-under=80` | **83.3%** | `.coveragerc` |
| 前端单测（hook + 组件） | Vitest + happy-dom + RTL | **45** | `frontend/lib/**/__tests__`、`components/__tests__`、`app/__tests__` |
| 前端 e2e（smoke） | Playwright + Chromium | **6** | `frontend/e2e/smoke.spec.ts` |
| 前端 a11y | axe-core + Playwright | **4** | `frontend/e2e/a11y.spec.ts` 零 WCAG 2.1 AA 违规 |
| Lighthouse CI | `@lhci/cli`，autorun | a11y ≥ 0.9 强制 | `frontend/lighthouserc.cjs` |
| Razorpay sandbox smoke | live API hitter | 手动 | `backend/scripts/razorpay_sandbox_smoke.py` |

CI matrix 在 `.github/workflows/ci.yml` 跑：backend × {3.11, 3.12} + frontend (lint + Vitest + build) + Playwright e2e + Lighthouse CI（PR 评论）。

## 9. 部署拓扑

详见 `deployment-digitalocean.md`（10/100/1k/10k QPS 四档）。

要点：
- 前端：无状态 Next.js，水平扩展
- 后端：无状态 FastAPI，连接池化的数据库
- 数据库：stage/prod 用 MySQL（`mysql+pymysql://`），dev 默认 SQLite
- 缓存（未来）：Redis / Valkey 在更高 QPS 缓存原型目录与 price 端点
- 对象存储：Spaces (S3-compat) 存 PDF
- Edge / OG：Next.js `/api/og/[id]` 跑在 nodejs；可后期迁到 edge

## 10. 决策账本

| 决策 | 选择 | 原因 | 可逆？ |
| --- | --- | --- | --- |
| 单产品 vs. 双病毒漏斗 | **单产品（MindPrism）** + IBTI 病毒 DNA 在结果页 | 工程成本最低同时保留病毒性 | 是（v2 可拆） |
| 6 类型框架 | Holland 双字母（24 cell） | 24 = 6×4 数学对齐 + 已有内容 | 困难 |
| OCEAN 角色 | 仅个性化、不分类 | 保持 cell 逻辑清洁 | 是 |
| 题目结构 | 5 dem + 24 RIASEC + 16 IPIP/interest = 45 | 信度 α；阶段干净 | 是 |
| 选题 | L1.5：IPIP/interest 动态、RIASEC 静态 | 跨用户可比 + 个性化 | 是 |
| 结果页 | 5 屏滚动、软付费墙 ~6%、3 分享触点 | 病毒 + 转化双优化 | 是 |
| 登录绑定 | 仅"解锁"点击时 | 减少答题 + 浏览摩擦 | 是 |
| 支付 | Razorpay 个人 KYC v1 + 多 driver registry | 自动确认 UX，规避公司注册 | 困难（直到企业 KYC） |
| OAuth | Email + WhatsApp + Google + Facebook（X/Telegram v1 隐藏） | 与印度用户习惯一致 | 是 |
| 视觉风格 | 番红花-绿混血（印度国旗启发） | 科学 + 病毒 + 本土 | 是 |
| i18n | 英语 + Hindi 切换、职业名天城体；4 种南印度语 v2 | v1 甜点 | 是 |
| 前端框架 | Next.js 16（Turbopack）+ React 19 + Tailwind 4 | 服务端 + 客户端 + edge 一套；React 19 新规则采纳 | 困难 |
| 后端框架 | FastAPI + SQLAlchemy 2.0 + Pydantic 2 + SQLite (dev) / MySQL (prod) | 类型安全 + 廉价 + 水平扩展 | 困难 |
| 测试环境 | happy-dom（不是 jsdom） | Node 25 自带的 broken localStorage 与 jsdom 冲突；happy-dom + 内存 polyfill 干净 | 是 |
| 覆盖率门禁 | 80%（后端）+ 零 a11y 违规（前端） | 真实可达；后续提到 90% / Lighthouse perf budget | 是 |

## 11. 已知后续

- [ ] dev SQLite → MySQL 对齐（Docker compose）以便提早发现 schema 漂移
- [ ] 第一次非加列变更前引入 Alembic
- [ ] 把 v1 `/api/assessment/*` 路由替换为 `/api/v3/*`（Phase 3 计划）
- [ ] 删除 `services/scoring_legacy.py` 与 `questions/question_bank.py`
- [ ] 把 OG 图生成迁移到 Edge runtime
- [ ] 给 WeasyPrint 打入天城体字体包，让 PDF 中印地文姓名正确渲染
