# MindPrism — 产品文档

> 产品定位、目标人群、用户旅程的权威说明。与 `architecture.md`（系统设计）和 `roadmap.md`（演进规划）形成三件套。
>
> _品牌沿革：2025 年作为 **MindIQ**（仅 Big Five 测评）发布，2026 年 4 月在 IPIP-NEO + Holland RIASEC 重设期间改名为 **CareerDNA**，2026 年 5 月统一为伞形品牌 **MindPrism**。_

---

## 1. 一句话定位

5 分钟、有科学背书、专为印度白领与 Gen-Z 打造的人格 + 职业测试。45 题 → 24 个原型之一 → INR 计价的匹配职业 — 免费看原型，付费 ₹49（早鸟）/ ₹99（标准）解锁完整报告。

## 2. 为什么做这个产品

- **印度受众长期被忽视。** 西方职业测试（16Personalities、MBTI 衍生品）使用美元薪资和文化无关的提示（"你会加入兄弟会吗？"），印度用户共鸣度差。
- **两个未被解决的张力：**
  1. *Buzzfeed 测试*病毒式但凭感觉；*真正的心理测量工具*（RIASEC、Big Five）严肃但乏味、仅英文。
  2. 印度家庭把"职业 = IIT/IIM/MBBS"，"什么适合你"是一个被严重低估的决策维度。
- **价格现实。** ₹49（约 $0.60）正中目标 — 高中零花钱级别；即时解锁；西方 $9.99 测试做不到的转化在这里能做到。

## 3. 目标人群

| 细分 | 触发场景 | 关键钩子 |
| --- | --- | --- |
| 11–12 年级学生 | "选理科还是商科？" | Holland 适配 + 父母期望框架 |
| 工科本科 | 编程工作 vs UPSC vs MBA | 原型 + 印度公司匹配清单 |
| 早期职场（22–30） | 从 TCS / WITCH 跳到创业公司 | OCEAN + 城市分级薪资带 |
| 转行者 / 复出者 | 职业第二春焦虑 | 优势 / 成长建议 + 朋友圈分享 |

地理覆盖：印度一二线城市 + 海外印度人；主要分发渠道为 **WhatsApp、Instagram Stories、X (Twitter India)**。v1 出英文 + Hindi（罗马字 + 部分天城体）切换。

## 4. 理论基础

| 模型 | 提供什么 | 我们如何使用 |
| --- | --- | --- |
| **Holland RIASEC**（J. L. Holland，1959–1997，3 万+ 引用） | 6 种职业兴趣构成六边形：Realistic / Investigative / Artistic / Social / Enterprising / Conventional | 主导前两类型 → 6×4 = **24 个原型格子**（如 `IA` = Investigative-Artistic），配印度风味标签 |
| **Big Five (IPIP-NEO)** | 5 维人格：Openness / Conscientiousness / Extraversion / Agreeableness / Neuroticism | OCEAN 0–100 分 + 百分位，用于付费报告中的细颗粒个性化 |
| **MAST**（多元原型显著触发） | 统计上的"罕见画像"探测器 | 多 σ 极端者（OCEAN 顶 + RIASEC 尾巴）被标记为稀有原型亚型，奖励病毒分享 |
| **IBTI 调性**（内部病毒框架） | "毒舌式" Hinglish 幽默 slogan | 注入到原型标签 + slogan，绝不污染科学题面 |

## 5. 24 个原型

24 格 = 6 RIASEC 主类型 × 4 副类型（六边形相邻）。每个格子配印度本土化内容：

- `cell_id`（2 字母）、`label_en`、`label_hi`
- `slogan_en`（一句话）、`core_insight_en`（4–6 句）、`deep_description_en`（1500+ 字）、`strengths_en[5]`、`growth_tips_en[5]`
- `career_directions[]`（5+ 匹配职业）
- `rarity_pct`（人群频次）

样例（完整内容在 `backend/content/data/cells/*.json`）：

| Cell | 标签 | Slogan |
| --- | --- | --- |
| **IA** | The 3AM Chai Philosopher | "你过度思考自己的过度思考。这句话也是。" |
| **EC** | The Spreadsheet Founder | "Vision plus VLOOKUP." |
| **SE** | The Glue | "你让人聚在一起。" |
| **AS** | The Reluctant Performer | "藏在宿舍被子下的天赋。" |
| **RC** | The Quiet Builder | "修好别人懒得修的东西。" |
| **CI** | The Pattern Hunter | "电子表格就是你的宝莱坞。" |

## 6. 职业库

`backend/content/data/careers/library.json` 收录 ~78 个职业，每个含：

- `name_en` + `name_hi`（90% 含天城体）
- `tagline_en`（一句话角色描述）
- `why_match`：以原型 `cell_id` 为键，每个原型的"为什么适合"文案不同
- `salary_inr`：`entry / mid / senior` 用 lakh / crore 表达
- `indian_companies`：真实雇主（Razorpay、Swiggy、TCS、Marwari 商业家族等）
- `education_path`：典型路径 / 证书
- `city_distribution`：班加罗尔 / 海得拉巴 / 孟买 / NCR / 浦那 / 二线首府 / 远程

职业库是**单向引用**：原型 cell 指向职业，职业可被**多个** cell 用不同 `why_match` 引用。`find_dormant_why_match_entries()` 校验器检测"被职业引用但 cell 已经不再链回"的情况。

## 7. 用户旅程

```
Landing /                                         ← 番红花-绿渐变 hero、24 原型墙、FAQ、印度风格、EN/Hindi 切换
        │
        ▼
答题 /test                                       ← 5 demographic + 40 动态 Likert
                                                   - 1-5 键盘快捷键
                                                   - localStorage 进度自动保存
                                                   - 后退一题 / 重新开始
                                                   - Q10 / 20 / 30 / 40 milestone 鼓励语（Hinglish）
        │
        ▼
免费结果 /results/[id]                            ← 5 屏滚动：
                                                   1. 原型卡 + 稀有度
                                                   2. Holland 雷达
                                                   3. 核心洞察
                                                   4. Top 1 职业 + 4 锁定预览
                                                   5. 双 CTA（分享 + 解锁）
        │
        ▼
软付费墙 /payment                                 ← 实时价格（₹49 早鸟 / ₹99 标准）+ 名额倒计时
                                                  + 多支付选择（Razorpay / UPI / Cashfree / PayU）
        │
        ├── /payment/success                      ← 验证 Razorpay 签名、写 paid=True
        │
        ▼
深度报告 /report/[id]                             ← Sticky TOC + 滚动 spy + Hindi 感知
                                                   - 原型深度（1500+ 字）
                                                   - 优势 × 成长建议
                                                   - OCEAN + 百分位
                                                   - 5+ 职业匹配（INR 薪资、why-match、雇主、城市）
                                                   - PDF 下载（WeasyPrint）
        │
        ▼
分享                                              ← `/s/{code}` 短链 + `/api/og/[id]` Edge ImageResponse 卡片
                                                   + 预生成的 WhatsApp / X 文案
```

## 8. 免费 vs 付费

| | 免费结果页 | 付费深度报告 |
| --- | --- | --- |
| 原型 cell + 标签 | ✓ | ✓ |
| Slogan + 稀有度 | ✓ | ✓ |
| Holland 雷达 | ✓ | ✓ |
| 核心洞察（4 句） | ✓ | ✓ |
| **Top 1 职业匹配** | ✓（含薪资带） | ✓ |
| **其余 4+ 职业** | 锁定预览 | ✓ 解锁 |
| 深度文（1500+ 字） | — | ✓ |
| 优势 × 成长建议 | — | ✓（各 5 条） |
| OCEAN 全画像 + 百分位 | — | ✓ |
| 每个职业的教育 + 城市 + 公司 | — | ✓ |
| PDF | — | ✓ |
| 分享文案 + OG 卡 | ✓ | ✓ |

软付费墙设计：仅约 6% 真正有价值的内容被锁；免费视图本身就足够分享。

## 9. 定价

| 档位 | INR | 大约美元 | 状态 |
| --- | --- | --- | --- |
| **早鸟（promo）** | ₹49 | $0.60 | 前 1,000 份报告，之后自动转为标准价 |
| **标准** | ₹99 | $1.20 | 名额耗尽之后 |

`GET /api/v3/payment/price` 返回 `{ amount_inr, promo_active, promo_remaining, promo_cap }`，付费页渲染实时进度条。

未来：地区折扣、礼品码、B2B 批量（学校升学顾问）。

## 10. 本地化与文化适配

- **语言。** 英语（主）+ Hindi（Hinglish + 职业名天城体），通过 `<LangToggle />` 切换并写入 `localStorage`。v2 添加泰米尔 / 孟加拉 / 泰卢固 / 马拉地。
- **文化标记融入。**
  - 称谓："Sharma ji 的儿子"、"Aunty"
  - 家庭 / 社会：联合家庭压力、EMI 数学、log kya kahenge、IIT/IIM 剧本、"安定"压力
  - 城市：一线（班加罗尔、孟买、Delhi-NCR、海德拉巴、钦奈、浦那、加尔各答）+ 二线首府跟踪
  - 公司：Razorpay、Swiggy、Zomato、Flipkart、Paytm、Tata、Infosys、TCS、Wipro（"WITCH"）、Reliance、Marwari 贸易网络、政府国企
- **避免敏感话题。** 无宗教、无种姓、无政党、无族群刻板印象。

## 11. 分享面

| 表面 | 钩子 |
| --- | --- |
| 免费结果页 | 预填 WhatsApp 分享文案 + "分享到 WhatsApp" CTA |
| 结果 OG 图 | `/api/og/[id]` 返回 1200×630 PNG，带原型 ID、标签、slogan、品牌条 |
| 短链 | `/s/{code}` 302 重定向到 `/results/[id]`；`ShortLink` 行计点击数 |
| 原型详情页 | 长尾 SEO；每个 cell 一个 URL（共 24 个），全部上 sitemap |
| Sitemap | `/sitemap.xml` 列 `/`、`/archetypes`、所有 `/archetypes/[cell]`，每周 / 月更新 |

## 12. 隐私与数据伦理

- 无第三方广告像素
- 无数据转售
- 免费路径只存：匿名答案、得分、原型、可选短链 code；不强制登录
- 付费路径：可选关联 `UserProfile`（Google / Facebook / WhatsApp / Email）以便邮件接收报告
- `/dashboard` 显示用户自己的历史评测；管理员端点不暴露其他用户的答案
- "邮件 support 删除我的数据"是当前手工通道；v2 上线 `DELETE /api/v3/assessment/{id}`

## 13. 合规与风险

- **非临床评估。** 每页 footer、付费页、报告页都有免责声明
- **Razorpay KYC。** v1 用印度朋友个人 KYC 作为商户；累计 GMV 跨 ₹5L 之前转 Pvt Ltd 公司 KYC
- **GDPR / DPDPA。** 数据最小化已落地（免费阶段无 PII）；DPDPA 第 8 条（更正与删除权）写入隐私文案；ticket 通道与删除请求复用同一邮箱
