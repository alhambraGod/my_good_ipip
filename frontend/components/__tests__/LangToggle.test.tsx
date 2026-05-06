// @vitest-environment happy-dom
import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { LangProvider } from "@/lib/i18n/LangContext";
import { LangToggle } from "@/components/LangToggle";

function withProvider(ui: React.ReactNode) {
  return <LangProvider>{ui}</LangProvider>;
}

describe("<LangToggle />", () => {
  it("renders both EN and हि buttons", () => {
    render(withProvider(<LangToggle />));
    expect(screen.getByRole("button", { name: "EN" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "हि" })).toBeInTheDocument();
  });

  it("defaults to EN with aria-pressed=true", () => {
    render(withProvider(<LangToggle />));
    expect(screen.getByRole("button", { name: "EN" })).toHaveAttribute("aria-pressed", "true");
    expect(screen.getByRole("button", { name: "हि" })).toHaveAttribute("aria-pressed", "false");
  });

  it("switches active state and persists to localStorage when हि is clicked", async () => {
    const user = userEvent.setup();
    render(withProvider(<LangToggle />));
    const hiBtn = screen.getByRole("button", { name: "हि" });
    await user.click(hiBtn);
    expect(hiBtn).toHaveAttribute("aria-pressed", "true");
    expect(screen.getByRole("button", { name: "EN" })).toHaveAttribute("aria-pressed", "false");
    expect(localStorage.getItem("careerdna_lang")).toBe("hi");
  });

  it("switches back to EN", async () => {
    const user = userEvent.setup();
    render(withProvider(<LangToggle />));
    await user.click(screen.getByRole("button", { name: "हि" }));
    await user.click(screen.getByRole("button", { name: "EN" }));
    expect(screen.getByRole("button", { name: "EN" })).toHaveAttribute("aria-pressed", "true");
    expect(localStorage.getItem("careerdna_lang")).toBe("en");
  });
});
