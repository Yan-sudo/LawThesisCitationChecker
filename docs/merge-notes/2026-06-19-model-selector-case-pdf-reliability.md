# Merge Note: 模型选择 + 案例 PDF 链接 + 三项准确性修复

**日期**: 2026-06-19
**Branch**: feature/design_zyx → master
**Commit**: 5c75737, ec563fa, bca996c

---

## 📋 本次做了什么（一句话）

修好了"模型停用导致整个检查跑不起来"的问题，给案例引用加了可以直接打开的判决书 PDF 链接，并修掉了三个让大量引用错误地显示成 "Unverified / Cannot verify" 的根因问题。

---

## 🎯 对应的需求/Bug

- 修复 Feedback-Log.md [2026-06-19] `gemini-2.0-flash` 模型被 Google 停用，报错 "This model is no longer available"
- 修复 Feedback-Log.md [2026-06-19] 大量脚注显示 "No JSON in Gemini response"
- 修复 Feedback-Log.md [2026-06-19] 作者自己写的分析性脚注被当成引用，污染 Unverified 计数
- 修复 Feedback-Log.md [2026-06-19] "supra note N" 短引用无法核实
- 对应需求：让用户能直接查看案例判决书原文（参考 Case Viewer 的做法）

---

## 🧪 PM 需要测试什么

### 测试步骤（一步步来）

1. 启动服务器: `cd backend && python3 main.py`
2. 打开 http://localhost:8000
3. 第 1 步面板里现在多了一个 **"Gemini model" 下拉框** —— 默认是 `gemini-2.5-flash`，确认能选择
4. 填入 Gemini API Key，上传一篇含案例、文章、以及大段叙述性脚注的论文（例如 `Taxing_Prediction_Markets_FINAL.docx`）
5. 点击 "Check Citations"，等待跑完
6. 重点观察：案例类脚注、叙述性脚注（如纯计算/纯说明文字）、以及 "supra note X" 这类脚注

### 预期结果

- **模型问题**：不再出现 "model is no longer available" 报错，检查能正常跑完
- **案例 PDF**：成功核实的案例（如 Gregory v. Helvering）卡片头部会出现红色 **"PDF ↗"** 标签，展开后有 **"View original document (PDF)"** 链接，能打开判决书原文
- **JSON 报错大幅减少**：之前满屏的 "No JSON in Gemini response" 基本消失
- **叙述性脚注**：作者自己的分析、计算、"User should verify…" 这类文字会被标成灰色的 **"Not a citation"**，单独计入新的 "Not a citation" 统计格，**不再算进 Unverified**
- **supra 引用**："Bradford, supra note 14" 会自动找到第 14 个脚注里 Bradford 的完整引用并去核实，而不是直接 "Cannot verify"

### 测试文件

| 文件名 | 用途 | 路径 |
|--------|------|------|
| Taxing_Prediction_Markets_FINAL.docx | 综合场景（案例/文章/叙述/supra 都有） | PM 本地 |

---

## 📝 已知限制 / 不完美之处

> **重要**: 这里列出当前版本的局限性，PM 在验收时不应该测试这些场景

- [ ] PDF 链接只对**案例（case）**有效，来自 CourtListener；statute / article / book 暂不返回 PDF
- [ ] "Not a citation" 的判定是启发式：无任何 Bluebook 引用特征 **且** 词数 ≥ 12 才会判定；少于 12 词的无特征片段仍保留为 "Unrecognised"，交给 Gemini 搜索（保守策略，避免误杀真引用）
- [ ] supra 解析依赖被引用的脚注本身能被正确解析；如果 note N 里的完整引用我们也没解析出来，supra 仍会回退到 "Cannot verify"
- [ ] `id.`（紧邻上一条引用）尚未做自动解析，本次只做了 supra
- [ ] 截断的 Gemini 响应会尽力修复 + 重试，但极端情况下仍可能解析失败（会给出更清晰的报错并自动重试一次）

---

## 🔄 对已有功能的影响

- [x] ⚠️ 修改了已有行为:
  - **Gemini 调用模型**从写死的 `gemini-2.0-flash` 改为用户可选（默认 `gemini-2.5-flash`），并提高了 `maxOutputTokens`、压低了 thinking 预算 —— 输出格式不变，但响应更完整、更省 token
  - **JSON 解析逻辑**重写为容错版（剥离 markdown 代码块包裹 + 修复截断），所有引用的核实结果都经过这条路径，PM 应整体回归一遍核实结果是否正常显示
  - **统计口径**新增 "Not a citation" 一栏，Unverified 数字会比以前小（因为叙述性脚注被移出去了）—— 这是预期变化

---

## 📊 技术细节（PM 可跳过）

### 改动文件清单

| 文件 | 改动类型 | 说明 |
|------|---------|------|
| backend/index.html | 修改 | 模型下拉框 + 持久化；案例 PDF 标签/链接；容错 JSON 解析（extractGeminiJson/repairTruncatedJson）；提高 maxOutputTokens、设 thinkingBudget；"Not a citation" 渲染与统计 |
| backend/fetchers/cases.py | 修改 | 一次性取 opinion，派生 `pdf_url`（优先 CourtListener 存储副本，回退法院原始 download_url） |
| backend/main.py | 修改 | 透传 `source_pdf_url`；新增 `_build_note_index` / `_resolve_supra`；`_fetch_source` 处理 NON_CITATION 与 supra 解析 |
| backend/citation_parser.py | 修改 | 新增 `CitationType.NON_CITATION` 与 `_try_non_citation()` 启发式检测 |
| backend/gemini.py | 修改 | 注释/模型字符串同步为 2.5-flash（该文件目前未被前端使用） |
| backend/test_core.py | 修改 | 新增 NON_CITATION 检测 + 真引用不被误判的测试 |
| backend/test_fetchers.py | 修改 | 新增案例 PDF、supra 解析、NON_CITATION dispatch 测试 |

### 测试结果

```
python3 backend/test_core.py              → All tests passed
python3 backend/test_authority_splitter.py → All authority_splitter tests passed
python3 backend/test_fetchers.py          → All fetcher tests passed
python3 backend/test_e2e.py               → All E2E tests passed
```

JS 端的 JSON 容错逻辑用 node 单独验证了 5 种场景：代码块包裹、截断字符串、截断嵌套、正常、垃圾输入。

---

## ✅ PM 验收 Checklist

> PM 测试完后，在这里打勾：

- [ ] 模型下拉框工作正常，不再报模型停用错误
- [ ] 案例卡片出现可点击的 PDF 链接
- [ ] "No JSON in Gemini response" 大幅减少
- [ ] 叙述性脚注进入 "Not a citation"，不再算 Unverified
- [ ] supra 引用能解析到被引用的完整出处
- [ ] 结果记录到 Feedback-Log.md
- [ ] 验收通过 / 需要返工

---

## 📞 如果有问题

- **功能不符合预期**: 在 Feedback-Log.md 中记录，格式: Fact Pattern / Expected / Actual
- **启动失败**: 检查 Python 版本 ≥ 3.10，运行 `python3 backend/test_core.py`
- **紧急问题**: 微信联系 Tech Lead，但随后必须补到 Feedback-Log.md
