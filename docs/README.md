# MindPrism Documentation

Living documentation for the MindPrism India career-archetype assessment.

> **Brand history.** Launched as **MindIQ** (2025), renamed **CareerDNA** during the Apr 2026 redesign, consolidated under the umbrella **MindPrism** (May 2026).

---

## 📁 Structure

```
docs/
├── README.md          ← you are here
├── en/                ← English docs (canonical)
├── zh/                ← 中文文档
└── superpowers/       ← historical specs / phase plans (point-in-time, do not edit)
```

Living docs live under `docs/en/` and `docs/zh/` with **identical filenames** (kebab-case lowercase). Update both when you change one.

---

## 📚 Living docs / 现行文档

| Topic | English | 中文 |
| --- | --- | --- |
| Product (what we are, who for, archetype catalog, free/paid) | [`en/product.md`](en/product.md) | [`zh/product.md`](zh/product.md) |
| Architecture (repo layout, data model, decisions ledger) | [`en/architecture.md`](en/architecture.md) | [`zh/architecture.md`](zh/architecture.md) |
| Infrastructure (nginx + horizontal scale-out) | [`en/infrastructure.md`](en/infrastructure.md) | [`zh/infrastructure.md`](zh/infrastructure.md) |
| Roadmap (quarter plan + non-goals) | [`en/roadmap.md`](en/roadmap.md) | [`zh/roadmap.md`](zh/roadmap.md) |
| Deployment — DigitalOcean (10 / 100 / 1k / 10k QPS sized recipes) | [`en/deployment-digitalocean.md`](en/deployment-digitalocean.md) | [`zh/deployment-digitalocean.md`](zh/deployment-digitalocean.md) |
| Deployment — Docker / native (dev + prod, container-by-container) | [`en/deployment-docker.md`](en/deployment-docker.md) | [`zh/deployment-docker.md`](zh/deployment-docker.md) |
| Payment providers (research + integration spec) | [`en/payment-providers.md`](en/payment-providers.md) | [`zh/payment-providers.md`](zh/payment-providers.md) |
| Razorpay runbook (mock → test → live) | [`en/runbook-payments.md`](en/runbook-payments.md) | [`zh/runbook-payments.md`](zh/runbook-payments.md) |
| CI/CD setup (PR gates, LHCI app, secrets) | [`en/ci-cd-setup.md`](en/ci-cd-setup.md) | [`zh/ci-cd-setup.md`](zh/ci-cd-setup.md) |

---

## 📜 Historical (snapshots, do not edit)

| File | What it captures |
| --- | --- |
| `superpowers/specs/2026-04-27-careerdna-india-redesign-design.md` | April 2026 product spec |
| `superpowers/plans/2026-04-27-careerdna-phase-1-backend-foundation.md` | Phase 1 — questions infra + scoring |
| `superpowers/plans/2026-04-28-careerdna-phase-2-content-library.md` | Phase 2 — Pydantic content + 24 cells + careers |
| `superpowers/plans/2026-04-28-careerdna-phase-3-api-payment-auth.md` | Phase 3 — v3 API surface, Razorpay v1, OAuth, share |
| `superpowers/plans/2026-04-28-careerdna-phase-4-frontend-mvp.md` | Phase 4 — Next.js MVP frontend |

---

## ✏️ Editing rules / 编辑规则

- **Filenames are kebab-case lowercase.** `payment-providers.md`, not `PAYMENT_PROVIDERS.md`.
- **Both languages stay in sync.** Whenever you change `en/<file>.md`, update `zh/<file>.md` (and vice-versa). For a major rewrite, mark the lagging side with a `> ⚠️ TRANSLATION NEEDED — last synced 2026-05-XX` banner at the top.
- **Internal links** use relative paths within `docs/` (e.g. `[runbook](runbook-payments.md)` from a sibling).
- **Do not** put doc-style files at the `docs/` root any more — only this README + `superpowers/` history.
- **Code samples** stay English regardless of doc language.

---

## ✏️ 编辑规则（中文）

- **文件名 kebab-case 小写。** 用 `payment-providers.md`，不要 `PAYMENT_PROVIDERS.md`。
- **中英文必须同步。** 改 `en/<file>.md` 时一并改 `zh/<file>.md`，反之亦然。大改时在落后那侧顶部贴一行 `> ⚠️ TRANSLATION NEEDED — last synced 2026-05-XX` 标记。
- **文档内链接**用 `docs/` 内相对路径（如同级 `[runbook](runbook-payments.md)`）。
- **不要**再往 `docs/` 根目录放新的文档式文件 — 根目录只放这个 README 和 `superpowers/` 历史。
- **代码示例**不论文档语言一律英文。
