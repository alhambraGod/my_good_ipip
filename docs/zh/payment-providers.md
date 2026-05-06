# MindPrism — 支付服务商调研与接入

> **印度**支付市场的决策文档 + 接入规范。配合 `runbook-payments.md`（每个驱动的上线手册）+ `architecture.md §4`（驱动抽象）一起读。

最后审查时间：**2026 年 5 月**。

---

## 1. 印度支付市场（2026 年现状）

UPI 主导印度零售支付（NPCI 公开数据：消费者数字交易**约 80% 量级**为 UPI）。卡是第二，网银 + 钱包紧随。对我们这种 ₹49 的 SaaS 卖给 Gen-Z 白领 / 学生：

| 方式 | 印度电商占比 | 为什么 MindPrism 关注 |
| --- | --- | --- |
| **UPI**（PhonePe / Google Pay / Paytm / BHIM） | ~60% | 零 MDR、即时、Gen-Z 原生、₹49 也能跑 |
| **卡**（RuPay / Visa / Mastercard） | ~15% | OVD 用户、一线城市 |
| **网银** | ~10% | 年长 / 公司账户 |
| **钱包**（Paytm / Mobikwik / Freecharge） | ~7% | 小众，多迁向 UPI |
| **EMI / BNPL** | ~5% | 高客单 — N/A |
| **国际卡** | < 1% | 仅海外印度人 |

**直连 UPI**（无聚合器）几乎免商户费，但有结算 + KYC 运维成本。**聚合器**（Razorpay、Cashfree、PayU、Paytm-PG、PhonePe-PG）取 1–2% MDR，但负责结算、退款、看板、KYC、webhook 投递 — 这就是为什么所有印度 SaaS 都用聚合器。

我们**支持多个聚合器**（每个环境可启用任意一个）+ **直连 UPI Intent**（无聚合器，结算靠你的银行 VPA — 最朴素的支付模式）。

---

## 2. 对比矩阵

| 服务商 | API 风格 | Webhook 方案 | 仅印度 | 上线 KYC | MDR（典型） | UI 模式 | 移动 UPI | 开源 SDK |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| **Razorpay** | REST (Orders + Checkout JS) | HMAC SHA-256 of body | 是 | 个人 PAN | 2%（UPI 由 NPCI 规定 0%，部分套餐仍计服务费） | 页内 modal | ✓ | razorpay-python, razorpay-js |
| **Cashfree** | REST (Orders + JS SDK) | HMAC SHA-256(timestamp + body) | 是 | 个人 PAN | 1.75% | 页内 / 页面 | ✓ | cashfree-pg-sdk-python, cashfree-checkout-js |
| **PayU India** | REST + 表单 POST（旧式 hash） | SHA-512 hash | 是 | 商户 onboarding | 2%（卡 / EMI 更高） | 跳转页（表单 POST） | ✓ | python-payu, payubiz-js |
| **Paytm Payments** | REST (Initiate + JS Checkout) | Checksum (PaytmChecksum) | 是 | 商户 onboarding | 1.99% | 页内 modal | ✓ | paytmchecksum, Paytm_AllInOneSDK |
| **PhonePe Direct** | REST (Standard Checkout) | X-VERIFY checksum | 是 | 商户 onboarding | UPI 0% | 跳转 / QR | ✓（原生） | community wrapper, PhonePe-checkout |
| **UPI Intent**（无聚合器） | `upi://` 深链 / QR | 无（手工对账或银行 webhook） | 是 | 自己 VPA | 0% | 自定义（深链或 QR） | ✓（最佳） | NPCI URL spec |
| **Stripe** | REST (PaymentIntents) + Stripe.js | HMAC SHA-256 | 全球 | 是（Atlas） | 2.9% + ₹2 | 页内 modal | UPI beta | stripe-python, stripe-js |
| **Mock** | n/a | n/a | n/a | n/a | n/a | 跳转 `/payment/success` | n/a | n/a |

> **MDR 注意。** RuPay 借记卡 + UPI 在 ₹2,000 以下消费者商户**官方 0% MDR**。但聚合器仍按笔收便利 / 网关费，UPI 通常 ₹1–2/笔。₹49 实际到账 ₹47–48。

---

## 3. v1 选型评分

按我们具体场景（Gen-Z、₹49 客单、软付费墙、印度本土、转化敏感）加权：

| 标准 | 权重 | Razorpay | Cashfree | PayU | Paytm | PhonePe | UPI Intent | Stripe |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 页内 modal（无跳转） | 4 | ✅ | ✅ | ❌（form POST） | ✅ | ❌（跳转） | ❌ | ✅ |
| onboarding 简单（个人 KYC） | 3 | ✅ | ✅ | 部分 | 部分 | 部分 | ✅（VPA） | ❌（需 Atlas） |
| 移动 UPI 自动填充 | 4 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅（最佳） | 部分 |
| Webhook 文档质量 | 2 | ✅ | ✅ | 部分 | ✅ | 部分 | ❌ | ✅ |
| 免费试 ₹1 测试 | 2 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 退款自动化 | 2 | ✅ | ✅ | ✅ | ✅ | ✅ | 手工 | ✅ |
| **总分** | 17 | **17** | **17** | 11 | 13 | 12 | 11 | 12 |

**决策（2026 年 5 月）：**
- **默认驱动：Razorpay**（页内 UX 最强）
- **可配替代**（运维选哪些启用）：**Cashfree、PayU、UPI Intent、Mock**
- **Stripe**：作为非印度路由的独立路径（海外印度人付 USD），不在 v1 picker
- **Paytm + PhonePe direct**：放到 backlog，等 GMV 上来再向他们谈聚合器级费率

picker UI 只显示 env 中启用的驱动；只装 Razorpay 时与之前完全一致。

---

## 4. 各 Provider 接入笔记

### 4.1 Razorpay（黄金标准 — 已接）

- Orders API：`POST /v1/orders`（HTTP Basic Auth，`key_id:key_secret`）
- Checkout JS：`https://checkout.razorpay.com/v1/checkout.js`
- Verify checkout：`HMAC_SHA256(order_id + "|" + payment_id, key_secret)` 与 `razorpay_signature` 比对
- Webhook：`X-Razorpay-Signature` = `HMAC_SHA256(body, webhook_secret)`
- 处理事件：`order.paid`、`payment.captured`、`payment_link.paid`（旧版）
- 见 `backend/services/payment/razorpay_driver.py` 与 `runbook-payments.md`

### 4.2 Cashfree

- Orders API：`POST https://api.cashfree.com/pg/orders`
  Headers：`x-api-version: 2023-08-01`、`x-client-id`、`x-client-secret`
- JS SDK：`https://sdk.cashfree.com/js/v3/cashfree.js`，用订单返回的 `paymentSessionId` init
- Verify webhook：`HMAC_SHA256(timestamp + raw_body, secret)` base64 编码 — header `x-webhook-signature`、`x-webhook-timestamp`
- 状态查询：`GET /pg/orders/{order_id}` → `order_status` ∈ `{ACTIVE, PAID, EXPIRED}`
- 测试凭证：dashboard "Generate Test Keys"
- 我们用 `httpx + dict` 而不是官方 SDK（避免版本漂移），与 Razorpay 路径一致

### 4.3 PayU India

- "PayU Money" REST：`POST https://test.payu.in/_payment`（UAT）/ `https://secure.payu.in/_payment`（live）；表单编码
- Auth：SHA-512(key|txnid|amount|productinfo|firstname|email|||||||||||salt)
- Verify response：相同 hash 加 status 字段，在重定向回的 URL 上
- Webhook：hash on `salt|status||||||||||email|firstname|productinfo|amount|txnid|key`
- 表单 POST 流程：后端返回预填表单 HTML（或 hash + URL 对），浏览器 POST 到 PayU
- 默认**关闭**；想做跳转式备选时打开

### 4.4 UPI Intent（无聚合器 — 自 VPA）

世界上最简单的支付集成：

- 按 NPCI URL spec 拼深链：
  ```
  upi://pay?
    pa=mindprism@upi&        # 你的 VPA
    pn=MindPrism&             # 显示名
    am=49.00&                 # 金额（INR）
    cu=INR&
    tn=MIND-{assessment_id}&  # 备注
    tr=MIND-{order_id}        # 交易引用
  ```
- 渲染为**可点击链接**（移动端自动唤起 UPI app）+ **PNG QR**（桌面用手机扫）
- **无自动确认。** 用户点 "I paid" → 后端轮询银行 / 聚合器 UPI 订阅 API，或运维手工核对银行流水。v1 前 50 付费用户可接受；超过后切到 Razorpay UPI 自动确认。

### 4.5 Stripe（国际）

- PaymentIntents API + Stripe.js
- 各处都标准；保留 `services/payment_service.py` 作为海外印度人的 legacy shim

### 4.6 Mock

- 永远成功，重定向到 `/payment/success?mock=true`
- v1 dev / CI / staging 默认

---

## 5. 本仓库中的架构

```
backend/services/payment/
├── base.py              ← Protocol + PaymentIntent + ProviderInfo dataclass
├── factory.py           ← get_payment_driver(name=None) — 多驱动注册表
├── mock.py              ← MockDriver
├── razorpay_driver.py   ← RazorpayDriver (Order + Checkout SDK + webhook)
├── cashfree_driver.py   ← CashfreeDriver (Order + JS SDK + webhook)
├── payu_driver.py       ← PayUDriver (form POST + redirect)
├── upi_intent_driver.py ← UPIIntentDriver (deep-link + QR；手工确认)
└── stripe_driver.py     ← (legacy, 保留)
```

运维配置（`env/{dev,prod}.env`）：

```dotenv
PAYMENT_DEFAULT_DRIVER=razorpay
PAYMENT_DRIVERS_ENABLED=razorpay,upi,cashfree,mock   # comma 列表

# 各 provider 凭证：
RAZORPAY_KEY_ID=rzp_live_xxx
RAZORPAY_KEY_SECRET=...
RAZORPAY_WEBHOOK_SECRET=...

CASHFREE_CLIENT_ID=xxx
CASHFREE_CLIENT_SECRET=xxx
CASHFREE_WEBHOOK_SECRET=xxx
CASHFREE_API_BASE=https://api.cashfree.com   # sandbox: https://sandbox.cashfree.com

PAYU_MERCHANT_KEY=xxx
PAYU_MERCHANT_SALT=xxx
PAYU_API_BASE=https://test.payu.in            # live: https://secure.payu.in

UPI_VPA=mindprism@hdfcbank
UPI_DISPLAY_NAME=MindPrism
```

### dev vs prod 付费墙

- `ALLOW_FREE_REPORT`（env，默认 dev=true / prod=false）
- 为 `true` 时，`/api/v3/report/{id}` 即使 `paid=False` 也返回报告，并标 `is_preview=True` 让 UI 加水印
- 为 `false`（prod 默认）时，`/api/v3/report/{id}` 在付费前返回 402

### 前端选择器

- `GET /api/v3/payment/providers` → `[{ id, label, label_hi, description, supports_methods, requires_redirect, recommended }]`
- `<PaymentMethodPicker />` 渲染 chip；用户选一个 → 命中对应驱动 endpoint。默认推荐项实现一键 happy path。

---

## 6. 测试卡 / VPA 参考

| Provider | 测试卡 | 测试 UPI VPA | 测试钱包 |
| --- | --- | --- | --- |
| Razorpay | `4111 1111 1111 1111` (success) / `4111 1111 1111 1112` (fail) | `success@razorpay` / `failure@razorpay` | n/a |
| Cashfree | `4111 1111 1111 1111` | `testsuccess@gocash` / `testfailure@gocash` | n/a |
| PayU India | `5123 4567 8901 2346` (Mastercard) | n/a | `payumoney` |
| Paytm | dashboard 配置 | n/a | dashboard |
| Stripe | `4242 4242 4242 4242` | n/a | n/a |
| UPI Intent | n/a（仅 live VPA） | n/a | n/a |

Sandbox OTP：`1234`（Razorpay）、`123456`（Cashfree）、`123`（PayU）

---

## 7. 合规与运维便签

- **退款 SLA：** Razorpay 5–7 工作日，Cashfree T+5，PayU T+7。在 `/payment/success` 写明，免运维邮件
- **GST 发票：** Razorpay/Cashfree 在公司 KYC 后自动开 GST 发票；之前由运维 PDF 手工
- **PCI-DSS 范围：** 我们代码永不接触卡号 — 聚合器 UI/SDK 处理。我们只看 `payment_id` + 签名，所以 SAQ-A 范围而非 SAQ-D
- **Webhook 幂等性：** 用 `event_id` / `order_id` 做唯一索引；重复 webhook → 200 + 日志
- **Razorpay 朋友 KYC v1 上限：** 累计 GMV 不能超 **₹5L**（Razorpay TOS）。到此前转 Pvt Ltd

---

## 8. 参考（开源 + 官方文档）

- **Razorpay**：
  - <https://razorpay.com/docs/api/orders/>
  - <https://razorpay.com/docs/payments/payment-gateway/web-integration/standard/>
  - SDK：<https://github.com/razorpay/razorpay-python>
- **Cashfree**：
  - <https://docs.cashfree.com/docs/order-create>
  - <https://docs.cashfree.com/docs/web-integration>
  - SDK：<https://github.com/cashfree/cashfree-pg-sdk-python>
- **PayU India**：
  - <https://payu.in/docs>
  - SDK：<https://github.com/payu-intrepos/PaymentSDK-Web>
- **Paytm**：<https://business.paytm.com/docs>
- **PhonePe**：<https://developer.phonepe.com>
- **UPI 深链规范**：
  - <https://www.npci.org.in/PDF/npci/upi/circular/2017/UPI-LinkingSpecsver1.6.pdf>
  - <https://developer.npci.org.in/upi/upi-deep-linking>
- **Stripe**：<https://stripe.com/docs/payments/payment-intents>
