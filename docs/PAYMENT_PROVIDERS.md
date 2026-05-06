# MindPrism — Payment Providers Research & Integration

> Decision document + integration spec for the **Indian** payment
> landscape. Pair with **RUNBOOK_payments.md** (going live with each
> driver) and **ARCHITECTURE.md §4** (driver abstraction).

Last reviewed: **May 2026**.

---

## 1. The Indian payment landscape (2026 reality)

UPI dominates retail payments in India (≈ **80% of consumer digital
transactions** by volume per NPCI public data). Cards are second; net
banking and wallets follow. Critically for a ₹49 SaaS purchase from
Gen-Z white-collar / students:

| Method | Share of Indian e-com | Why MindPrism cares |
| --- | --- | --- |
| **UPI** (PhonePe / Google Pay / Paytm / BHIM) | ~60% | Zero-MDR, instant, Gen-Z native, works on ₹49 |
| **Cards** (RuPay / Visa / Mastercard) | ~15% | OVD users, urban Tier-1 |
| **Netbanking** | ~10% | Older / corporate users |
| **Wallets** (Paytm / Mobikwik / Freecharge) | ~7% | Niche, many migrating to UPI |
| **EMI / BNPL** | ~5% | Higher ticket only — N/A for ₹49 |
| **International cards** | < 1% | Only diaspora |

**Direct UPI** (no aggregator) is essentially free of merchant fees but
has settlement and KYC operational cost. **Aggregators** (Razorpay,
Cashfree, PayU, Paytm-PG, PhonePe-PG) take 1–2% MDR but handle
settlement, refunds, dashboard, KYC paperwork and webhook
delivery — which is why every Indian SaaS you've heard of uses one.

We support **multiple aggregators** (any one can be enabled per env)
and **a direct UPI Intent path** (no aggregator at all, settlement via
your bank's VPA — the kindergarten-payments mode).

---

## 2. Comparison matrix

| Provider | API style | Webhook scheme | India-only | KYC for live | MDR (typical) | UI mode | Mobile UPI | Open-source SDK |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| **Razorpay** | REST (Orders + Checkout JS) | HMAC SHA-256 of body | yes | individual PAN OK | 2% (UPI 0% by NPCI rule, but Razorpay still bills service fee in some plans) | Hosted modal (in-page) | ✓ via UPI in modal | razorpay-python, razorpay-js |
| **Cashfree** | REST (Orders + JS SDK) | HMAC SHA-256 of `(timestamp + body)` | yes | individual PAN OK | 1.75% standard | Hosted page or modal | ✓ | cashfree-pg-sdk-python, cashfree-checkout-js |
| **PayU India** | REST + form POST (legacy hash) | SHA-512 hash of params | yes | merchant onboarding | 2% standard, EMI/cards higher | Hosted page (form POST) | ✓ via wrapper | python-payu (community), payubiz-js |
| **Paytm Payments** | REST (Initiate Transaction + JS Checkout) | Checksum (PaytmChecksum) | yes | merchant onboarding | 1.99% standard | Hosted modal | ✓ | paytmchecksum, Paytm_AllInOneSDK |
| **PhonePe Direct** | REST (Standard Checkout) | X-VERIFY checksum | yes | merchant onboarding | 0% on UPI | Hosted page or QR | ✓ (native) | community Python wrappers, PhonePe-checkout |
| **UPI Intent** (no aggregator) | `upi://` deep link / QR | none (manual reconciliation via bank webhook or polling) | yes | self-VPA / business UPI ID | 0% | Custom (deep link or QR PNG) | ✓ (excellent) | none — pure URL spec (NPCI standard) |
| **Stripe** | REST (PaymentIntents) + Stripe.js | HMAC SHA-256 | global | yes (Atlas / Stripe India) | 2.9% + ₹2 | Hosted modal | partial (UPI in beta) | stripe-python, stripe-js |
| **Mock** | n/a | n/a | n/a | n/a | n/a | redirect to `/payment/success` | n/a | n/a |

> **MDR caveat.** As of NPCI rules, RuPay debit cards + UPI for
> consumer-facing merchants under ₹2,000 are **0% MDR** — but
> aggregators bill flat per-txn convenience fees / gateway charges,
> typically ₹1–2 per UPI txn. For ₹49 sticker price, the real cost
> after fees is **₹47–48** to your bank.

---

## 3. Selection rubric for v1 launch

Goals weighted for our specific case (Gen-Z, ₹49 sticker, soft
paywall, India only, conversion-sensitive):

| Criterion | Weight | Razorpay | Cashfree | PayU | Paytm | PhonePe | UPI Intent | Stripe |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| In-page modal (no redirect) | 4 | ✅ | ✅ | ❌ (form POST) | ✅ | ❌ (redirect) | ❌ | ✅ |
| Onboarding ease (individual KYC) | 3 | ✅ | ✅ | partial | partial | partial | ✅ (just need a UPI ID) | ❌ (Atlas needed) |
| UPI auto-fill on mobile | 4 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ (best) | partial |
| Webhook docs quality | 2 | ✅ | ✅ | partial | ✅ | partial | ❌ | ✅ |
| Free trials (₹1 test txns) | 2 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Refund automation | 2 | ✅ | ✅ | ✅ | ✅ | ✅ | manual | ✅ |
| **Total** | 17 | **17** | **17** | 11 | 13 | 12 | 11 | 12 |

**Decision (May 2026)**:
- **Default driver**: **Razorpay** (highest UX bar in-page).
- **Configurable alternates** (operator picks what's enabled):
  **Cashfree, PayU, UPI Intent, Mock**.
- **Stripe**: kept as a separate path for non-India routes (diaspora
  buyers paying in USD); not part of the v1 picker.
- **Paytm + PhonePe direct**: backlogged for v2 once we have the GMV
  to negotiate aggregator-grade rates from them.

The picker UI (frontend) shows **only the providers the operator
enables in env**, never the full menu, so a launch with only Razorpay
behaves identically to before.

---

## 4. Per-provider integration notes

### 4.1 Razorpay (already wired — gold reference)

- Orders API: `POST /v1/orders` (HTTP Basic Auth with `key_id:key_secret`).
- Checkout JS: `https://checkout.razorpay.com/v1/checkout.js`.
- Verify checkout: `HMAC_SHA256(order_id + "|" + payment_id, key_secret)` matches `razorpay_signature`.
- Webhook: `X-Razorpay-Signature` = `HMAC_SHA256(body, webhook_secret)`.
- Events to handle: `order.paid`, `payment.captured`, `payment_link.paid` (legacy).
- See `backend/services/payment/razorpay_driver.py` and
  `RUNBOOK_payments.md`.

### 4.2 Cashfree

- Orders API: `POST https://api.cashfree.com/pg/orders`
  Headers: `x-api-version: 2023-08-01`, `x-client-id`, `x-client-secret`.
- JS SDK: `https://sdk.cashfree.com/js/v3/cashfree.js`.
  Init with `paymentSessionId` returned by the order.
- Verify webhook: `HMAC_SHA256(timestamp + raw_body, secret)` then
  base64-encoded — header `x-webhook-signature`, `x-webhook-timestamp`.
- Status check: `GET /pg/orders/{order_id}` returns `order_status` ∈
  `{ACTIVE, PAID, EXPIRED}`.
- Test creds: signup → "Generate Test Keys" in dashboard.
- Reference SDK: `pip install cashfree-pg` (we use raw httpx + dict to
  avoid SDK version drift, mirroring Razorpay path).

### 4.3 PayU India

- "PayU Money" REST: `POST https://test.payu.in/_payment` (UAT) /
  `https://secure.payu.in/_payment` (live). Form-encoded.
- Auth via SHA-512 hash of `key|txnid|amount|productinfo|firstname|email|||||||||||salt`.
- Verify response: same hash, with extra status field, on the
  redirect-back URL.
- Webhook: hash on `salt|status||||||||||email|firstname|productinfo|amount|txnid|key`.
- Form POST flow: backend returns the prefilled form HTML (or just the
  hash + URL pair to the frontend), browser submits to PayU.
- Decision: implemented but **default off**; turn on via env when you
  want a redirect-style fallback.

### 4.4 UPI Intent (no aggregator — the "free / self-VPA" path)

The simplest possible payment integration on Earth:

- Build a deep link per the NPCI URL spec:
  ```
  upi://pay?
    pa=mindprism@upi&        # ← your VPA
    pn=MindPrism&             # ← display name
    am=49.00&                 # ← amount in INR
    cu=INR&
    tn=MIND-{assessment_id}&  # ← reference
    tr=MIND-{order_id}        # ← txn ref
  ```
- Render as a **clickable link** (mobile auto-opens the user's UPI app)
  AND a **PNG QR** (desktop scans it with their phone).
- **No automated confirmation.** The user clicks "I paid" → backend
  polls bank's transaction list (via aggregator's UPI subscription
  API), or you just manually verify each ₹49 hit in your bank
  statement. v1 acceptable for first 50 paid users; after that, switch
  to Razorpay UPI for auto-confirm.

### 4.5 Stripe (international)

- PaymentIntents API + Stripe.js.
- Standard everywhere; we keep `services/payment_service.py` as the
  legacy shim for diaspora.

### 4.6 Mock

- Always succeeds, redirects to `/payment/success?mock=true`.
- v1 default in dev / CI / staging.

---

## 5. Architecture in this repo

```
backend/services/payment/
├── base.py              ← Protocol + PaymentIntent + ProviderInfo dataclass
├── factory.py           ← get_payment_driver(name=None) — multi-driver registry
├── mock.py              ← MockDriver
├── razorpay_driver.py   ← RazorpayDriver (Order + Checkout SDK + webhook)
├── cashfree_driver.py   ← CashfreeDriver (Order + JS SDK + webhook)
├── payu_driver.py       ← PayUDriver (form POST + redirect)
├── upi_intent_driver.py ← UPIIntentDriver (deep-link + QR; manual confirm)
└── stripe_driver.py     ← (kept; legacy)
```

Operator config (`env/{dev,prod}.env`):

```dotenv
PAYMENT_DEFAULT_DRIVER=razorpay
PAYMENT_DRIVERS_ENABLED=razorpay,upi,cashfree,mock   # comma list

# Per-provider creds:
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

### dev vs. prod gating

- `ALLOW_FREE_REPORT` (env, default = `dev=true`, `prod=false`).
- When `true`, `/api/v3/report/{id}` returns the report even if
  `assessment.paid == False`, with `is_preview: true` set so the UI can
  render a watermark.
- When `false` (prod default), `/api/v3/report/{id}` returns 402 until
  paid. Fully restored to current behaviour.

### Frontend method picker

- `GET /api/v3/payment/providers` → list of `{ id, label, label_hi,
  description, supports_methods, requires_redirect, recommended }`.
- `<PaymentMethodPicker />` renders chips; user picks one; we hit a
  driver-specific endpoint. Defaults to the recommended one for a
  one-click happy path.

---

## 6. Test card / VPA reference

| Provider | Test card | Test UPI VPA | Test wallet |
| --- | --- | --- | --- |
| Razorpay | `4111 1111 1111 1111` (success) / `4111 1111 1111 1112` (fail) | `success@razorpay` / `failure@razorpay` | n/a |
| Cashfree | `4111 1111 1111 1111` | `testsuccess@gocash` / `testfailure@gocash` | n/a |
| PayU India | `5123 4567 8901 2346` (Mastercard) | n/a (UPI only on form) | `payumoney` |
| Paytm | per dashboard config | n/a | per dashboard |
| Stripe | `4242 4242 4242 4242` | n/a | n/a |
| UPI Intent | n/a (live VPA only) | n/a | n/a |

OTP for sandbox: `1234` (Razorpay), `123456` (Cashfree), `123` (PayU).

---

## 7. Compliance + ops sticky notes

- **Refund SLAs.** Razorpay 5–7 working days, Cashfree T+5, PayU
  T+7. Document this on `/payment/success` so users don't email ops.
- **GST invoice.** Razorpay/Cashfree both auto-generate GST invoices
  if MindPrism is registered as a Pvt Ltd; until then attach a manual
  PDF emailed by ops on request.
- **PCI-DSS scope.** None of our code ever sees a card number — the
  aggregator's hosted UI / SDK takes the card. We only see
  `payment_id` + signature. So we're SAQ-A scope, not SAQ-D.
- **Webhook idempotency.** Use the aggregator's `event_id` / `order_id`
  as a unique key in DB; reject duplicate webhooks with 200 + a log
  line (Razorpay et al will retry up to 24h on non-2xx).
- **Razorpay friend-KYC v1 cap.** Don't cross **₹5L cumulative GMV**
  on a friend's personal KYC (Razorpay TOS). Move to a Pvt Ltd before
  that — see `ROADMAP.md` 1.8.

---

## 8. References (open-source + official docs)

- **Razorpay**:
  - <https://razorpay.com/docs/api/orders/>
  - <https://razorpay.com/docs/payments/payment-gateway/web-integration/standard/>
  - SDK: <https://github.com/razorpay/razorpay-python>
- **Cashfree**:
  - <https://docs.cashfree.com/docs/order-create>
  - <https://docs.cashfree.com/docs/web-integration>
  - SDK: <https://github.com/cashfree/cashfree-pg-sdk-python>
- **PayU India**:
  - <https://payu.in/docs>
  - SDK reference: <https://github.com/payu-intrepos/PaymentSDK-Web>
- **Paytm**:
  - <https://business.paytm.com/docs>
- **PhonePe**:
  - <https://developer.phonepe.com>
- **UPI deep-link spec**:
  - <https://www.npci.org.in/PDF/npci/upi/circular/2017/UPI-LinkingSpecsver1.6.pdf>
  - <https://developer.npci.org.in/upi/upi-deep-linking>
- **Stripe**:
  - <https://stripe.com/docs/payments/payment-intents>
