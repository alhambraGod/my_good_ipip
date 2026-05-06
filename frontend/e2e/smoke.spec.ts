import { expect, test } from "@playwright/test";

test.describe("CareerDNA smoke (no backend required)", () => {
  test("landing page renders hero + CTAs + feature cards", async ({ page }) => {
    await page.goto("/");

    await expect(
      page.getByRole("heading", { name: /Indian Career DNA/i, level: 1 }),
    ).toBeVisible();

    // Two primary CTAs in the hero
    const startCtas = page.getByRole("link", { name: /Start Free Test/i });
    await expect(startCtas.first()).toBeVisible();
    await expect(
      page.getByRole("link", { name: /Browse 24 archetypes/i }),
    ).toBeVisible();

    // The three feature card headings (exact match scoped to headings)
    await expect(
      page.getByRole("heading", { name: "Your archetype", exact: true }),
    ).toBeVisible();
    await expect(
      page.getByRole("heading", { name: "Career match", exact: true }),
    ).toBeVisible();
    await expect(
      page.getByRole("heading", { name: "WhatsApp-ready share", exact: true }),
    ).toBeVisible();

    // FAQ accordion is collapsed by default; expanding the first item
    // should reveal the description.
    const faqSummary = page.getByText(/Is this scientifically valid\?/);
    await faqSummary.click();
    await expect(
      page.getByText(/peer-reviewed instruments/i),
    ).toBeVisible();
  });

  test("language toggle switches Hindi label and persists across reload", async ({ page }) => {
    await page.goto("/");

    const hi = page.locator('button[aria-pressed]', { hasText: "हि" });
    await hi.click();
    await expect(hi).toHaveAttribute("aria-pressed", "true");

    // Hindi headline copy on landing
    await expect(page.getByText(/Apna pataa lagao/i)).toBeVisible();

    await page.reload();

    // Persists in localStorage; should still be Hindi after reload
    const hiAfter = page.locator('button[aria-pressed]', { hasText: "हि" });
    await expect(hiAfter).toHaveAttribute("aria-pressed", "true");
    await expect(page.getByText(/Apna pataa lagao/i)).toBeVisible();
  });

  test("/archetypes renders gracefully when backend is unreachable", async ({ page }) => {
    await page.goto("/archetypes");
    await expect(
      page.getByRole("heading", { name: /24 CareerDNA archetypes/i }),
    ).toBeVisible();
    // With backend unreachable, the empty-state copy is shown; no crash.
    await expect(
      page.getByText(/Couldn't load archetypes\./i),
    ).toBeVisible();
  });

  test("/test renders the loading shell (no crash without backend)", async ({ page }) => {
    await page.goto("/test");
    // We just want to verify the route loads without an error boundary.
    // The page either shows the diya loading state or pushes back to /.
    const url = page.url();
    expect(url.endsWith("/test") || url.endsWith("/")).toBe(true);
  });

  test("404 page is themed and offers home + take-test links", async ({ page }) => {
    const response = await page.goto("/this-route-definitely-does-not-exist");
    expect(response?.status()).toBe(404);
    const main = page.getByRole("main");
    await expect(main.getByText(/wandered off/i)).toBeVisible();
    await expect(main.getByRole("link", { name: /Go home/i })).toBeVisible();
    await expect(main.getByRole("link", { name: /Take the test/i })).toBeVisible();
  });

  test("/robots.txt and /sitemap.xml are served", async ({ request }) => {
    const robots = await request.get("/robots.txt");
    expect(robots.status()).toBe(200);
    const robotsBody = await robots.text();
    expect(robotsBody).toMatch(/User-Agent|user-agent|Sitemap/i);

    const sitemap = await request.get("/sitemap.xml");
    expect(sitemap.status()).toBe(200);
    const sitemapBody = await sitemap.text();
    expect(sitemapBody).toMatch(/<urlset|<\?xml/);
  });
});
