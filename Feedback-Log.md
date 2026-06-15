# Feedback Log

> **怎么用：** 每次测试完在顶部加一条新记录。一句话标题 + 模板三要素（Fact Pattern / Expected / Actual）。
>
> 更多细节参考 `Vibe-Coding-Playbook.md`。

---

<!-- 
  ==========================================
  模板（复制下面整块来用）
  ==========================================

## [YYYY-MM-DD] 标题：一句话总结

**类型：** `UI/UX` | `Search精度` | `逻辑规则` | `数据缺失` | `性能`

**测试用例 (Fact Pattern)：**
> （把引用原文贴这里）

**预期结果 (Expected)：**
> （应该发生什么）

**实际结果 (Actual)：**
> （实际发生了什么）

**建议修复方向：**
> （你的直觉，可选但欢迎写）

  ==========================================
-->

---

## [2026-06-16] M1 需求草稿：URL 类引用支持（待 PM 审查）

**类型：** `需求`
**状态：** `待 PM 审查` — Tech Lead 代写草稿，PM 审查后确认/修改再开始开发

**来源：** citation-checker-prd.pdf Section 4.1 + Section 9 (M1)

---

### 用户画像 & 痛点 (Persona & Pain Point)

> 我是 JD 学生，正在写一篇关于网络隐私权的论文。我的脚注里有不少引用直接是网页链接（如法院官网的判决页面、政府机构的公告页面），也有些是 Bluebook 标准格式的在线来源引用（如 "John Doe, *Privacy in the Digital Age*, https://example.com/article (last visited June 2026)"）。
> 目前系统完全不认识 URL 类型的引用——`citation_parser.py` 会返回 `UNKNOWN`，然后只能依赖 Gemini Google Search 去猜。这导致：
> 1. URL 引用没有 Bluebook rule badge，UI 上显示 "Format not recognised"
> 2. 没有预抓取的 source snippet，Gemini 比对质量下降
> 3. 没有 source URL 链接，我无法一键打开原始来源验证

### 使用场景 (User Scenario)

**场景 A — 裸 URL**
> 1. 我上传一篇论文 .docx，脚注里有：`https://www.supremecourt.gov/opinions/20pdf/19-715_8b59.pdf`
> 2. 系统识别这是一个 URL 类引用
> 3. 系统抓取该网页/PDF 的内容
> 4. Gemini 比对正文命题和抓取到的原文，给出 Supports / Does not support 判定

**场景 B — Bluebook 格式的在线来源**
> 1. 脚注里有：`John Doe, Privacy in the Digital Age, https://www.eff.org/deeplinks/2024/01/privacy (last visited Jan. 15, 2024)`
> 2. 系统识别这是 URL 类引用，提取出标题、作者、URL
> 3. 系统抓取该网页的正文内容
> 4. Gemini 比对并额外检查 parenthetical 和 last visited 日期

### 我期望产品做到

1. `citation_parser.py` 新增 `CitationType.URL`，能识别两种格式：
   - 裸 URL：`https://...` 或 `http://...`
   - Bluebook 在线引用：包含 URL 的结构化引用（含 last visited 日期）
2. 新建 `fetchers/webpages.py`，从 URL 抓取网页正文（去导航/广告）
3. 抓取失败时（404、超时、需登录），明确标注 "Cannot verify" 并给出原因
4. UI 上 URL 类引用显示对应的 badge 和可点击的 source link

### 为什么这个需求重要

URL 引用是法律论文中越来越常见的引用形式（在线判决、政府公告、NGO 报告）。PRD 将 M1 定义为"最易闭环"的里程碑，是验证整个系统端到端流程的最佳起点。

### 验收标准 (Acceptance Criteria)

- [ ] AC1: 输入裸 URL `https://www.supremecourt.gov/opinions/...` → 系统识别为 URL 类型，badge 显示 "URL"
- [ ] AC2: 输入 Bluebook 在线引用 `Author, Title, https://... (last visited ...)` → 识别为 URL 类型，提取标题和作者
- [ ] AC3: 抓取成功的 URL → 返回 source snippet 和 source_url，Gemini 比对正常工作
- [ ] AC4: 抓取失败的 URL（404/超时） → 不崩溃，显示 "Cannot verify" + 失败原因
- [ ] AC5: UI 上 URL 类引用显示可点击的 source link
- [ ] AC6: 已有的 36 个测试用例全部通过（不破坏现有功能）

---

### PM 审查说明

**PM 请确认以下问题：**

1. 上面的两个场景（裸 URL / Bluebook 在线引用）是否覆盖了你需要的主要用例？还有其他吗？
2. AC1-AC6 的验收标准是否合理？需要增加或修改吗？
3. 你有没有现成的 .docx 测试文件包含 URL 类引用？如果没有，我可以造一个。
4. 确认后请把状态从 `待 PM 审查` 改为 `已确认`，Tech Lead 即可开始开发。

---

## [2026-05-16] 初始日志 — Playbook 生效日

**类型：** `文档`

**备注：** 本文件即日起作为所有测试反馈的唯一书面记录。手机微信不再作为 bug 追踪渠道。

