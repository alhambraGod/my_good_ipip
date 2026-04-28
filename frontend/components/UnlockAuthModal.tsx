"use client";

import { useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import { startGoogleOAuth, startFacebookOAuth, startWhatsAppOAuth } from "@/lib/api";
import { setOAuthNextPath } from "@/lib/oauth-return";

type Props = {
  open: boolean;
  onClose: () => void;
  /** Where to go after successful sign-in (or guest continue). */
  paymentPath: string;
};

export function UnlockAuthModal({ open, onClose, paymentPath }: Props) {
  const dialogRef = useRef<HTMLDialogElement>(null);
  const router = useRouter();

  useEffect(() => {
    const el = dialogRef.current;
    if (!el) return;
    if (open) el.showModal();
    else el.close();
  }, [open]);

  const beginOAuth = async (kind: "google" | "facebook" | "whatsapp") => {
    setOAuthNextPath(paymentPath);
    try {
      let authUrl: string;
      if (kind === "google") {
        const r = await startGoogleOAuth();
        authUrl = r.auth_url;
      } else if (kind === "facebook") {
        const r = await startFacebookOAuth();
        authUrl = r.auth_url;
      } else {
        const r = await startWhatsAppOAuth();
        authUrl = r.auth_url;
      }
      window.location.href = authUrl;
    } catch {
      /* caller sees spinner stop; keep modal */
    }
  };

  return (
    <dialog
      ref={dialogRef}
      className="backdrop:bg-navy-text/40 rounded-3xl border-2 border-saffron-700/20 p-0 max-w-md w-[calc(100%-2rem)] bg-cream text-navy-text shadow-2xl"
      onClose={onClose}
      onCancel={(e) => {
        e.preventDefault();
        onClose();
      }}
    >
      <div className="p-6 md:p-8">
        <div className="text-center mb-2 text-2xl">🪔</div>
        <h2 className="text-xl font-bold text-center mb-1">Sign in to unlock</h2>
        <p className="text-sm text-navy-text/70 text-center mb-6">
          Link your account before payment so you can recover your report later.
          You can still pay as a guest.
        </p>

        <div className="flex flex-col gap-3">
          <button
            type="button"
            onClick={() => beginOAuth("google")}
            className="w-full rounded-xl py-3 px-4 font-semibold bg-white border border-navy-text/15 hover:bg-saffron-50 transition-colors text-sm"
          >
            Continue with Google
          </button>
          <button
            type="button"
            onClick={() => beginOAuth("facebook")}
            className="w-full rounded-xl py-3 px-4 font-semibold bg-[#1877F2] text-white hover:bg-[#166FE5] transition-colors text-sm"
          >
            Continue with Facebook
          </button>
          <button
            type="button"
            onClick={() => beginOAuth("whatsapp")}
            className="w-full rounded-xl py-3 px-4 font-semibold bg-[#25D366] text-white hover:bg-[#20BD5A] transition-colors text-sm"
          >
            Continue with WhatsApp (Meta)
          </button>
        </div>

        <button
          type="button"
          onClick={() => {
            router.push(paymentPath);
            onClose();
          }}
          className="w-full mt-4 text-sm font-medium text-navy-text/60 hover:text-navy-text py-2"
        >
          Continue as guest → pay without account
        </button>

        <button
          type="button"
          onClick={onClose}
          className="w-full mt-1 text-xs text-navy-text/40 hover:text-navy-text/60"
        >
          Cancel
        </button>
      </div>
    </dialog>
  );
}
