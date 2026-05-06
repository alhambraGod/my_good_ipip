# MindPrism — CI/CD 配置

把 `.github/workflows/ci.yml` 串到真实的 PR 门禁工作流：要求状态检查、PR 上跑 Lighthouse 评论、（之后）每次 merge 部署到 staging。

---

## 1. 必需状态检查（PR merge 门禁）

我们有 5 个 CI job：

- `backend / pytest (py3.11)`
- `backend / pytest (py3.12)`
- `frontend / lint + vitest + build`
- `e2e / Playwright (smoke + a11y)`
- `lighthouse / lhci`

把它们设成 merge 前必通过：

1. **Repo → Settings → Branches → Branch protection rules**
2. 给 `main`（如果保留 `master` 也加）添加规则
3. 勾 **Require status checks to pass before merging**
4. 勾 **Require branches to be up to date before merging**
5. 在搜索框逐个粘上面 5 个 job 名并勾选
6. 保存

参考截图（2026 年 5 月）：

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

> **提示。** 状态检查名只在每个 job **第一次**在 PR 上跑过之后才会出现在选择器中。先开个简单 PR 让 CI 跑一次，再回来加规则。

---

## 2. LHCI — PR 富评论

`@lhci/cli` 默认匿名 PR 评论；加少量配置可以变成完整的富评论：每 URL 各分类评分、跟上一次 run 的 diff、Storage 链接到完整报告。

### 2a. 简单模式（匿名，无配置）

`.github/workflows/ci.yml` 已经传 `LHCI_GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}` — 这足以用于 **GitHub status check** 和基础评论。**无需进一步配置。**

### 2b. 富评论（LHCI GitHub App）

想看每 URL 的完整 Lighthouse 摘要 + 嵌入分数，安装 LHCI GitHub App 并把 token 放 secret：

1. 访问 <https://github.com/apps/lighthouse-ci> 点 **Configure**
2. 选 org / repo，授权（read code + write checks + write PRs）
3. 安装后 copy 安装页显示的 JWT token
4. Repo → **Settings → Secrets and variables → Actions → New repository secret**：
   - Name: `LHCI_GITHUB_APP_TOKEN`
   - Value: 上一步的 JWT
5. 保存。在 PR 上 re-run `lighthouse` job — 评论变成富 PR review

### 2c. 长寿 LHCI server（历史 + diff）

想看 LHCI 看板（perf 趋势），在小 Droplet 上跑 [LHCI Server](https://github.com/GoogleChrome/lighthouse-ci/tree/main/packages/server)，CI 通过：

```yaml
env:
  LHCI_SERVER_BASE_URL: https://lhci.mindprism.in
  LHCI_BUILD_TOKEN:     ${{ secrets.LHCI_BUILD_TOKEN }}
```

启动档（Tier 0）暂不做；Tier 2 (Growth) 时再说。

---

## 3. 仓库 secrets 清单

| Secret | 用途 | 必需性 |
| --- | --- | --- |
| `LHCI_GITHUB_APP_TOKEN` | Lighthouse PR 富评论 | 可选 |
| `LHCI_BUILD_TOKEN` | LHCI server 上传 token | 可选 |
| `DOCKER_USERNAME` / `DOCKER_TOKEN` | 推镜像到注册表 | 加 deploy job 时 |
| `DIGITALOCEAN_ACCESS_TOKEN` | 推镜像到 DOCR + `kubectl set image` | 接 CD 时 |
| `STAGING_SSH_HOST` / `STAGING_SSH_KEY` | SSH 部署（Bootstrap 档） | 接 `deploy-staging.yml` 时 |

通过 Repo → Settings → Secrets and variables → Actions 添加。

---

## 4. 加 deploy job（Bootstrap 档）

`.github/workflows/deploy-staging.yml` 草稿：

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
      - name: SSH 进 Droplet + pull + restart
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

这个 job：
1. 把最新 `main` 拉到 Droplet
2. 重建 + 重启 compose stack
3. 验证 health 端点，失败回滚

bootstrap-tier Droplet 起来后再接 — 见 `deployment-digitalocean.md` Tier 0。

---

## 5. CI 我们已经踩过的坑（便签）

- **Node 25 + happy-dom localStorage。** Vitest setup 在测试前 polyfill `localStorage`；CI 镜像如果用 Node 25 stock，这个 polyfill 是必需的。已在 `vitest.setup.ts`
- **WeasyPrint 系统库。** backend job 上要 `apt-get install -y libpango-1.0-0 libpangoft2-1.0-0 libharfbuzz-subset0 libcairo2 libgdk-pixbuf-2.0-0`；缺会出 `OSError: cannot load library 'libgobject-2.0-0'`
- **Playwright Chromium 缓存。** 第一次跑下载 ~90 MB。workflow 缓存 `~/.cache/ms-playwright`，key 用 `frontend/package-lock.json`，下次几秒
- **Lighthouse 也要 Chromium。** 同样缓存 + autorun 配置解析 `playwright/chromium` 路径，无需单独装 Chrome
- **Coverage 门禁。** `pytest.ini` `--cov-fail-under=80`。PR 让覆盖率掉进就红，merge 被挡

---

## 6. 本地 pre-push hook（可选推荐）

装 [`pre-commit`](https://pre-commit.com)，加 hook 让同一组门禁在 push 前跑：

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

然后 `pre-commit install --hook-type pre-push`。
