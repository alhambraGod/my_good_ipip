# Razorpay Runbook

End-to-end checklist for taking the MindPrism payment flow from `mock`
to a real **test-mode** account, then to **live**.

> **Scope:** dev-laptop verification. Going live (prod) requires a Razorpay
> account on a registered Indian entity / KYC-verified individual. v1
> uses an Indian friend's personal KYC; v2 should move to a registered
> business account.

---

## 0. Prereqs

* A Razorpay account (an Indian phone + PAN is enough for **test** mode)
* Backend running locally (FastAPI on `:3001`) and frontend (`:3000`)
* Public tunnel for the webhook endpoint (`ngrok`, `cloudflared`, etc.) when
  you want to capture real webhook events

---

## 1. Get test credentials

1. Razorpay Dashboard → top-right toggle: switch to **Test Mode**
2. Settings → **API Keys** → **Generate Test Key**
3. Copy `Key Id` (starts with `rzp_test_`) and `Key Secret`
4. Settings → **Webhooks** → **Add New Webhook**
   * URL: `https://<your-ngrok>.app/api/v3/payment/webhook/razorpay`
   * Active events: `payment.captured`, `order.paid`, `payment_link.paid`
   * Webhook secret: any random string — **save the same value into
     `RAZORPAY_WEBHOOK_SECRET`** below

---

## 2. Local env

Append (or replace) the following in `env/dev.env` (or the env file your
`deploy_backend.sh` reads):

```dotenv
PAYMENT_MODE=razorpay
RAZORPAY_KEY_ID=rzp_test_xxxxxxxxxxxxxx
RAZORPAY_KEY_SECRET=xxxxxxxxxxxxxxxxxxxxxxxx
RAZORPAY_WEBHOOK_SECRET=whatever-you-saved-above
```

> Re-run `bash backend/deploy_backend.sh dev` so `backend/.env` is
> regenerated; restart `uvicorn`.

---

## 3. Sandbox smoke test (no DB, no UI)

This script verifies the credentials + signing logic without touching the
local FastAPI app:

```bash
cd backend
conda activate my_good_ipip
PAYMENT_MODE=razorpay \
RAZORPAY_KEY_ID=rzp_test_xxxxx \
RAZORPAY_KEY_SECRET=xxxxx \
python -m scripts.razorpay_sandbox_smoke
```

Expected output:

```
➜ Razorpay sandbox smoke
[1/3] Creating sandbox Order…   ok
[2/3] Verifying that the HMAC signing rule round-trips…   ok
[3/3] Sanity-check webhook signature helper…   ok
```

If you get **HTTP 401** the keys are wrong; if **HTTP 400** there's
likely a typo in `RZP_SMOKE_AMOUNT_INR`.

---

## 4. End-to-end with the UI

1. `bash start_all.sh dev`
2. In another shell, expose your backend:

   ```bash
   ngrok http 3001
   # copy the HTTPS URL into the Razorpay webhook URL in §1
   ```

3. Visit `http://localhost:3000` → take the 45-question test
4. On `/results/<id>` click **Unlock full report →**
5. Sign in (or continue as guest) → `/payment?assessment_id=...`
6. Click **Pay ₹49 via Razorpay**. The Razorpay JS modal opens **in-page**
7. Pay with a test card (Razorpay test card list):
   * Success: `4111 1111 1111 1111`, any future expiry, any CVV, OTP `1234`
   * Fail: `4111 1111 1111 1112`
8. On success, the SDK calls `handler({ razorpay_order_id, _payment_id, _signature })`
9. Frontend `POST /api/v3/payment/razorpay/verify` confirms the assessment
10. Browser navigates to `/payment/success?assessment_id=...`
11. **Independently**, Razorpay fires `payment.captured` to your webhook URL.
    Backend matches it to the same assessment via `payment_txn_id` (the
    order id) and double-confirms.

### Troubleshooting

| Symptom | Cause | Fix |
| --- | --- | --- |
| Modal opens, payment succeeds, but report stays locked | `verify` failed | Check FastAPI logs for `/razorpay/verify` 401 — usually a wrong `RAZORPAY_KEY_SECRET` |
| Webhook never reaches server | ngrok URL stale or not added in dashboard | Re-create webhook with the current ngrok https URL |
| `Invalid webhook signature` 401 | `RAZORPAY_WEBHOOK_SECRET` mismatch | Copy the exact secret from the dashboard webhook config |
| `Assessment not yet completed` 400 on `/razorpay/order` | Triggered before submitting answers | Take the test before navigating to /payment |
| Mock-mode redirect URL appears even though `PAYMENT_MODE=razorpay` | Backend env didn't reload | Restart uvicorn, re-source the env file |

---

## 5. Going live

1. Razorpay Dashboard → Activate live mode (KYC required: PAN + bank account)
2. Generate **Live API Keys** (`rzp_live_...`)
3. Set `PAYMENT_MODE=razorpay`, `RAZORPAY_KEY_ID=rzp_live_...`,
   `RAZORPAY_KEY_SECRET=...`, `RAZORPAY_WEBHOOK_SECRET=...` in
   `env/prod.env` and redeploy
4. Run the sandbox smoke (`python -m scripts.razorpay_sandbox_smoke`) once
   on the live keys — it'll create a tiny ₹49 order to validate keys; you
   can void it from the dashboard immediately
5. Update the live webhook URL to `https://<prod-domain>/api/v3/payment/webhook/razorpay`
6. Send yourself a `₹1` test transaction from another phone, then refund it
   from the dashboard

> **Compliance:** keep test transactions clearly tagged (`notes.smoke=true`)
> so reconciliation is easy.

---

## 6. Disabling Razorpay (rollback)

Set `PAYMENT_MODE=mock` and restart. The frontend
`<RazorpayCheckoutButton />` automatically falls back to the mock
redirect URL — users still get the full flow in dev, but no charges.

---

## 7. Reference

* Razorpay Orders API: https://razorpay.com/docs/api/orders/
* Razorpay Checkout JS: https://razorpay.com/docs/payments/payment-gateway/web-integration/standard/
* Test cards: https://razorpay.com/docs/payments/payments/test-card-details/
* Webhook events: https://razorpay.com/docs/webhooks/
