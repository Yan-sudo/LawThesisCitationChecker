# LexCheck 开发协作流程规范

> **适用人员**: 开发者 (Tech Lead) ↔ 产品主理人 (PM)
> **工具链**: Cursor + Codegraph + Superpowers Skills
> **最后更新**: 2026-06-16

---

## 1. 角色定义

| 角色 | 人员 | 职责 | 工具 |
|------|------|------|------|
| **Tech Lead** | zyx (你) | 技术实现、代码质量、架构决策 | Cursor + Codegraph + Superpowers |
| **PM** | 朋友 | 需求定义、验收测试、用户场景设计 | Claude Code + Feedback-Log.md |

---

## 2. 开发流程图（Superpowers 驱动）

```
┌─────────────────────────────────────────────────────────────────────┐
│                        完整开发循环                                    │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  PM 写需求                    Tech Lead 开发              PM 验收   │
│  ┌──────────┐               ┌──────────────┐           ┌────────┐  │
│  │ User     │  Feedback-    │ Brainstorm   │           │ 对照   │  │
│  │ Story    │──Log.md───→  │ → Plan       │           │ AC 逐条│  │
│  │ + AC     │               │ → TDD 实现   │           │ 验收   │  │
│  └──────────┘               │ → Codegraph  │           └────────┘  │
│                              │   分析影响   │               │       │
│                              │ → Commit     │               │       │
│                              └──────────────┘               │       │
│                                     │                       │       │
│                              ┌──────▼──────┐               │       │
│                              │ Merge Note  │───────────────→       │
│                              │ (交接文档)   │               │       │
│                              └─────────────┘                       │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 3. Tech Lead 开发流程（你每次开发时）

### 3.1 接到需求后

1. **读取 Feedback-Log.md** — 了解 PM 的需求或 bug 反馈
2. **用 Codegraph 分析影响范围**:
   ```
   # 理解架构（一次性）
   codegraph_explore: "Handler _process_one _fetch_source"

   # 修改前评估影响
   codegraph_impact: "CitationType" (depth: 2)

   # 查找调用者
   codegraph_callers: "split_authorities"
   ```
3. **Brainstorming（Superpowers skill）**— 复杂功能必须先设计

### 3.2 创建 Feature Branch

```bash
# 1. 同步最新 master
git checkout master
git pull --ff-only

# 2. 创建 feature branch
git checkout -b feature/<描述>
# 例: feature/url-citation-support
# 例: feature/pdf-parser
# 例: fix/gemini-rate-limit-retry
```

### 3.3 TDD 开发（Superpowers skill）

```bash
# ① RED — 先写失败的测试
python3 -m pytest backend/test_core.py -v

# ② GREEN — 最少代码让测试通过
# ... 写实现代码 ...

# ③ REFACTOR — 清理代码
# ... 重构 ...

# ④ 用 Codegraph 验证没有破坏其他模块
codegraph_impact: "你修改的函数名"
```

### 3.4 Commit 规范

```
feat(url): add URL citation type recognition

- Add CitationType.URL enum value
- Add _try_url() parser for http/https links
- Create fetchers/webpages.py for HTML content extraction

Closes: URL 类引用支持 (M1)
```

### 3.5 Push & 写 Merge Note

```bash
git push -u origin feature/<描述>
```

然后 **必须** 在 `docs/merge-notes/` 下创建交接文档（模板见 Section 5）。

---

## 4. PM 工作流（你朋友每次验收时）

### 4.1 提需求

在 `Feedback-Log.md` 中按模板写 User Story：

```markdown
## [YYYY-MM-DD] 需求：一句话标题

**类型：** `需求` | `Bug` | `优化`

**用户画像 & 痛点：**
> 我是 JD 学生，正在...目前遇到的问题是...

**使用场景：**
> 1. 我打开...
> 2. 我输入...
> 3. 我期望看到...

**验收标准 (AC)：**
> - [ ] Given ..., When ..., Then ...
> - [ ] Given ..., When ..., Then ...
```

### 4.2 验收

Tech Lead 写完 Merge Note 后，PM 对照 AC 逐条测试：

```markdown
### 验收报告：[需求标题]

**测试日期：** YYYY-MM-DD
**测试人：** PM

**验收结果：**
> - [x] AC1: ... → ✅ 通过
> - [ ] AC2: ... → ❌ 未通过（详见下方）

**未通过项反馈：**
> AC2 失败：[描述问题]
> 已记录到 Feedback-Log.md 第 XX 条。

**通过率：** 1/2
```

---

## 5. Merge Note 交接文档模板 ⭐

> **这是你每次 merge 到 master 时，必须写给 PM 的文档。**
> **存放位置**: `docs/merge-notes/YYYY-MM-DD-<feature-name>.md`

---

### 模板开始

```markdown
# Merge Note: [功能名称]

**日期**: YYYY-MM-DD
**Branch**: feature/xxx → master
**Commit**: abc1234

---

## 📋 本次做了什么（一句话）

[用 PM 能懂的话说清楚这个功能是干什么的]

## 🎯 对应的需求/Bug

> 链接到 Feedback-Log.md 中对应的条目
> 例: "对应 Feedback-Log.md [2026-06-16] URL 类引用支持"

## 🧪 PM 需要测试什么

### 测试步骤（一步步来）

1. 启动服务器: `cd backend && python3 main.py`
2. 打开 http://localhost:8000
3. 上传测试文件: `docs/test-fixtures/xxx.docx`
4. 观察第 X 个脚注的结果

### 预期结果

- 第 X 个脚注应该显示 "URL" 类型的 badge
- 来源应该来自 xxx 网站
- 比对结果应该是 "Supports" / "Does not support"

### 测试文件

| 文件名 | 用途 | 路径 |
|--------|------|------|
| xxx.docx | 测试 URL 引用 | docs/test-fixtures/ |
| yyy.docx | 测试边界情况 | docs/test-fixtures/ |

## 📝 已知限制 / 不完美之处

- [ ] 当前不支持需要登录的网页
- [ ] PDF 链接暂未处理（M3 阶段做）
- [ ] 对于动态渲染的页面（SPA），抓取可能不完整

## 🔄 对已有功能的影响

- [x] 不影响已有功能（纯新增）
- [ ] 修改了已有行为: [说明改了什么]

## 📊 技术细节（PM 可跳过）

### 改动文件清单

| 文件 | 改动类型 | 说明 |
|------|---------|------|
| citation_parser.py | 修改 | 新增 URL 类型 |
| fetchers/webpages.py | 新增 | 网页抓取模块 |
| main.py | 修改 | _fetch_source 增加 URL 分支 |

### Codegraph 影响分析

```
codegraph_impact("CitationType"):
  - _fetch_source (main.py) — 需增加 URL 分支
  - index.html — UI badge 需增加 URL 显示
```

## ✅ PM 验收 Checklist

- [ ] 功能按预期工作
- [ ] 测试文件已准备好
- [ ] 已知限制已了解
- [ ] 结果记录到 Feedback-Log.md
```

### 模板结束

---

## 6. 文件职责边界

### Tech Lead（你）负责的文件

| 文件 | 职责 |
|------|------|
| `backend/main.py` | HTTP 服务器和请求处理 |
| `backend/fetchers/*.py` | 各类来源的抓取逻辑 |
| `backend/gemini.py` | Gemini API 调用 |
| `backend/index.html` | 前端 UI |
| `taskpane/` | Office 插件 |
| `docs/merge-notes/` | Merge Note 交接文档 |
| `docs/test-fixtures/` | 测试用 DOCX 文件 |

### PM（朋友）负责的文件

| 文件 | 职责 |
|------|------|
| `backend/bluebook.py` | Bluebook 引用规范判断 |
| `backend/authority_splitter.py` | 引用拆分规则 |
| `backend/citation_parser.py` | 引用字符串解析 |
| `Feedback-Log.md` | 测试反馈和需求记录 |
| `citation-checker-prd.pdf` | 产品需求文档 |

### 共同维护

| 文件 | 说明 |
|------|------|
| `README.md` | 项目说明 |
| `Vibe-Coding-Playbook.md` | 协作公约 |

---

## 7. 当前待开发功能优先级（基于 PRD）

| 优先级 | 功能 | PRD Milestone | 预估工作量 | 对应 Branch |
|--------|------|--------------|-----------|-------------|
| P0 | URL 类引用识别+抓取+比对 | M1 | 2-3天 | feature/url-citation |
| P1 | PDF 解析（文本层） | M3 | 3-5天 | feature/pdf-parser |
| P1 | PDF 解析（OCR 降级） | M3 | 2-3天 | feature/pdf-ocr |
| P2 | 报告导出（PDF/CSV） | M4 | 2天 | feature/report-export |
| P2 | 批量进度可视化 | M4 | 1-2天 | feature/progress-bar |
| P3 | 语义比对阈值控制 | 风险项 | 1天 | feature/threshold |
| P3 | 来源缓存/镜像 | 风险项 | 2天 | feature/source-cache |

---

## 8. 工具使用说明

### Codegraph（代码智能）

Codegraph 已经为项目建好索引（244 nodes, 409 edges）。在 Cursor 中可以直接通过 MCP 使用：

```
# 理解某个函数的完整上下文
codegraph_explore: "fetch_case CourtListener"

# 修改前看看会影响什么
codegraph_impact: "parse" (depth: 2)

# 找某个函数的所有调用点
codegraph_callers: "check_citation"

# 查找符号位置
codegraph_search: "CitationType"
```

### Superpowers Skills（开发方法论）

| 何时用 | 用哪个 Skill | 做什么 |
|--------|-------------|--------|
| 开始新功能前 | `brainstorming` | 先设计方案，再写代码 |
| 复杂功能拆解 | `writing-plans` | 拆成可执行的步骤 |
| 写代码时 | `test-driven-development` | 先写测试再实现 |
| 遇到 Bug | `systematic-debugging` | 先找根因再修复 |
| 声称完成前 | `verification-before-completion` | 跑测试验证 |
| 多个独立任务 | `subagent-driven-development` | 并行执行 |

---

## 9. Git 规范速查

```bash
# 日常四步
git pull --ff-only          # ① 拉最新
git checkout -b feat/xxx    # ② 开新分支
git add . && git commit -m "feat: ..."  # ③ 存盘
git push -u origin feat/xxx # ④ 推到远程

# 禁止事项
# ❌ 直接 push 到 master
# ❌ 对 master 做 force push
# ❌ 不带 --ff-only 的 pull
# ❌ 在 master 上直接改代码
```

---

## 10. 沟通渠道

| 场景 | 渠道 | 格式 |
|------|------|------|
| PM 提需求 | `Feedback-Log.md` | 按模板写 User Story |
| Tech Lead 交付 | `docs/merge-notes/` | 按 Merge Note 模板 |
| Bug 反馈 | `Feedback-Log.md` | Fact Pattern / Expected / Actual |
| 紧急问题 | 微信 | 但随后必须补到 Feedback-Log.md |
