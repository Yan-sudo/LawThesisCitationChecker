# Merge Note 模板

> **使用说明**: 每次将 feature branch merge 到 master 时，复制此模板到 `docs/merge-notes/YYYY-MM-DD-<feature-name>.md`
> **目标读者**: PM（产品主理人），用非技术语言描述变更

---

## 复制以下模板 ⬇️

```markdown
# Merge Note: [功能名称]

**日期**: YYYY-MM-DD
**Branch**: feature/xxx → master
**Commit**: abc1234

---

## 📋 本次做了什么（一句话）

[用 PM 能懂的话说清楚这个功能是干什么的]

**示例**:
> "新增了 URL 类引用的支持——现在如果脚注里有一个网页链接，系统会自动抓取网页内容并比对引用是否准确。"

---

## 🎯 对应的需求/Bug

> 链接到 Feedback-Log.md 中对应的条目
> 例: "对应 Feedback-Log.md [2026-06-16] URL 类引用支持"
> 例: "修复 Feedback-Log.md [2026-06-10] CFTC 搜索结果年份错误"

---

## 🧪 PM 需要测试什么

### 测试步骤（一步步来）

1. 启动服务器: `cd backend && python3 main.py`
2. 打开 http://localhost:8000
3. 上传测试文件: `docs/test-fixtures/xxx.docx`
4. 观察第 X 个脚注的结果
5. [其他步骤]

### 预期结果

- [结果1: 应该看到什么]
- [结果2: badge 应该显示什么]
- [结果3: 来源应该来自哪里]

### 测试文件

| 文件名 | 用途 | 路径 |
|--------|------|------|
| xxx.docx | 测试正常情况 | docs/test-fixtures/ |
| yyy.docx | 测试边界情况 | docs/test-fixtures/ |

---

## 📝 已知限制 / 不完美之处

> **重要**: 这里列出当前版本的局限性，PM 在验收时不应该测试这些场景

- [ ] 限制1: [说明]
- [ ] 限制2: [说明]
- [ ] 限制3: [说明]

---

## 🔄 对已有功能的影响

> **二选一**:

- [ ] ✅ 不影响已有功能（纯新增）
- [ ] ⚠️ 修改了已有行为:
  - [具体说明改了什么旧功能]
  - [PM 需要额外测试哪些旧功能]

---

## 📊 技术细节（PM 可跳过）

### 改动文件清单

| 文件 | 改动类型 | 说明 |
|------|---------|------|
| path/to/file.py | 新增/修改/删除 | 一句话说明 |

### Codegraph 影响分析

```
codegraph_impact("修改的函数名"):
  - 受影响的函数1 (文件) — 影响说明
  - 受影响的函数2 (文件) — 影响说明
```

### 测试结果

```
pytest backend/test_core.py -v
==================== 36 passed in 2.3s ====================
```

---

## ✅ PM 验收 Checklist

> PM 测试完后，在这里打勾：

- [ ] 功能按预期工作
- [ ] 测试文件已准备好
- [ ] 已知限制已了解
- [ ] 结果记录到 Feedback-Log.md
- [ ] 验收通过 / 需要返工

---

## 📞 如果有问题

- **功能不符合预期**: 在 Feedback-Log.md 中记录，格式: Fact Pattern / Expected / Actual
- **启动失败**: 检查 Python 版本 ≥ 3.10，运行 `python3 -m pytest backend/test_core.py`
- **紧急问题**: 微信联系 Tech Lead，但随后必须补到 Feedback-Log.md
```

---

## 示例: 一个完整的 Merge Note

### 文件: `docs/merge-notes/2026-06-16-url-citation-support.md`

```markdown
# Merge Note: URL 类引用支持

**日期**: 2026-06-16
**Branch**: feature/url-citation → master
**Commit**: a1b2c3d

---

## 📋 本次做了什么（一句话）

新增了 URL 类引用的支持——现在如果脚注里有一个网页链接（如 https://example.com），系统会自动抓取网页内容并比对引用是否准确。

---

## 🎯 对应的需求/Bug

对应 Feedback-Log.md [2026-06-10] PRD M1: URL 类引用支持

---

## 🧪 PM 需要测试什么

### 测试步骤

1. 启动服务器: `cd backend && python3 main.py`
2. 打开 http://localhost:8000
3. 上传测试文件: `docs/test-fixtures/url-test-01.docx`
4. 观察第 3 个脚注（包含 https://www.supremecourt.gov/... 链接）
5. 点击 "Check Citations"
6. 等待 10-15 秒

### 预期结果

- 第 3 个脚注应该显示 "URL" 类型的 badge（蓝色）
- 来源应该来自 supremecourt.gov
- 比对结果应该是 "Supports" / "Does not support" / "Cannot verify"
- 如果网页无法访问，应该显示 "Cannot verify" 并给出原因

### 测试文件

| 文件名 | 用途 | 路径 |
|--------|------|------|
| url-test-01.docx | 正常 URL 引用 | docs/test-fixtures/ |
| url-test-02.docx | 失效链接（404） | docs/test-fixtures/ |
| url-test-03.docx | 需要登录的网页 | docs/test-fixtures/ |

---

## 📝 已知限制 / 不完美之处

- [ ] 当前不支持需要登录的网页（如 Westlaw、LexisNexis）
- [ ] PDF 链接暂未处理（M3 阶段做）
- [ ] 对于动态渲染的页面（SPA），抓取可能不完整
- [ ] 如果网页有反爬虫机制，可能会被拦截

---

## 🔄 对已有功能的影响

- [x] ✅ 不影响已有功能（纯新增）

---

## 📊 技术细节（PM 可跳过）

### 改动文件清单

| 文件 | 改动类型 | 说明 |
|------|---------|------|
| backend/citation_parser.py | 修改 | 新增 `CitationType.URL` 枚举和 `_try_url()` 解析器 |
| backend/fetchers/webpages.py | 新增 | 网页抓取模块，使用 requests + readability |
| backend/main.py | 修改 | `_fetch_source()` 增加 URL 分支 |
| backend/test_core.py | 修改 | 新增 5 个 URL 相关测试用例 |

### Codegraph 影响分析

```
codegraph_impact("CitationType"):
  - _fetch_source (main.py:186) — 已增加 URL 分支
  - BLUEBOOK_RULES (citation_parser.py:44) — 已增加 URL 规则
```

### 测试结果

```
pytest backend/test_core.py -v
==================== 41 passed in 2.8s ====================
（原 36 个 + 新增 5 个 URL 测试）
```

---

## ✅ PM 验收 Checklist

- [ ] 功能按预期工作
- [ ] 测试文件已准备好
- [ ] 已知限制已了解
- [ ] 结果记录到 Feedback-Log.md
- [ ] 验收通过 / 需要返工
```
