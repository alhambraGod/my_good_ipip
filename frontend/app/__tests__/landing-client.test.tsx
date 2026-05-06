// @vitest-environment happy-dom
import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { LandingClient } from "@/app/_landing-client";
import { LangProvider } from "@/lib/i18n/LangContext";
import { type V3ArchetypeSummary } from "@/lib/v3-api";

const FEATURED: V3ArchetypeSummary[] = [
  { cell_id: "IA", label_en: "The 3AM Chai Philosopher", label_hi: "Sochne Wala", slogan_en: "You overthink your overthinking.", rarity_pct: 4.3 },
  { cell_id: "EC", label_en: "The Spreadsheet Founder", label_hi: "Hisaab Kitaab", slogan_en: "Vision plus VLOOKUP.", rarity_pct: 5.1 },
  { cell_id: "SE", label_en: "The Glue", label_hi: "Sab Ka Bandhu", slogan_en: "You bring people together.", rarity_pct: 6.2 },
];

function withProvider(ui: React.ReactNode) {
  return <LangProvider>{ui}</LangProvider>;
}

describe("<LandingClient />", () => {
  it("renders the hero, gallery, and FAQ when archetypes are provided", () => {
    render(withProvider(<LandingClient featured={FEATURED} />));
    // Hero CTA
    expect(screen.getByRole("link", { name: /Start Free Test/i })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Browse 24 archetypes/i })).toBeInTheDocument();
    // Gallery cards
    expect(screen.getByText("IA")).toBeInTheDocument();
    expect(screen.getByText("The 3AM Chai Philosopher")).toBeInTheDocument();
    expect(screen.getByText("Vision plus VLOOKUP.", { exact: false })).toBeInTheDocument();
    // FAQ entries
    expect(screen.getByText(/Why ₹49/i)).toBeInTheDocument();
    expect(
      screen.getByText(/How is this different from a Buzzfeed quiz/i),
    ).toBeInTheDocument();
  });

  it("hides the gallery section when no featured archetypes", () => {
    render(withProvider(<LandingClient featured={[]} />));
    expect(screen.queryByText(/Some archetypes you might be/i)).not.toBeInTheDocument();
  });

  it("FAQ items are collapsed by default and expand on click", async () => {
    const user = userEvent.setup();
    render(withProvider(<LandingClient featured={FEATURED} />));
    const summary = screen.getByText(/Is this scientifically valid\?/);
    const details = summary.closest("details") as HTMLDetailsElement;
    expect(details.open).toBe(false);
    await user.click(summary);
    expect(details.open).toBe(true);
  });
});
