# Razorpay 上线手册 / Runbook

把 MindPrism 的支付从 `mock` 推到真实 **test** 账户，再推到 **live** 的端到端 checklist。

> **范围：** 开发笔记本验证。上 prod（真实运营）需要在已注册的印度实体 / KYC 个人下面注册 Razorpay 账户。v1 用印度朋友个人 KYC；v2 应迁到 Pvt Ltd。

---

## 0. 前置

- 一个 Razorpay 账户（**test** 模式只需印度手机 + PAN）
- 后端在本地（FastAPI 跑 `:3001`）+ 前端（`:3000`）
- 公网隧道（`ngrok`、`cloudflared` 等）来收 webhook 真实事件

---

## 1. 拿测试凭证

1. Razorpay Dashboard → 右上 toggle 切 **Test Mode**
2. Settings → **API Keys** → **Generate Test Key**
3. 复制 `Key Id`（`rzp_test_` 开头）和 `Key Secret`
4. Settings → **Webhooks** → **Add New Webhook**
   - URL：`https://<your-ngrok>.app/api/v3/payment/webhook/razorpay`
   - 启用事件：`payment.captured`、`order.paid`、`payment_link.paid`
   - Webhook secret：任意随机字符串 — **同一个值写到下面 `RAZORPAY_WEBHOOK_SECRET`**

---

## 2. 本地 env

把以下追加到 `env/dev.env`（或你 `deploy_backend.sh` 读的那个）：

```dotenv
PAYMENT_MODE=razorpay
RAZORPAY_KEY_ID=rzp_test_xxxxxxxxxxxxxx
RAZORPAY_KEY_SECRET=xxxxxxxxxxxxxxxxxxxxxxxx
RAZORPAY_WEBHOOK_SECRET=whatever-you-saved-above
```

> 重新跑 `bash backend/deploy_backend.sh dev` 重新生成 `backend/.env`；重启 uvicorn。

---

## 3. Sandbox smoke（无 DB、无 UI）

不碰本地 FastAPI 验证凭证 + 签名逻辑：

```bash
cd backend
conda activate my_good_ipip
PAYMENT_MODE=razorpay \
RAZORPAY_KEY_ID=rzp_test_xxxxx \
RAZORPAY_KEY_SECRET=xxxxx \
python -m scripts.razorpay_sandbox_smoke
```

期望输出：

```
➜ Razorpay sandbox smoke
[1/3] Creating sandbox Order…   ok
[2/3] Verifying that the HMAC signing rule round-trips…   ok
[3/3] Sanity-check webhook signature helper…   ok
```

如果 **HTTP 401** key 不对；**HTTP 400** 看 `RZP_SMOKE_AMOUNT_INR` 是否拼错。

---

## 4. 端到端走 UI

1. `bash start_all.sh dev`
2. 另一窗口：暴露后端
   ```bash
   ngrok http 3001
   # 把 https URL 写到 §1 的 webhook URL
   ```
3. 浏览器访问 `http://localhost:3000` → 答完 45 题
4. `/results/<id>` 点 **Unlock full report →**
5. 登录（或 guest 继续）→ `/payment?assessment_id=...`
6. 点 **Pay ₹49 via Razorpay**。Razorpay JS modal **页内**打开
7. 用测试卡：
   - 成功：`4111 1111 1111 1111`，任意未来 expiry，任意 CVV，OTP `1234`
   - 失败：`4111 1111 1111 1112`
8. 成功后 SDK 回 `handler({ razorpay_order_id, _payment_id, _signature })`
9. 前端 `POST /api/v3/payment/razorpay/verify` 确认 assessment
10. 浏览器到 `/payment/success?assessment_id=...`
11. **独立地**，Razorpay 把 `payment.captured` 推到你的 webhook URL；后端按 `payment_txn_id` 匹配 + 双重确认

### 故障排查

| 现象 | 原因 | 修复 |
| --- | --- | --- |
| modal 打开、付款成功，但报告仍锁 | verify 失败 | 看 FastAPI 日志 `/razorpay/verify` 401 — 通常 `RAZORPAY_KEY_SECRET` 错 |
| webhook 永不到 | ngrok URL 过期或没在 dashboard 配 | 用当前 ngrok https URL 重建 webhook |
| `Invalid webhook signature` 401 | `RAZORPAY_WEBHOOK_SECRET` 不一致 | dashboard 上拷贝同一个 secret |
| `Assessment not yet completed` 400 | 在提交答案前就触发了 `/razorpay/order` | 先做完测试 |
| mock 模式仍出现 redirect URL 即使 `PAYMENT_MODE=razorpay` | 后端 env 没 reload | 重启 uvicorn，重新 source env |
| Letsencrypt 续期失败 | 80 端口不可达 / DNS 未指向 | `nslookup mindprism.in` + `ufw status` |

---

## 5. 上 live

1. Razorpay Dashboard → 激活 live 模式（KYC：PAN + 银行账号）
2. 生成 **Live API Keys**（`rzp_live_...`）
3. 在 `env/prod.env` 设 `PAYMENT_MODE=razorpay`、`RAZORPAY_KEY_ID=rzp_live_...`、`RAZORPAY_KEY_SECRET=...`、`RAZORPAY_WEBHOOK_SECRET=...`，重新部署
4. 用 live key 跑一次 sandbox smoke（创建一笔 ₹49 订单验证；可立即在 dashboard 撤销）
5. live webhook URL 改成 `https://<prod-domain>/api/v3/payment/webhook/razorpay`
6. 用另一手机给自己发 ₹1，再从 dashboard 退款

> **合规：** 测试交易标 `notes.smoke=true` 方便对账

---

## 6. 关闭 Razorpay（回滚）

设 `PAYMENT_MODE=mock` 重启。前端 `<RazorpayCheckoutButton />` 自动回退到 mock 重定向 URL — dev 流程仍然完整，但不会真扣款。

---

## 6b. 多 Provider 上线手册（2026 年 5 月起）

MindPrism 现在并行支持多个支付驱动，运维可以在同一个 `/payment` 页面提供 Razorpay + UPI Intent（或 PayU 备选）。每个驱动的 onboarding：

### Razorpay（默认）
见 §1–5。**无变化。**

### Cashfree（备选聚合器）

1. 注册 <https://merchant.cashfree.com>，启用 test 模式
2. Settings → API Keys → 拷贝 `App ID` + `Secret Key`
3. Settings → Webhooks → 添加 `https://api.mindprism.in/api/v3/payment/webhook/cashfree`
4. `env/prod.env`：
   ```dotenv
   CASHFREE_CLIENT_ID=...
   CASHFREE_CLIENT_SECRET=...
   CASHFREE_WEBHOOK_SECRET=...
   CASHFREE_API_BASE=https://api.cashfree.com   # sandbox: https://sandbox.cashfree.com
   PAYMENT_DRIVERS_ENABLED=razorpay,cashfree,upi,mock
   ```
5. 重启。picker 显示 Cashfree 作为非推荐选项

### PayU India（form-POST 备选）

1. 注册 <https://payu.in/business>，完成商户 onboarding
2. Dashboard → Integration → 拷贝 `Merchant Key` + `Salt`
3. env：
   ```dotenv
   PAYU_MERCHANT_KEY=...
   PAYU_MERCHANT_SALT=...
   PAYU_API_BASE=https://test.payu.in       # production: https://secure.payu.in
   PAYMENT_DRIVERS_ENABLED=razorpay,payu,mock
   ```
4. 重启。PayU 用户跳转到 PayU 托管页（不是 modal）

### UPI Intent（无聚合器）

1. 在你的银行（HDFC / ICICI / Axis SmartBiz）拿一个商业 VPA。前若干 GMV 之内也能用个人 VPA — 看银行 TOS
2. env：
   ```dotenv
   UPI_VPA=mindprism@hdfcbank
   UPI_DISPLAY_NAME=MindPrism
   PAYMENT_DRIVERS_ENABLED=razorpay,upi,mock
   ```
3. 重启。UPI 显示为 "UPI Pay (PhonePe / GPay / Paytm)"
4. **手工对账。** 用户点"我付了"后 assessment 进 `payment_status="awaiting_review"`。运维比对银行流水的 txn ref（如 `MIND12AB`），手工 flip：
   ```sql
   UPDATE assessments
     SET paid = 1, payment_status = 'confirmed'
     WHERE id = '<assessment_id>';
   ```
   （或用未来的管理员端点）

### 切换默认
- `PAYMENT_DEFAULT_DRIVER=razorpay`（或任何 enabled id） — picker 会标 **Recommended**
- 留空 → 回退 `PAYMENT_MODE`（旧式单驱动）

### dev/prod 付费墙
- **dev** 默认 `ALLOW_FREE_REPORT=true`，QA 不配支付驱动也能看完整报告。UI 上叠加大型对角 `PREVIEW · DEV` 水印 + "Unlock the real report" CTA
- **prod** 默认 `ALLOW_FREE_REPORT=false`。`/api/v3/report/{id}` 在未付费时返回 `402`
- 任意环境通过 `ALLOW_FREE_REPORT=true|false` 显式覆盖
