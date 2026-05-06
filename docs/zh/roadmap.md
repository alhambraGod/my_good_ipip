# MindPrism — 路线图

> 按季度组织的前瞻规划。**Stretch** 标记的项目仅在该季度有余力时上。

---

## Q3 2026 — 正式上线（v1）

**北极星指标：** 7 日滚动 1,000 次有机完成。

| ID | 项目 | 原因 | 验收 |
| --- | --- | --- | --- |
| 1.1 | Razorpay live KYC + ₹49 → ₹99 promo cap 监控 | 没这个运维就在救火 | 前 100 付费用户无人工干预 |
| 1.2 | dev SQLite → MySQL 对齐（Docker compose） | 提早发现 schema 漂移 | `start_all.sh dev` 跑 MySQL |
| 1.3 | Alembic（非加列迁移） | 当前只能 ADD COLUMN IF NOT EXISTS | 第一份迁移落地 |
| 1.4 | 删 `services/scoring_legacy.py` + `questions/question_bank.py` shim | Phase 5 清理 | 旧 v1 路由 + 测试删除；pytest count 下降，coverage 维持 |
| 1.5 | WhatsApp 分享 — Meta 业务模板预审 | 当前用 `wa.me/?text=` 有 200 字限制 | Meta 审核通过的模板触发 |
| 1.6 | WeasyPrint 天城体字体包 | 现在 PDF 里印地文姓名是空白方框 | Acrobat + Preview 都能渲染 |
| 1.7 | Lighthouse 真实 perf 预算 | 当前只 warn | Performance ≥ 0.85 强制（error） |
| 1.8 | Razorpay 完整公司 KYC（Pvt Ltd） | 朋友 KYC v1 上限 ₹5L 累计 GMV | 公司 GSTIN + Pvt Ltd 证书提交 |

## Q4 2026 — 增长（v1.5）

**北极星：** 7 日滚动 10,000 完成；免费→付费 ≥ 0.7%。

| ID | 项目 | 原因 | 验收 |
| --- | --- | --- | --- |
| 2.1 | Hindi UI 完整版（天城体，非 Hinglish） | 二三线触达 | 所有 STRINGS 键都有原生天城体 hi 值 |
| 2.2 | 泰米尔 + 孟加拉 + 泰卢固 + 马拉地 UI | 南印度 + 东印度解锁 | 新增语言切换；先做 label/slogan |
| 2.3 | 结果页 A/B 框架 | 优化分享率 + 转化 | 50/50 分流，14 天 power 计算工具 |
| 2.4 | 在 `/test` Q40 弹 auth modal（替代仅在解锁时） | 提早捕获意图 | A/B：可付费率 ≥ 对照 |
| 2.5 | Dashboard `/dashboard` 历史视图 + 复测 | 重复访问 + "我变了"洞察 | 登录用户能看所有历史评测 |
| 2.6 | DELETE `/api/v3/assessment/{id}` | DPDPA 合规 + 隐私承诺 | `/dashboard` 一键删除 |
| 2.7 | Webhook 幂等性 key | Razorpay 重发可能重复处理 | DB 唯一索引在 `(event_id)` |
| 2.8 | OG 图轮播（每原型 3+ 变体） | 提高分享 CTR | 每 cell A/B 胜出版本上线 |
| 2.9 | 职业库 × 原型刷新（200+ 职业） | 当前长尾稀疏 | 每原型 8-10 职业 |
| 2.10 | 推荐：每分享得 50% off | 低成本推荐回路 | LandingClient 检测 `?ref=` 显示徽章 |
| 2.11 | **Stretch:** 升学顾问 B2B 端 | 学校批量买码 | 兑换码流程 + 机构后台 |

## Q1 2027 — "Smart MindPrism"

**北极星：** 日付费 100 用户；引入更高客单（Career Plan ₹499）目标 5–10% 升级。

| ID | 项目 | 原因 |
| --- | --- | --- |
| 3.1 | LLM 个性化报告（GPT-5 / 端侧 Llama） | 动态文风非模板 |
| 3.2 | "Career Plan ₹499" SKU | 6 个月节奏，周更 nudge |
| 3.3 | 简历 / 面试题生成器 | 面向行动的原型应用 |
| 3.4 | 5 年模拟器 | "选 X 5 年后会怎样" |
| 3.5 | 真实印度公司合作 | 直接招聘 CTA |
| 3.6 | 导师匹配 | Top 匹配原型预约 30 分钟 |
| 3.7 | RIASEC 60 题完整版（付费） | 更严谨的复测 |
| 3.8 | 移动 app（React Native + Expo） | 推送召回，dashboard |
| 3.9 | **Stretch:** 情侣 / 家庭版 | 2 人 → 联合报告，分享回路 |

## Q2 2027 — 平台

| ID | 项目 |
| --- | --- |
| 4.1 | 公开读 API + 开发者门户 |
| 4.2 | SOC 2 Type 1 + DPDPA 审计 |
| 4.3 | 多 region 只读副本 |
| 4.4 | 英语作为第二语言的非印度市场（孟加拉、斯里兰卡、巴基斯坦） |
| 4.5 | 机构主导的管理：HR、升学顾问 |
| 4.6 | **Stretch:** 题库开源 |

## 长期下注（2028+）

- IRT（项目反应理论）校准全部题目，自适应题目难度
- Adaptive testing — 高置信度原型用更少题目
- "Career genome" 纵向：每 6 月复测，绘制漂移
- 语音先行答题（Hindi 语音 → Likert）
- 工作场景集成：Slack bot、Notion 看板、"团队原型组合"报告

## 明确不做

| 不做 | 原因 |
| --- | --- |
| 占星 / 数字命理 / 风水 | 品牌：科学，滑坡风险 |
| MBTI 字母（E/I, S/N, T/F, J/P） | 独立审查信度 < 0.7；用 Holland + Big Five |
| 性能 / IQ 测试 | 超出范围，是另一个产品 |
| 推荐大学 / 学院 | 利益冲突；只推角色不推机构 |
| 推送通知 | v2 mobile 之前不做；邮件 + WhatsApp link 已够 |
| 加密 / Web3 | 与目标人群无关 |

## 跟踪与重新规划

- 每季度：1 页 retro + 北极星指标重置
- 项目跨季度迁移要打日期戳；不能默默腐烂
- 改动 product.md 或 architecture.md 的决策必须连带 docs PR
