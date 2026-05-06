/**
 * Lighthouse CI config for CareerDNA marketing surfaces.
 *
 * Run locally:
 *   npm run lighthouse           # build + start + collect + assert
 *   npm run lighthouse:collect   # collect only against an already-running server
 *
 * Run in CI:
 *   LHCI_SERVER_BASE_URL=http://...  npm run lighthouse
 *
 * Performance + best-practice scores depend on the host CPU/network, so
 * thresholds are deliberately conservative on the first pass — tighten
 * once we have at least 3 historical runs.
 */

const PORT = process.env.LHCI_PORT || "3100";
const BASE_URL = process.env.LHCI_BASE_URL || `http://localhost:${PORT}`;

module.exports = {
  ci: {
    collect: {
      // `autorun` will build, then start the server, wait for `startServerReadyPattern`,
      // collect Lighthouse runs, run assertions, then shut everything down.
      startServerCommand: `sh -c "npm run build > /tmp/lhci-next-build.log 2>&1 && npm run start -- --port ${PORT}"`,
      startServerReadyPattern: "Ready in",
      startServerReadyTimeout: 240_000,
      url: [
        `${BASE_URL}/`,
        `${BASE_URL}/archetypes`,
      ],
      numberOfRuns: 1,
      settings: {
        preset: "desktop",
        // Static landing pages don't need full PWA / robots audits flagged red.
        skipAudits: ["uses-http2"],
        // Use Playwright's bundled Chromium so we don't need a system Chrome.
        chromePath:
          process.env.LHCI_CHROME_PATH ||
          require("@playwright/test").chromium.executablePath(),
      },
    },
    assert: {
      assertions: {
        // Score thresholds (0..1):
        "categories:accessibility": ["error", { minScore: 0.9 }],
        "categories:best-practices": ["warn", { minScore: 0.85 }],
        "categories:seo": ["warn", { minScore: 0.9 }],
        "categories:performance": ["warn", { minScore: 0.7 }],
      },
    },
    upload: {
      target: "temporary-public-storage",
    },
  },
};
