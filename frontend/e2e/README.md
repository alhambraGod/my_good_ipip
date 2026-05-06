# Playwright e2e

End-to-end smoke checks for the CareerDNA frontend chrome (Next.js 16). The
Playwright runner builds the app and serves it on port 3100 by default,
pointed at a deliberately-unreachable backend so we exercise the
"backend down" graceful-degradation path. This is enough to catch:

- Build / hydration regressions
- Header + nav rendering
- Landing hero + CTA + FAQ
- Language toggle persistence
- `/archetypes` empty-state copy
- 404 page chrome
- `/robots.txt` + `/sitemap.xml`

## Run locally

```bash
cd frontend
npm run test:e2e          # headless
npm run test:e2e:ui       # Playwright Inspector
```

The first run downloads Chromium (~90 MB).

## Run with a real backend

For full quiz → results flows you need both servers up:

```bash
# in one shell
bash start_all.sh dev

# in another shell
cd frontend
E2E_NO_WEBSERVER=1 \
  E2E_BASE_URL=http://localhost:3000 \
  E2E_API_URL=http://localhost:3001 \
  npm run test:e2e
```

The default `E2E_API_URL` (`http://127.0.0.1:1`) is unreachable on purpose
so the "backend down" smoke runs deterministically without DB seeds.

## Adding new specs

- Files: `e2e/*.spec.ts`
- Avoid hard-coded archetype IDs / cell content (those need backend up).
- Prefer `getByRole` / `getByText` over CSS selectors so refactors are
  resilient.
