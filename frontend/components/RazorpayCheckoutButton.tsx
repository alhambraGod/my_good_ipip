"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import {
  createV3RazorpayOrder,
  verifyV3RazorpayCheckout,
} from "@/lib/v3-api";
import {
  loadRazorpayCheckout,
  openRazorpayCheckout,
  type RazorpayHandlerResponse,
} from "@/lib/razorpay";
import { useToast } from "@/components/Toast";

type Props = {
  assessmentId: string;
  amountLabel: string;
  fullLabel: string;
  loading?: boolean;
  /** Override fallback redirect (mock mode) — defaults to backend payment_url. */
};

export function RazorpayCheckoutButton({
  assessmentId,
  amountLabel,
  fullLabel,
  loading,
}: Props) {
  const router = useRouter();
  const toast = useToast();
  const [busy, setBusy] = useState(false);

  const handleClick = async () => {
    if (busy || loading) return;
    setBusy(true);
    try {
      const order = await createV3RazorpayOrder(assessmentId);

      // Mock fallback — backend doesn't have Razorpay creds in dev.
      if (order.provider === "mock") {
        if (order.mock_redirect_url) {
          window.location.href = order.mock_redirect_url;
          return;
        }
        toast.push("Payment unavailable: server in mock mode", "error");
        return;
      }

      if (!order.order_id || !order.key_id) {
        toast.push("Razorpay order incomplete", "error");
        return;
      }

      try {
        await loadRazorpayCheckout();
      } catch {
        toast.push("Could not load payment SDK; check your network", "error");
        return;
      }

      openRazorpayCheckout({
        key: order.key_id,
        amount: order.amount_paise,
        currency: order.currency,
        order_id: order.order_id,
        name: "MindPrism India",
        description: "Full personality + career report",
        theme: { color: "#138808" },
        notes: { assessment_id: assessmentId },
        modal: {
          ondismiss: () => setBusy(false),
          escape: true,
        },
        handler: async (resp: RazorpayHandlerResponse) => {
          try {
            await verifyV3RazorpayCheckout({
              assessment_id: assessmentId,
              razorpay_order_id: resp.razorpay_order_id,
              razorpay_payment_id: resp.razorpay_payment_id,
              razorpay_signature: resp.razorpay_signature,
            });
            router.push(`/payment/success?assessment_id=${assessmentId}`);
          } catch (e) {
            toast.push(
              e instanceof Error ? e.message : "Payment verification failed",
              "error",
            );
            setBusy(false);
          }
        },
      });
    } catch (e) {
      toast.push(
        e instanceof Error ? e.message : "Could not start checkout",
        "error",
      );
      setBusy(false);
    }
  };

  const label = busy
    ? fullLabel.replace("Pay", "Opening checkout…").replace("Razorpay", "")
    : amountLabel;

  return (
    <button
      type="button"
      onClick={handleClick}
      disabled={busy || loading}
      className="w-full bg-gradient-to-r from-india-green-600 to-india-green-700 text-white font-bold text-lg py-4 rounded-2xl hover:from-india-green-700 hover:to-india-green-800 transition-all shadow-lg disabled:opacity-60 disabled:cursor-not-allowed"
    >
      {busy ? (
        <span className="flex items-center justify-center gap-2">
          <span className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
          Opening checkout…
        </span>
      ) : (
        <>{label}</>
      )}
    </button>
  );
}
