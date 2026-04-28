#!/usr/bin/env bash
# CareerDNA Phase 4 smoke runner: v3 backend E2E (pytest) + frontend lint/build.
# Full browser walkthrough (landing → test → results → pay → report) needs
#   start_all.sh dev or two terminals; see printed checklist below.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"

echo "==> Backend: v3 journey pytest (in-memory DB)"
(cd "$ROOT/backend" && pytest tests/test_v3_e2e.py -q)

echo "==> Frontend: lint + production build"
(cd "$ROOT/frontend" && npm run lint && npm run build)

echo ""
echo "✓ Automated smoke passed."
echo ""
echo "Manual UI checklist (http://localhost:3000, API on :3001, PAYMENT_MODE=mock):"
echo "  1. Landing → Start Free Test → /test"
echo "  2. 5 demographic + 40 main questions; milestones ~Q10/Q20/Q30/Q40"
echo "  3. Redirect to /results/[id] — five sections + share"
echo "  4. Unlock → /payment?assessment_id=... → mock redirects to /payment/success"
echo "  5. View full report → /report/[id] paid content"
echo ""
