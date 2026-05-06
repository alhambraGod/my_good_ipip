# MindPrism — CI/CD setup

How to wire `.github/workflows/ci.yml` into a real PR-gated workflow:
require status checks, post Lighthouse comments on PRs, and (later) ship
to staging on every merge.

---

## 1. Required status checks (PR merge gate)

We have four CI jobs:

- `backend / pytest (py3.11)`
- `backend / pytest (py3.12)`
- `frontend / lint + vitest + build`
- `e2e / Playwright (smoke + a11y)`
- `lighthouse / lhci`

Steps to make them required before merge:

1. Open **Repo → Settings → Branches → Branch protection rules**.
2. Add a rule for `main` (and `master` if you keep both).
3. Tick **Require status checks to pass before merging**.
4. Tick **Require branches to be up to date before merging**.
5. In the search box, paste each job name above and tick it.
6. Save.

GitHub UI screenshot reference (May 2026):

```
[ Branch name pattern  ] main
[x] Require a pull request before merging
[x] Require approvals: 1
[x] Require status checks to pass before merging
    [x] Require branches to be up to date before merging
    Status checks:
      ✓ backend / pytest (py3.11)
      ✓ backend / pytest (py3.12)
      ✓ frontend / lint + vitest + build
      ✓ e2e / Playwright (smoke + a11y)
      ✓ lighthouse / lhci
[x] Require conversation resolution before merging
[x] Do not allow bypassing the above settings
```

> **Tip.** Status check names appear in the picker only **after** the
> first time each job has run on a PR. So push a quick PR first, let
> CI run once, then add the rule.

---

## 2. LHCI — get rich PR comments

`@lhci/cli` posts an anonymous PR comment by default; with a tiny
extra setup it becomes a rich comment with category scores per URL,
diffs vs. the previous run, and a Storage URL with full reports.

### 2a. Easy mode (anonymous, no setup)

`.github/workflows/ci.yml` already passes `LHCI_GITHUB_TOKEN:
${{ secrets.GITHUB_TOKEN }}` — that is enough for **GitHub status
checks** and a basic comment. **No further setup is needed for the
20-LOC PR-comment summary.**

### 2b. Rich mode (with the LHCI GitHub App)

If you want the full Lighthouse summary with embedded scores per URL,
install the LHCI GitHub App on the repo and store its token as a
secret.

1. Visit <https://github.com/apps/lighthouse-ci> and click **Configure**.
2. Choose your org / repo. Grant access (read code + write checks +
   write PRs).
3. After install, copy the JWT-style token shown on the install page.
4. Repo → **Settings → Secrets and variables → Actions → New
   repository secret**:
   - Name: `LHCI_GITHUB_APP_TOKEN`
   - Value: the JWT from step 3
5. Save. Re-run the `lighthouse` job on a PR — the comment now lands
   as a rich PR review comment, not a status check.

### 2c. Optional: long-running LHCI server (history + diff)

For projects that want LHCI dashboards (perf trend over time), run
the [LHCI Server](https://github.com/GoogleChrome/lighthouse-ci/tree/main/packages/server)
on a tiny Droplet and point CI to it via:

```yaml
env:
  LHCI_SERVER_BASE_URL: https://lhci.mindprism.in
  LHCI_BUILD_TOKEN:     ${{ secrets.LHCI_BUILD_TOKEN }}
```

Out of scope for the launch tier; revisit at Tier 2 (Growth).

---

## 3. Secrets to configure on the repo

| Secret | Purpose | Required for |
| --- | --- | --- |
| `LHCI_GITHUB_APP_TOKEN` | Rich Lighthouse PR comments | optional |
| `LHCI_BUILD_TOKEN` | If you stand up an LHCI server | optional |
| `DOCKER_USERNAME` / `DOCKER_TOKEN` | Push images to a registry | when we add the deploy job |
| `DIGITALOCEAN_ACCESS_TOKEN` | Push images to DOCR + `kubectl set image` | when we wire CD |
| `STAGING_SSH_HOST` / `STAGING_SSH_KEY` | Direct SSH deploy (Bootstrap tier) | when we wire `deploy-staging.yml` |

Add via Repo → Settings → Secrets and variables → Actions.

---

## 4. Adding a deploy job (Bootstrap tier)

Sketch for `.github/workflows/deploy-staging.yml`:

```yaml
name: Deploy staging
on:
  push:
    branches: [main]
  workflow_dispatch:

jobs:
  ssh-deploy:
    runs-on: ubuntu-latest
    needs: []
    steps:
      - uses: actions/checkout@v4
      - name: SSH into Droplet + pull + restart
        uses: appleboy/ssh-action@v1
        with:
          host: ${{ secrets.STAGING_SSH_HOST }}
          username: ${{ secrets.STAGING_SSH_USER }}
          key: ${{ secrets.STAGING_SSH_KEY }}
          script: |
            set -euo pipefail
            cd /opt/mindprism
            git fetch --depth=1 origin main
            git reset --hard origin/main
            sudo bash deploy/start_docker.sh prod --build
            curl -fsS http://localhost/api/health || (sudo bash deploy/stop_docker.sh prod && exit 1)
```

This job:
1. Pulls the latest `main` onto the Droplet.
2. Re-builds + restarts the compose stack.
3. Verifies the health endpoint, rolls back if it fails.

Wire it after the bootstrap-tier Droplet is alive — see
`deployment-digitalocean.md` Tier 0.

---

## 5. CI gotchas we already hit (sticky notes)

- **Node 25 + happy-dom localStorage.** Vitest's setup polyfills
  `localStorage` before tests; if your CI image uses Node 25 stock,
  the polyfill is essential. Already done in `vitest.setup.ts`.
- **WeasyPrint native libs.** `apt-get install -y libpango-1.0-0
  libpangoft2-1.0-0 libharfbuzz-subset0 libcairo2 libgdk-pixbuf-2.0-0`
  on the backend job; missing these gives a cryptic
  `OSError: cannot load library 'libgobject-2.0-0'`.
- **Playwright Chromium cache.** First run downloads ~90 MB. The
  workflow caches `~/.cache/ms-playwright` keyed on
  `frontend/package-lock.json` so subsequent runs are seconds.
- **Lighthouse needs Chromium too.** Same cache + the autorun config
  resolves `playwright/chromium` executable path so we don't ship a
  separate Chrome.
- **Coverage gate.** `pytest.ini` has `--cov-fail-under=85`. If a PR
  drops coverage, the backend job goes red and merge is blocked.

---

## 6. Local pre-push hook (optional, recommended)

Install [`pre-commit`](https://pre-commit.com) and add a hook so the
same gates run before push:

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: pytest
        name: pytest --no-cov
        entry: bash -c 'cd backend && pytest -q --no-cov'
        language: system
        pass_filenames: false
        stages: [pre-push]
      - id: vitest
        name: vitest run
        entry: bash -c 'cd frontend && npm test'
        language: system
        pass_filenames: false
        stages: [pre-push]
      - id: lint
        name: eslint
        entry: bash -c 'cd frontend && npm run lint'
        language: system
        pass_filenames: false
        stages: [pre-push]
```

Then `pre-commit install --hook-type pre-push`.
