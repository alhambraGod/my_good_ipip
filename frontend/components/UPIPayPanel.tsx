"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { confirmV3UPIPayment, type V3PaymentIntent } from "@/lib/v3-api";
import { useToast } from "@/components/Toast";

/**
 * Renders the deep link + QR for a UPI Intent payment, plus an "I've paid"
 * button. Confirmation is server-marked `awaiting_review` until ops manually
 * reconciles against the bank statement (see PAYMENT_PROVIDERS.md §4.4).
 */
export function UPIPayPanel({
  intent,
  assessmentId,
}: {
  intent: V3PaymentIntent;
  assessmentId: string;
}) {
  const router = useRouter();
  const toast = useToast();
  const [busy, setBusy] = useState(false);

  const cp = (intent.client_payload || {}) as {
    vpa?: string;
    display_name?: string;
    amount_inr?: number;
    txn_ref?: string;
    deep_link?: string;
  };

  const handleConfirm = async () => {
    if (busy) return;
    setBusy(true);
    try {
      const res = await confirmV3UPIPayment({
        assessment_id: assessmentId,
        txn_ref: intent.txn_id ?? cp.txn_ref ?? undefined,
      });
      toast.push(
        res.message ||
          "Thanks — we've noted your payment and will confirm in 30 minutes.",
        "success",
        6000,
      );
      router.push(`/payment/success?assessment_id=${assessmentId}&provider=upi`);
    } catch (e) {
      toast.push(
        e instanceof Error ? e.message : "Couldn't record your confirmation",
        "error",
      );
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="rounded-2xl border-2 border-india-green-300 bg-white p-5 mb-4">
      <div className="flex items-center justify-between mb-3">
        <div>
          <p className="text-xs font-bold uppercase tracking-wider text-saffron-700 mb-1">
            Pay via UPI
          </p>
          <p className="text-sm text-navy-text/70">
            Send <span className="font-bold">₹{cp.amount_inr ?? intent.amount_inr}</span>{" "}
            to{" "}
            <code className="px-1.5 py-0.5 rounded bg-saffron-50 text-saffron-700 text-xs">
              {cp.vpa}
            </code>
          </p>
        </div>
      </div>

      {intent.qr_code_data_url ? (
        <div className="flex flex-col items-center my-4">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src={intent.qr_code_data_url}
            alt={`Scan to pay ₹${cp.amount_inr} to ${cp.vpa}`}
            className="w-44 h-44 rounded-md border border-saffron-200"
          />
          <p className="text-[11px] text-navy-text/50 mt-2">
            Scan with PhonePe / Google Pay / Paytm / BHIM
          </p>
        </div>
      ) : null}

      <div className="flex flex-col sm:flex-row gap-2 mb-3">
        <a
          href={cp.deep_link || intent.payment_url}
          className="flex-1 text-center bg-india-green-600 hover:bg-india-green-700 text-white font-bold py-2.5 rounded-xl transition-colors text-sm"
        >
          Open UPI app (mobile)
        </a>
      </div>

      <p className="text-xs text-navy-text/60 mb-3">
        Reference: <code>{intent.txn_id ?? cp.txn_ref}</code> — the bank will
        show this in your statement so we can match it.
      </p>

      <button
        type="button"
        onClick={handleConfirm}
        disabled={busy}
        className="w-full bg-saffron-600 hover:bg-saffron-700 text-white font-bold py-3 rounded-xl transition-all disabled:opacity-60"
      >
        {busy ? "Recording…" : "I've paid — submit for confirmation"}
      </button>
      <p className="text-[11px] text-navy-text/45 mt-2 text-center">
        Manual confirmation usually within 30 minutes (business hours). You&apos;ll
        get an email when your report is unlocked.
      </p>
    </div>
  );
}
