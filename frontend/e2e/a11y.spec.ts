import { expect, test } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

/**
 * Accessibility smoke. Uses axe-core's WCAG 2.1 AA + best-practice rules.
 * Tags can be tightened over time:
 *   - "wcag2a" / "wcag2aa" — strict statutory level
 *   - "wcag21aa"           — current target
 *   - "best-practice"      — opinionated; useful warnings
 *
 * The aim is **zero violations** on chrome surfaces; data-driven pages
 * (results / report) are out of scope here because they need backend.
 */

const PAGES: Array<{ path: string; label: string }> = [
  { path: "/", label: "landing" },
  { path: "/archetypes", label: "archetypes index" },
  { path: "/this-is-a-404", label: "404 page" },
];

for (const { path, label } of PAGES) {
  test(`${label} has no axe violations (WCAG 2.1 AA)`, async ({ page }, testInfo) => {
    await page.goto(path);
    // Give Framer Motion time to settle so axe doesn't flag opacity-0 nodes.
    await page.waitForTimeout(400);

    const results = await new AxeBuilder({ page })
      .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
      .analyze();

    if (results.violations.length > 0) {
      await testInfo.attach("axe-violations.json", {
        body: JSON.stringify(results.violations, null, 2),
        contentType: "application/json",
      });
    }
    expect(
      results.violations,
      `axe violations on ${label}: ${results.violations.map((v) => v.id).join(", ")}`,
    ).toEqual([]);
  });
}

test("language toggle keeps the page accessible after switching to Hindi", async ({ page }, testInfo) => {
  await page.goto("/");
  await page.locator('button[aria-pressed]', { hasText: "हि" }).click();
  await page.waitForTimeout(200);
  const results = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
    .analyze();
  if (results.violations.length > 0) {
    await testInfo.attach("axe-violations-hi.json", {
      body: JSON.stringify(results.violations, null, 2),
      contentType: "application/json",
    });
  }
  expect(results.violations).toEqual([]);
});
