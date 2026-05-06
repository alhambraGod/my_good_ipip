// @vitest-environment happy-dom
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

// Mock all collaborators BEFORE importing the SUT.
vi.mock("@/lib/v3-api", () => ({
  createV3RazorpayOrder: vi.fn(),
  verifyV3RazorpayCheckout: vi.fn(),
}));
vi.mock("@/lib/razorpay", () => ({
  loadRazorpayCheckout: vi.fn(),
  openRazorpayCheckout: vi.fn(),
}));
const pushMock = vi.fn();
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: pushMock }),
}));

import { RazorpayCheckoutButton } from "@/components/RazorpayCheckoutButton";
import { ToastProvider } from "@/components/Toast";
import { createV3RazorpayOrder, verifyV3RazorpayCheckout } from "@/lib/v3-api";
import { loadRazorpayCheckout, openRazorpayCheckout } from "@/lib/razorpay";

type RzpOptions = Parameters<typeof openRazorpayCheckout>[0];
type Verify = typeof verifyV3RazorpayCheckout;

const ASSESSMENT_ID = "assess-XYZ";

function renderButton(extra: Partial<React.ComponentProps<typeof RazorpayCheckoutButton>> = {}) {
  return render(
    <ToastProvider>
      <RazorpayCheckoutButton
        assessmentId={ASSESSMENT_ID}
        amountLabel="Pay ₹49 via Razorpay"
        fullLabel="Pay via Razorpay"
        {...extra}
      />
    </ToastProvider>,
  );
}

// Capture writes to window.location.href without happy-dom navigating.
const lastNav: { href: string | null } = { href: null };
const originalLocation = window.location;

beforeEach(() => {
  pushMock.mockClear();
  vi.mocked(createV3RazorpayOrder).mockReset();
  vi.mocked(verifyV3RazorpayCheckout).mockReset();
  vi.mocked(loadRazorpayCheckout).mockReset();
  vi.mocked(openRazorpayCheckout).mockReset();
  lastNav.href = null;

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
      replace: (v: string) => {
        lastNav.href = v;
      },
      reload: () => {},
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

describe("<RazorpayCheckoutButton />", () => {
  it("renders the amount label by default", () => {
    renderButton();
    expect(screen.getByRole("button", { name: /Pay ₹49 via Razorpay/ })).toBeInTheDocument();
  });

  it("falls back to mock_redirect_url when backend is in mock mode", async () => {
    vi.mocked(createV3RazorpayOrder).mockResolvedValue({
      assessment_id: ASSESSMENT_ID,
      provider: "mock",
      order_id: null,
      amount_inr: 49,
      amount_paise: 4900,
      currency: "INR",
      key_id: null,
      promo_active: true,
      mock_redirect_url: "/payment/success?assessment_id=assess-XYZ&mock=true",
    });
    const user = userEvent.setup();
    renderButton();

    await user.click(screen.getByRole("button"));

    await waitFor(() => {
      expect(lastNav.href).toBe("/payment/success?assessment_id=assess-XYZ&mock=true");
    });
    expect(loadRazorpayCheckout).not.toHaveBeenCalled();
    expect(openRazorpayCheckout).not.toHaveBeenCalled();
  });

  it("opens the Razorpay SDK with the order params in razorpay mode", async () => {
    vi.mocked(createV3RazorpayOrder).mockResolvedValue({
      assessment_id: ASSESSMENT_ID,
      provider: "razorpay",
      order_id: "order_TEST_1",
      amount_inr: 49,
      amount_paise: 4900,
      currency: "INR",
      key_id: "rzp_test_KEY",
      promo_active: true,
      mock_redirect_url: null,
    });
    vi.mocked(loadRazorpayCheckout).mockResolvedValue();
    vi.mocked(openRazorpayCheckout).mockReturnValue({
      open: vi.fn(),
      close: vi.fn(),
    } as unknown as ReturnType<typeof openRazorpayCheckout>);

    const user = userEvent.setup();
    renderButton();
    await user.click(screen.getByRole("button"));

    await waitFor(() => {
      expect(openRazorpayCheckout).toHaveBeenCalledTimes(1);
    });
    const opts = vi.mocked(openRazorpayCheckout).mock.calls[0][0] as RzpOptions;
    expect(opts.key).toBe("rzp_test_KEY");
    expect(opts.order_id).toBe("order_TEST_1");
    expect(opts.amount).toBe(4900);
    expect(opts.currency).toBe("INR");
    expect(opts.notes).toEqual({ assessment_id: ASSESSMENT_ID });
    expect(typeof opts.handler).toBe("function");
  });

  it("verifies the payment and routes to /payment/success on Razorpay handler success", async () => {
    vi.mocked(createV3RazorpayOrder).mockResolvedValue({
      assessment_id: ASSESSMENT_ID,
      provider: "razorpay",
      order_id: "order_X",
      amount_inr: 49,
      amount_paise: 4900,
      currency: "INR",
      key_id: "rzp_test_X",
      promo_active: true,
      mock_redirect_url: null,
    });
    vi.mocked(loadRazorpayCheckout).mockResolvedValue();
    vi.mocked(openRazorpayCheckout).mockReturnValue({
      open: vi.fn(),
      close: vi.fn(),
    } as unknown as ReturnType<typeof openRazorpayCheckout>);
    const verify = vi.mocked(verifyV3RazorpayCheckout) as unknown as ReturnType<
      typeof vi.mocked<Verify>
    >;
    verify.mockResolvedValue({ assessment_id: ASSESSMENT_ID, paid: true, status: "confirmed" });

    const user = userEvent.setup();
    renderButton();
    await user.click(screen.getByRole("button"));

    await waitFor(() => expect(openRazorpayCheckout).toHaveBeenCalled());
    const opts = vi.mocked(openRazorpayCheckout).mock.calls[0][0] as RzpOptions;

    await opts.handler({
      razorpay_order_id: "order_X",
      razorpay_payment_id: "pay_Y",
      razorpay_signature: "sig_Z",
    });

    expect(verify).toHaveBeenCalledWith({
      assessment_id: ASSESSMENT_ID,
      razorpay_order_id: "order_X",
      razorpay_payment_id: "pay_Y",
      razorpay_signature: "sig_Z",
    });
    expect(pushMock).toHaveBeenCalledWith(`/payment/success?assessment_id=${ASSESSMENT_ID}`);
  });

  it("toasts an error when verifyV3RazorpayCheckout rejects", async () => {
    vi.mocked(createV3RazorpayOrder).mockResolvedValue({
      assessment_id: ASSESSMENT_ID,
      provider: "razorpay",
      order_id: "order_X",
      amount_inr: 49,
      amount_paise: 4900,
      currency: "INR",
      key_id: "rzp_test_X",
      promo_active: true,
      mock_redirect_url: null,
    });
    vi.mocked(loadRazorpayCheckout).mockResolvedValue();
    vi.mocked(openRazorpayCheckout).mockReturnValue({
      open: vi.fn(),
      close: vi.fn(),
    } as unknown as ReturnType<typeof openRazorpayCheckout>);
    vi.mocked(verifyV3RazorpayCheckout).mockRejectedValue(new Error("Invalid signature"));

    const user = userEvent.setup();
    renderButton();
    await user.click(screen.getByRole("button"));

    await waitFor(() => expect(openRazorpayCheckout).toHaveBeenCalled());
    const opts = vi.mocked(openRazorpayCheckout).mock.calls[0][0] as RzpOptions;

    await opts.handler({
      razorpay_order_id: "order_X",
      razorpay_payment_id: "pay_Y",
      razorpay_signature: "bad",
    });

    await waitFor(() => {
      expect(screen.getByText(/Invalid signature/)).toBeInTheDocument();
    });
    expect(pushMock).not.toHaveBeenCalled();
  });

  it("toasts when the SDK script fails to load", async () => {
    vi.mocked(createV3RazorpayOrder).mockResolvedValue({
      assessment_id: ASSESSMENT_ID,
      provider: "razorpay",
      order_id: "order_Z",
      amount_inr: 49,
      amount_paise: 4900,
      currency: "INR",
      key_id: "rzp_test_Z",
      promo_active: true,
      mock_redirect_url: null,
    });
    vi.mocked(loadRazorpayCheckout).mockRejectedValue(new Error("Network down"));
    const user = userEvent.setup();
    renderButton();

    await user.click(screen.getByRole("button"));

    await waitFor(() => {
      expect(screen.getByText(/Could not load payment SDK/)).toBeInTheDocument();
    });
    expect(openRazorpayCheckout).not.toHaveBeenCalled();
  });

  it("toasts when /razorpay/order itself rejects", async () => {
    vi.mocked(createV3RazorpayOrder).mockRejectedValue(new Error("Already paid"));
    const user = userEvent.setup();
    renderButton();

    await user.click(screen.getByRole("button"));

    await waitFor(() => {
      expect(screen.getByText(/Already paid/)).toBeInTheDocument();
    });
  });

  it("is disabled while parent is in loading state", () => {
    renderButton({ loading: true });
    expect(screen.getByRole("button")).toBeDisabled();
  });
});
