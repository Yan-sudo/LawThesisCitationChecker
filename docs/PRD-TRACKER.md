# PRD 需求拆解 & 进度追踪

> 来源：citation-checker-prd.pdf v0.1 (2026-06-13)
> 最后更新：2026-06-16
> 维护人：Tech Lead (zyx)

## 状态说明

| 标记 | 含义 |
|------|------|
| ✅ 已完成 | 功能完整，有测试覆盖 |
| 🔶 部分完成 | 核心逻辑在，但有缺口 |
| ❌ 未开始 | 完全没有代码 |
| ⏸ 待定 | 需要 PM 确认需求后才能开工 |

---

## Section 4.1 — 引用类型识别

PRD 要求："单个 footnote 需能辨别三种 citation 类型并分流到对应处理器"

### 4.1.1 网页 URL — 直接链接，可在线抓取

| 子需求 | 状态 | 当前实现 | 缺口 |
|--------|------|----------|------|
| 裸 URL 识别 (`https://...`) | ❌ | `citation_parser.py` 无 URL 类型 | 需新增 `CitationType.URL` + `_try_url()` |
| Bluebook 在线引用识别 (`Author, Title, https://... (last visited ...)`) | ❌ | 同上 | 需解析含 URL 的结构化引用 |
| URL 分流到对应处理器 | ❌ | `main.py _fetch_source` 无 URL 分支 | 需新增 fetcher 分发 |

**→ 这就是 M1 需求，已写草稿在 Feedback-Log.md，待 PM 审查**

### 4.1.2 论文 / 学术文献 — 期刊、卷、页等结构化信息

| 子需求 | 状态 | 当前实现 | 缺口 |
|--------|------|----------|------|
| 期刊论文格式识别 | ✅ | `citation_parser._try_article()` 支持 Rule 16 | — |
| 提取作者/标题/卷/期刊/页/年份 | ✅ | `ParsedCitation` dataclass 完整字段 | — |
| 分流到论文处理器 | ✅ | `main.py _fetch_source` → `fetch_article()` | — |

### 4.1.3 法条 / 政策文件 — 成文法、行政政策

| 子需求 | 状态 | 当前实现 | 缺口 |
|--------|------|----------|------|
| 成文法识别 (U.S.C. / C.F.R.) | ✅ | `citation_parser._try_statute()` Rule 12 | — |
| 宪法识别 | ✅ | `citation_parser._try_constitution()` Rule 11 | — |
| 行政法规识别 (agency orders) | ✅ | `citation_parser._try_administrative()` Rule 14.3 | — |
| 立法材料识别 (bills/reports) | ✅ | `citation_parser._try_legislative()` Rule 13 | — |
| Restatement/Model Code 识别 | ✅ | `citation_parser._try_restatement()` Rule 12.9.4 | — |
| 分流到对应处理器 | ✅ | `main.py _fetch_source` 有全部分支 | — |

### 额外已实现的类型（PRD 未明确要求但代码已有）

| 类型 | 状态 | 说明 |
|------|------|------|
| CASE (判例) | ✅ | Rule 10, CourtListener fetcher |
| SHORT_CASE (短引用) | ✅ | Rule 10 short form |
| BOOK (书籍) | ✅ | Rule 15, Google Books fetcher |
| ID (同上引用) | ✅ | Rule 4.1 |
| SUPRA (交叉引用) | ✅ | Rule 4.2 |

---

## Section 4.2 — 来源抓取 (Fetch Authorities)

PRD 要求："根据识别出的引用，从对应网站抓取 authority 原文"

### 4.2.1 抓取渠道

| 渠道 | 状态 | 当前实现 | 缺口 |
|------|------|----------|------|
| 判例 → CourtListener | ✅ | `fetchers/cases.py`，citation-exact + party search | — |
| 成文法 → Cornell Law (USC) | ✅ | `fetchers/statutes.py` | — |
| 行政法规 → eCFR (CFR) | ✅ | `fetchers/statutes.py`（刚修复路由 bug） | — |
| 论文 → CrossRef | ✅ | `fetchers/articles.py` | — |
| 论文 → OpenAlex | ✅ | `fetchers/articles.py` (fallback) | — |
| 论文 → Semantic Scholar | ✅ | `fetchers/articles.py` (fallback) | — |
| 书籍 → Google Books | ✅ | `fetchers/books.py` | — |
| **网页 URL → 直接抓取** | ❌ | 不存在 | **M1 核心需求** |
| **PDF 解析** | ❌ | 不存在 | **M3 核心需求** |
| 宪法 → 链接指向 | ✅ | `main.py` 返回 constitution.congress.gov URL | 无实际文本抓取 |
| 立法材料 → 链接指向 | ✅ | `main.py` 返回 congress.gov URL | 无实际文本抓取 |
| 行政裁定 → 链接指向 | 🔶 | `main.py` 返回 CFTC 首页 URL | URL 太泛，需精确到具体 docket 页面 |

### 4.2.2 HTML 网页正文抽取（去导航/广告）

| 子需求 | 状态 | 说明 |
|--------|------|------|
| 去 HTML 标签 | 🔶 | `cases.py _strip_html()` 只有基础 regex |
| 去导航/广告/侧栏 | ❌ | 没有 readability/trafilatura 级别的正文抽取 |
| 文本清洗（多余空白、段落保持） | 🔶 | `cases.py _get_snippet()` 有基础清洗 |

**→ 网页正文抽取需要更健壮的方案，是 M1 的前置依赖**

### 4.2.3 抓取失败处理

PRD 要求："抓取失败（链接失效、被墙、需登录）时给出明确状态码与原因"

| 子需求 | 状态 | 当前实现 | 缺口 |
|--------|------|----------|------|
| 网络超时 | ✅ | `TIMEOUT = 15` + exception handling | — |
| HTTP 错误码处理 | 🔶 | 有 catch-all exception，但没有区分 404/403/500 | 需要结构化错误码 |
| 付费墙标记 | ✅ | `articles.py` 返回 `"source": "paywalled"` | — |
| 来源不可达降级 | 🔶 | 返回 `not_found` / `error`，Gemini 用 Google Search 兜底 | 可以更明确 |

---

## Section 4.3 — 比对校验 (Comparison)

PRD 要求："提取 parenthetical，与 authority 原文做语义 + 字面对比"

### 4.3.1 Parenthetical 提取

| 子需求 | 状态 | 当前实现 | 缺口 |
|--------|------|----------|------|
| 从脚注中提取括号内文本 | 🔶 | Gemini prompt 里有要求，但没有独立的 Python 提取模块 | 应在 `citation_parser.py` 或新模块中实现 |
| 识别 parenthetical 类型 (holding/stating/quoting) | ❌ | 不存在 | 可增强比对精度 |

### 4.3.2 比对引擎

PRD 技术方案："embedding 相似度 + 关键片段对齐"
实际实现：Gemini API（不是 embedding 方案，而是 LLM 直接判断）

| 子需求 | 状态 | 当前实现 | 缺口 |
|--------|------|----------|------|
| 命题支持度判断 | ✅ | `callGemini()` → `proposition_support` verdict | — |
| Parenthetical 准确度 | ✅ | `callGemini()` → `parenthetical_accuracy` verdict | — |
| Pincite 准确度 | ✅ | `callGemini()` → `pincite_accuracy` verdict | — |
| 相关原文引用 | ✅ | `relevant_quote` 字段 + 客户端验证 | — |
| 比对基础标记 | ✅ | `comparison_basis` (original/secondary/footnote_only) | — |
| 防幻觉机制 | ✅ | text mode 下 quote 必须在 source text 中出现 | — |

### 4.3.3 输出格式

PRD 要求："输出三档结果：一致 / 存疑 / 不一致，并高亮差异片段"

| 子需求 | 状态 | 当前实现 | 缺口 |
|--------|------|----------|------|
| 三档结果 | ✅ | 实际四档：Supports / Questionable / Does not support / Cannot verify | 超出 PRD 要求 |
| 差异高亮 | ❌ | 没有 diff 高亮，只有 `relevant_quote` 原文 | PRD 明确要求 "高亮差异片段" |
| 置信度标记 | ✅ | `confidence: High/Medium/Low` | — |
| 来源链接 | ✅ | `source_url_read` + grounding sources | — |

---

## Section 5 — 技术方案

| 方案 | PRD 计划 | 实际实现 | 差异 |
|------|----------|----------|------|
| 类型分类 | 规则 + 轻量分类模型 | 纯正则规则 (`citation_parser.py`) | 没有 ML 分类器，但准确率尚可 |
| 网页抓取 | HTTP fetch + 正文抽取 | HTTP fetch（各 API） | 正文抽取能力弱 |
| PDF 解析 | 文本层优先；扫描件走 OCR | ❌ 不存在 | M3 核心攻坚 |
| 比对引擎 | embedding 相似度 + 关键片段对齐 | Gemini API 直接判断 | 实际方案更优（LLM 比 embedding 更准） |

---

## Section 7 — 输入/输出

### 输入

| 子需求 | 状态 | 当前实现 |
|--------|------|----------|
| 含脚注的 .docx 文档 | ✅ | `docx_parser.py` 提取脚注 + 正文句子 |
| 脚注文本列表 | ❌ | 只支持 .docx 上传，不支持手动输入脚注文本 |

### 输出

PRD 要求："逐条校验报告，每条包含引用类型、来源抓取状态、比对结果、差异高亮 + 原文链接"

| 子需求 | 状态 | 当前实现 | 缺口 |
|--------|------|----------|------|
| 引用类型 badge | ✅ | `rule-badge` 显示 Bluebook rule + description | — |
| 来源抓取状态 | ✅ | `source_name` + `source_url` + `source_note` | — |
| 比对结果 | ✅ | 四档 verdict + explanation | — |
| 差异高亮 | ❌ | 无 | PRD 要求 |
| 原文链接 | ✅ | `source_url_read` 可点击链接 | — |
| **JSON 导出** | ✅ | `exportResults()` 下载 .json | — |
| **PDF/Word 报告导出** | ❌ | 仅 JSON | M4 需求 |

---

## Section 8 — 验收标准

| 指标 | PRD 要求 | 当前状态 | 缺口 |
|------|----------|----------|------|
| 类型识别准确率 | ≥ 90% | ❓ 无量化数据 | 需要测试集 + 自动化计量 |
| 可达来源抓取成功率 | ≥ 85% | ❓ 无量化数据 | 需要测试集 + 自动化计量 |
| 比对不一致召回率 | ≥ 80% | ❓ 无量化数据 | 需要标注数据集 |
| 误报率可阈值控制 | ❌ | 无可调阈值 | 需要增加 confidence threshold |

**→ 验收标准的量化追踪是长期维护项，需要先建测试集**

---

## Section 9 — 迭代规划 (Milestones)

### M1：URL 类引用（最易闭环）

| 任务 | 状态 | 说明 |
|------|------|------|
| `CitationType.URL` 枚举 | ❌ | 新增 |
| `_try_url()` 解析器 | ❌ | 裸 URL + Bluebook 在线引用 |
| `fetchers/webpages.py` | ❌ | HTTP fetch + 正文抽取 |
| `main.py` URL 分支 | ❌ | 路由到 webpages fetcher |
| UI badge + source link | ❌ | `sourceLabel()` 加 URL |
| 测试 | ❌ | 单元测试 + E2E |

**状态：⏸ 需求草稿已写，待 PM 审查**

### M2：论文类引用支持

| 任务 | 状态 | 说明 |
|------|------|------|
| ARTICLE 类型识别 | ✅ | `_try_article()` 已实现 |
| CrossRef fetcher | ✅ | `fetchers/articles.py` |
| OpenAlex fetcher | ✅ | fallback 链 |
| Semantic Scholar fetcher | ✅ | fallback 链 |
| Abstract 重建 | ✅ | `_reconstruct_abstract()` |
| 标题匹配 | ✅ | `_best_by_title()` |

**状态：✅ 已完成（PRD 写的时候可能没意识到已经实现了）**

### M3：法条 / 政策 PDF 支持

| 任务 | 状态 | 说明 |
|------|------|------|
| STATUTE 类型识别 | ✅ | 已实现 |
| USC fetcher (Cornell) | ✅ | 已实现 |
| CFR fetcher (eCFR) | ✅ | 已实现（刚修 bug） |
| CONSTITUTION 类型 | ✅ | 已实现 |
| ADMINISTRATIVE 类型 | ✅ | 已实现 |
| LEGISLATIVE 类型 | ✅ | 已实现 |
| **PDF 下载** | ❌ | 核心攻坚 |
| **PDF 文本提取** | ❌ | 需要 PyPDF2 / pdfminer |
| **扫描件 OCR** | ❌ | 需要 pytesseract / cloud vision |
| **表格/多栏解析** | ❌ | 政策文件排版复杂 |

**状态：🔶 法条部分已完成，PDF 解析未开始**

### M4：批量处理 + 报告导出

| 任务 | 状态 | 说明 |
|------|------|------|
| 多脚注并行处理 | ✅ | `threading.Thread` 并行 |
| 并发 Gemini 调用 (3 路) | ✅ | `limitedMap(items, 3, fn)` |
| 速率限制重试 | ✅ | `withRetry()` 指数退避 |
| JSON 导出 | ✅ | `exportResults()` |
| **PDF 报告导出** | ❌ | 需要格式化报告模板 |
| **Word 批注回写** | 🔶 | `taskpane/` 有 `applyFootnoteCorrection()` 但仅 Word Add-in |
| **批量文件处理** | ❌ | 当前一次只能上传一个 .docx |

**状态：🔶 批量处理已完成，报告导出部分完成**

---

## 横向功能（PRD 未明确提及但项目已有）

| 功能 | 状态 | 说明 |
|------|------|------|
| Bluebook 格式验证 | ✅ | `bluebook.py` 验证 + 建议格式 |
| Short form 识别 (Id./Supra) | ✅ | Rule 4.1 + Rule 4.2 |
| 多引用脚注拆分 | ✅ | `authority_splitter.py` |
| API Key 本地存储 | ✅ | `localStorage` |
| 来源可靠性标记 | ✅ | `urlReliability()` (high/medium/low) |
| 通用 URL 检测 | ✅ | `isGenericUrl()` 防止首页链接 |
| 搜索结果 URL 过滤 | ✅ | `isSearchUrl()` 排除搜索引擎 |
| Word Add-in (taskpane/) | 🔶 | TypeScript/React 骨架，未集成到主流程 |
| 测试套件 | ✅ | 107 个测试断言（test_core + test_authority_splitter + test_fetchers + test_e2e） |

---

## 可直接开工的任务（不需要 PM 讨论）

按优先级排序：

| # | 任务 | 来源 | 预估工作量 |
|---|------|------|-----------|
| 1 | 抓取错误响应结构化（区分 404/403/500） | PRD §4.2 | 1-2h |
| 2 | Parenthetical 提取模块（从脚注中独立提取括号文本） | PRD §4.3 | 2-3h |
| 3 | 差异高亮 UI（对比 parenthetical 和 source 文本） | PRD §4.3 | 3-4h |
| 4 | 行政裁定的精确 URL（当前返回 CFTC 首页） | 代码质量问题 | 1-2h |
| 5 | 支持手动输入脚注文本（不只能上传 .docx） | PRD §7 | 1-2h |
| 6 | 验收标准量化追踪框架 | PRD §8 | 2-3h |

## 需要 PM 讨论的任务

| # | 任务 | 讨论点 |
|---|------|--------|
| 1 | M1 URL 类引用 | 需求草稿已写，待审查 |
| 2 | M3 PDF 解析 | 技术方案选择（PyPDF2 vs pdfminer vs cloud API） |
| 3 | M4 报告导出格式 | PDF? Word 批注? Excel? |
| 4 | 差异高亮的交互方式 | 内联 diff? 侧边栏? 高亮颜色? |
