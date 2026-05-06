// @vitest-environment happy-dom
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

vi.mock("@/lib/api", () => ({
  startGoogleOAuth: vi.fn(),
  startFacebookOAuth: vi.fn(),
  startWhatsAppOAuth: vi.fn(),
}));
vi.mock("@/lib/oauth-return", () => ({
  setOAuthNextPath: vi.fn(),
  consumeOAuthNextPath: vi.fn(() => "/profile"),
}));
const pushMock = vi.fn();
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: pushMock }),
}));

import { UnlockAuthModal } from "@/components/UnlockAuthModal";
import {
  startGoogleOAuth,
  startFacebookOAuth,
  startWhatsAppOAuth,
} from "@/lib/api";
import { setOAuthNextPath } from "@/lib/oauth-return";

const PAYMENT_PATH = "/payment?assessment_id=abc-123";

const lastNav: { href: string | null } = { href: null };
const originalLocation = window.location;

beforeEach(() => {
  pushMock.mockClear();
  vi.mocked(startGoogleOAuth).mockReset();
  vi.mocked(startFacebookOAuth).mockReset();
  vi.mocked(startWhatsAppOAuth).mockReset();
  vi.mocked(setOAuthNextPath).mockReset();
  lastNav.href = null;

  // Stub <dialog> showModal/close — happy-dom 18 does not implement them.
  if (typeof HTMLDialogElement !== "undefined") {
    HTMLDialogElement.prototype.showModal = function () {
      this.setAttribute("open", "");
    };
    HTMLDialogElement.prototype.close = function () {
      this.removeAttribute("open");
    };
  }

  Object.defineProperty(window, "location", {
    configurable: true,
    writable: true,
    value: {
      get href() {
        return lastNav.href ?? "";
      },
      set href(v: string) {
        lastNav.href = v;
      },
      assign: (v: string) => {
        lastNav.href = v;
      },
    },
  });
});

afterEach(() => {
  Object.defineProperty(window, "location", {
    configurable: true,
    writable: true,
    value: originalLocation,
  });
  vi.restoreAllMocks();
});

function renderModal(open: boolean, onClose = vi.fn()) {
  return {
    onClose,
    ...render(
      <UnlockAuthModal open={open} onClose={onClose} paymentPath={PAYMENT_PATH} />,
    ),
  };
}

describe("<UnlockAuthModal />", () => {
  it("opens the dialog when open=true and shows three OAuth buttons", () => {
    renderModal(true);
    const dialog = document.querySelector("dialog")!;
    expect(dialog.hasAttribute("open")).toBe(true);
    expect(screen.getByRole("button", { name: /Continue with Google/ })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Continue with Facebook/ })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /WhatsApp/ })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Continue as guest/ })).toBeInTheDocument();
  });

  it("closes the dialog when open=false", () => {
    const { rerender } = render(
      <UnlockAuthModal open={true} onClose={vi.fn()} paymentPath={PAYMENT_PATH} />,
    );
    rerender(
      <UnlockAuthModal open={false} onClose={vi.fn()} paymentPath={PAYMENT_PATH} />,
    );
    const dialog = document.querySelector("dialog")!;
    expect(dialog.hasAttribute("open")).toBe(false);
  });

  it("Google: stashes next-path then redirects to provider auth_url", async () => {
    vi.mocked(startGoogleOAuth).mockResolvedValue({ auth_url: "https://accounts.google.com/auth?x=1" });
    const user = userEvent.setup();
    renderModal(true);

    await user.click(screen.getByRole("button", { name: /Continue with Google/ }));

    await waitFor(() => {
      expect(setOAuthNextPath).toHaveBeenCalledWith(PAYMENT_PATH);
      expect(lastNav.href).toBe("https://accounts.google.com/auth?x=1");
    });
  });

  it("Facebook: same flow with the Facebook provider", async () => {
    vi.mocked(startFacebookOAuth).mockResolvedValue({ auth_url: "https://www.facebook.com/dialog/oauth?x=2" });
    const user = userEvent.setup();
    renderModal(true);

    await user.click(screen.getByRole("button", { name: /Continue with Facebook/ }));

    await waitFor(() => {
      expect(setOAuthNextPath).toHaveBeenCalledWith(PAYMENT_PATH);
      expect(lastNav.href).toBe("https://www.facebook.com/dialog/oauth?x=2");
    });
  });

  it("WhatsApp: same flow with the WhatsApp/Meta provider", async () => {
    vi.mocked(startWhatsAppOAuth).mockResolvedValue({ auth_url: "https://www.facebook.com/v17.0/dialog/oauth?x=3" });
    const user = userEvent.setup();
    renderModal(true);

    await user.click(screen.getByRole("button", { name: /WhatsApp/ }));

    await waitFor(() => {
      expect(setOAuthNextPath).toHaveBeenCalledWith(PAYMENT_PATH);
      expect(lastNav.href).toBe("https://www.facebook.com/v17.0/dialog/oauth?x=3");
    });
  });

  it("OAuth start failure keeps the modal open and does not navigate", async () => {
    vi.mocked(startGoogleOAuth).mockRejectedValue(new Error("oauth-down"));
    const user = userEvent.setup();
    const { onClose } = renderModal(true);

    await user.click(screen.getByRole("button", { name: /Continue with Google/ }));

    await waitFor(() => {
      expect(setOAuthNextPath).toHaveBeenCalledWith(PAYMENT_PATH);
    });
    expect(lastNav.href).toBeNull();
    expect(onClose).not.toHaveBeenCalled();
  });

  it("Continue-as-guest pushes paymentPath and closes", async () => {
    const user = userEvent.setup();
    const { onClose } = renderModal(true);

    await user.click(screen.getByRole("button", { name: /Continue as guest/ }));

    expect(pushMock).toHaveBeenCalledWith(PAYMENT_PATH);
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it("Cancel button calls onClose without navigating", async () => {
    const user = userEvent.setup();
    const { onClose } = renderModal(true);

    await user.click(screen.getByRole("button", { name: /^Cancel$/ }));

    expect(onClose).toHaveBeenCalledTimes(1);
    expect(pushMock).not.toHaveBeenCalled();
  });
});
