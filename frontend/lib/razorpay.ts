"use client";

const SCRIPT_URL = "https://checkout.razorpay.com/v1/checkout.js";

let loadPromise: Promise<void> | null = null;

export function loadRazorpayCheckout(): Promise<void> {
  if (typeof window === "undefined") {
    return Promise.reject(new Error("SSR cannot load Razorpay"));
  }
  if ((window as unknown as { Razorpay?: unknown }).Razorpay) return Promise.resolve();
  if (loadPromise) return loadPromise;
  loadPromise = new Promise((resolve, reject) => {
    const existing = document.querySelector<HTMLScriptElement>(
      `script[src="${SCRIPT_URL}"]`,
    );
    const onload = () => resolve();
    const onerror = () => reject(new Error("Razorpay SDK failed to load"));
    if (existing) {
      if ((window as unknown as { Razorpay?: unknown }).Razorpay) {
        resolve();
        return;
      }
      existing.addEventListener("load", onload, { once: true });
      existing.addEventListener("error", onerror, { once: true });
      return;
    }
    const s = document.createElement("script");
    s.src = SCRIPT_URL;
    s.async = true;
    s.onload = onload;
    s.onerror = onerror;
    document.body.appendChild(s);
  });
  return loadPromise;
}

export type RazorpayHandlerResponse = {
  razorpay_payment_id: string;
  razorpay_order_id: string;
  razorpay_signature: string;
};

export type RazorpayCheckoutOptions = {
  key: string;
  amount: number;
  currency: string;
  order_id: string;
  name: string;
  description: string;
  prefill?: { name?: string; email?: string; contact?: string };
  notes?: Record<string, string>;
  theme?: { color?: string };
  handler: (response: RazorpayHandlerResponse) => void;
  modal?: { ondismiss?: () => void; escape?: boolean };
};

export type RazorpayInstance = { open: () => void; close: () => void };

type RazorpayConstructor = new (options: RazorpayCheckoutOptions) => RazorpayInstance;

export function openRazorpayCheckout(options: RazorpayCheckoutOptions): RazorpayInstance {
  const Ctor = (window as unknown as { Razorpay?: RazorpayConstructor }).Razorpay;
  if (!Ctor) throw new Error("Razorpay SDK not loaded");
  const inst = new Ctor(options);
  inst.open();
  return inst;
}
