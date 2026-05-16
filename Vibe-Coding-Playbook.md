# Vibe-Coding Playbook

> **写给队友的协作手册：** 一份让 AI 听得懂我们、让你写得开心、让 bug 无处遁形的开发公约。
>
> ---
> *"Good code is like good law — clear, consistent, and reviewable by someone who wasn't in the room when you wrote it."*
> ---

---

## 0. 我们是谁 & 我们在干什么

| 角色 | 你是谁 | 你的武器 | 你的主场 |
|------|--------|----------|----------|
| **大状 (Counsel)** | JD 学生，法律逻辑天花板 | Claude Code | 实体法：引用规则、判例检索逻辑、测试用例设计 |
| **架构师 (Engineer)** | 全栈开发者 | Cursor | 程序法：搜索引擎、API 管道、UI 框架、后端基建 |

我们不是在写代码，我们是在**搭一座桥**——把 200 页的法律引用规范 (Bluebook) 翻译成一台能自动检查论文引用的机器。

一个负责定义"什么是正确"（实体法），一个负责实现"怎么跑到正确"（程序法）。目标一致、分工清晰、互不踩脚。

---

## 1. 核心原则：单线冲刺，分支护航

在大部分日常迭代中，我们走 **"主分支单线冲刺"** 模式——因为只有两个人，且你不会和我同时改同一个文件：

```
master (唯一事实来源)
  │
  ├── 我提交修改 → git push
  ├── 你 git pull → 运行测试
  ├── 你在 Feedback-Log.md 里记录结果
  └── 我读 log → Cursor 精准修复 → 下一轮
```

但当改动较大、涉及多个文件、或你想在我的改动审核完之前不被阻塞地继续测试时，就该用 **feature branch** 出场了。分支不是噪音——它是你的**安全网**：哪怕分支上的代码炸了，切回 `master` 一切照旧。

Git 的具体操作见 **附录 A：Git 使用指南**——只背 5 条命令就够用。

---

## 2. 我们的 TDD 协作循环（"法庭三幕剧"）

把每一轮迭代想象成一场微型庭审：

### 第一幕：出题 — The Fact Pattern（你来）

你提供一个**具体、刁钻、有预期结果**的测试用例。这是最重要的环节——你的领域知识是整台机器的方向盘。

> **一个好 test case 长这样：**
>
> *"我有一段论文脚注：'See CFTC v. Smith, No. 21-1234 (Nov. 2021) (order)'*
> *我期望系统：*
> *1. 识别出 'order' 是文件类型，优先匹配行政裁决类数据库；*
> *2. 精确匹配 2021 年 11 月，不允许返回 2021 年 2 月的结果；*
> *3. 返回的 source link 能直接打开展示具体段落。"*

### 第二幕：建造 — The Engine Room（我来）

我用 Cursor + AI 来：
- 修 UI 逻辑（让溯源信息更清晰）
- 调搜索管线（API 选择、权重调整、年份匹配算法）
- 接管所有基建代码（`main.py`、`fetchers/`、API 路由）

你不碰基建，我不碰法律规则。分工明确，零摩擦。

### 第三幕：审判 — The Verdict（你来）

你 `git pull` 最新代码，对着你的 test case 跑一遍，然后——

> **把结果写进 `Feedback-Log.md`（见下一节），而不是发微信告诉我。**

这不是冷漠，这是**可检索、可追溯、可喂给 AI 的闭环数据**。你发微信说"搜出来不对"，我转手还得帮你翻译成 AI 能懂的格式。直接写进 log，Cursor 能当场读、当场修。

---

## 3. 核心机制：`Feedback-Log.md` — 我们的"案卷系统"

这是整个协作里**最重要的文件**。它比代码注释更关键，因为它是 AI 修复 bug 的唯一定向标。

### 3.1 文件位置与格式

文件就在仓库根目录：`Feedback-Log.md`

**每次记录一条反馈，格式如下：**

```markdown
## [YYYY-MM-DD] 标题：一句话总结

**类型：** `UI/UX` | `Search精度` | `逻辑规则` | `数据缺失` | `性能`

**测试用例 (Fact Pattern)：**
> （把你测试用的引用原文贴在这里）

**预期结果 (Expected)：**
> （应该发生什么）

**实际结果 (Actual)：**
> （实际发生了什么）

**复现步骤 (Steps)：**
> 1. 打开 index.html
> 2. 输入引用 xxx
> 3. 观察 xxx

**建议修复方向：**
> （可选，但非常欢迎——你的直觉往往就是对的）
```

### 3.2 好报告 vs 差报告：真实案例教学

#### 案例 A：UI / 交互体验

| 类型 | 内容 |
|------|------|
| ❌ 差 | "UI 看着有点乱。" |
| ✅ 好 | **"[UI 溯源问题] 界面上显示的 'quoted sentence' 让人困惑——我不确定这是我原本 Word 文档里的句子，还是从外部 source 爬下来的原文。建议：给两种来源增加明确的视觉标签区分。"** |

**为什么好？** 它说了三件事：(1) 哪个界面元素有问题；(2) 为什么会产生困惑（用户心智模型 vs 实际行为）；(3) 给出了改进方向。Cursor 拿到这条直接就能定位到 UI 渲染逻辑。

#### 案例 B：搜索引擎 / 检索精度

| 类型 | 内容 |
|------|------|
| ❌ 差 | "搜出来的东西似是而非。" |
| ✅ 好 | **"[Search 精度问题] 目标靶件：CFTC 2021 年 11 月发布的 order。系统错误抓取：2021 年 2 月的会议记录。建议：搜索权重需要加强年份 + 月份的精准匹配，或者优先匹配 'order' 这种文件类型（而非 meeting minutes / press release）。"** |

**为什么好？** 它给了 AI 一个**可操作的对比**：目标是什么 × 错误返回了什么 × 两者差异在哪（月份、文件类型）。这就是给搜索引擎调参的「靶心数据」。

---

### 3.3 你写给 Claude Code 的指令长这样

当你自己在用 Claude Code 调试法律逻辑时，也请用同样格式记录发现：

```markdown
## [YYYY-MM-DD] Bluebook Rule 14.3 行政裁决引用格式问题

**类型：** `逻辑规则`

**测试用例：**
> 引用格式："In re Application of XYZ Corp., CFTC Docket No. 21-001"

**Claude 当前行为：**
> 判定为 "非法引用格式"。

**正确规则（Bluebook Rule 14.3）：**
> CFTC 行政裁决应包含 docket number，且 "In re" 开头是合法格式。当前判错。

**建议修复：**
> 在 authority_splitter.py 的 rule 列表中加入 CFTC 行政裁决的模板匹配。
```

这样一来，你的 Claude Code 结果也能喂给我的 Cursor，形成跨 AI 的知识传递。

---

## 4. 边界感：谁动什么、谁不动什么

以下是一个**互不侵犯条约**：

### 你的领域（请你和 Claude Code 自由驰骋）

| 文件 / 模块 | 干什么 |
|-------------|--------|
| `backend/bluebook.py` | Bluebook 引用规范的核心判断逻辑 |
| `backend/authority_splitter.py` | 引用拆分与机构识别规则 |
| `backend/citation_parser.py` | 引用字符串解析规则 |
| 所有**法律规则层面**的判断标准 | 判例格式、脚注顺序、缩写规范 |

### 我的领域（请让 Cursor + 我来管）

| 文件 / 模块 | 干什么 |
|-------------|--------|
| `backend/main.py` | FastAPI 后端路由与服务编排 |
| `backend/fetchers/*.py` | 数据库/搜索引擎 API 对接 |
| `backend/index.html` | 前端 UI 架构与交互逻辑 |
| `backend/gemini.py` | Google Gemini API 调用管道 |
| `taskpane/` 全部 | Office 插件 UI 层 |
| 所有**基建 & 管道**层面代码 | 部署、环境变量、API keys |

> **给你 Claude Code 的标准指令模板（每次对话开头贴上）：**
>
> ```
> 你的任务是分析和修正法律引用规则，不要修改以下文件：
>   - backend/main.py
>   - backend/fetchers/ 下的任何文件
>   - backend/index.html（仅修改法律规则展示文案可以，不改结构）
>   - taskpane/ 下的任何文件
> 如果你发现基建有问题影响法律判断，在 Feedback-Log.md 里记录，不要直接动手。
> ```

---

## 5. 完整开发循环：从需求到验收（四幕剧）

一个功能从"脑子里有个念头"到"跑通了能上线"，走四个阶段。每个阶段都有标准模板，你照填就行，剩下的交给 AI 和我。

---

### 5.1 阶段一：需求撰写 — 他来写"法律故事"

他不是写"我要一个搜索功能"——那是废话。他应该写一个**场景化的法律 Fact Pattern**，就像法学院的考试题目。

**标准模板（他每次提需求时复制这份）：**

```markdown
### 需求：[一句话标题]

**使用场景 (Scenario)：**
> 我是一名法学院学生，正在写一篇关于[主题]的论文。我在 Word 文档中
> 插入了一条脚注，引用了[具体机构/判例名称]。
> 
> 具体引文是：`[完整引用原文]`

**我期望系统做到：**
> 1. [预期行为 1：比如正确识别引用类型是 case / statute / order]
> 2. [预期行为 2：比如返回的 source link 能直接打开，且精确到具体段落]
> 3. [预期行为 3：比如年份匹配不允许 ±1 年的误差]
> 4. [边界情况：哪些情况不应该触发 / 哪些输入应该被优雅处理]

**为什么这个需求重要：**
> [一句话说明：因为这个引用格式在 Bluebook Rule X.X 里有特殊规定 / 
>   因为 CFTC orders 是行政法论文的高频引用 / 等等]

**验收标准 (Acceptance Criteria)：**
> - [ ] 输入 `[引文A]` → 输出应包含 `[预期输出A]`
> - [ ] 输入 `[引文B]` → 输出应包含 `[预期输出B]`
> - [ ] 输入 `[引文C（故意刁难）]` → 不应崩溃，应给出 `[降级行为]`
```

---

### 5.2 阶段二：技术方案 — 我来接档翻译

拿到他的需求后，我用 Cursor 产出以下内容（不给他看，但归档在 PR 里）：

```markdown
### 技术方案：[对应需求标题]

**现状分析：** 当前系统对这类引用做了什么（或没做什么）
**改动范围：** 涉及哪些文件（e.g. fetchers/cases.py, bluebook.py）
**实现思路：** 3-5 句话说明怎么做
**风险点：** 会不会破坏已有功能？哪些 edge case 需要注意？
**预估改动量：** ~N 行代码，涉及 M 个文件
```

这个他不看也没关系，但**我写了才有底气动手**。AI 可以帮我写，但我审过才 commit。

---

### 5.3 阶段三：实现交付

我改代码 → 本地跑测试 → commit → push。

**Commit 消息格式：**

```
feat(search): enforce exact year-month match for CFTC administrative orders

- Add month-precision flag to CFTC fetcher
- Penalize year-mismatch results by -0.5 weight
- Add 'order' document type to priority list

Closes: [需求标题]
```

他在 `Feedback-Log.md` 对应的需求下面追加一行 `## Status: Ready for Test`，我就能看到他确认可以测了。

---

### 5.4 阶段四：验收测试 — 他对照原始需求逐条验收

**不是"随便点点觉得还行"——而是对照他阶段一写的验收标准，一条一条过：**

```markdown
### 验收报告：[需求标题]

**测试日期：** YYYY-MM-DD
**测试人：** [大状名字]

**验收结果：**
> - [x] AC1: 输入 `See CFTC v. Smith (Nov. 2021)` → ✅ 正确返回 Nov 2021 order
> - [x] AC2: 输入 `See CFTC v. Smith (Feb. 2021)` → ✅ 正确返回 Feb 2021 meeting record（不是 order）
> - [ ] AC3: 输入 `CFTC 2021 order`（模糊查询） → ❌ 系统返回了 SEC 的结果
> 
> **通过率：** 2/3

**未通过项的详细反馈：**
> AC3 失败：模糊查询时似乎没有限制机构范围，CFTC 变成了泛搜索。
> 详见 Feedback-Log.md 第 XX 条记录。
```

---

### 5.5 完整例子：一条 CFTC order 需求从头到尾

#### 阶段一：他的需求

```markdown
### 需求：CFTC 行政裁决精确检索

**使用场景：**
> 我写一篇关于衍生品监管的论文，脚注里引用了 CFTC 2021 年 11 月
> 发布的一份行政裁决 (order)。
> 具体引文：`See CFTC v. Smith, No. 21-1234 (Nov. 2021) (order)`

**我期望系统做到：**
> 1. 识别 "order" 是文件类型，优先匹配行政裁决，而非 meeting record
> 2. 年份精确匹配 2021 年 11 月，不允许返回 2021 年 2 月的结果
> 3. 返回的 source link 直接指向 CFTC 官网的具体 order 页面

**为什么这个需求重要：**
> Bluebook Rule 14.3 对行政裁决有特殊引用格式；CFTC orders 
> 是行政法论文的高频引用类型。

**验收标准：**
> - [ ] 输入 `CFTC v. Smith, No. 21-1234 (Nov. 2021) (order)` → 返回正确 order 原文
> - [ ] 输入 `CFTC v. Jones, No. 21-0456 (Feb. 2021) (meeting)` → 返回 meeting record，不是 order
> - [ ] 输入 `CFTC 2021 order`（模糊查询） → 不应返回 SEC 或 FTC 的结果
```

#### 阶段二：我的技术方案（存档用）

```markdown
### 技术方案：CFTC 行政裁决精确检索

**现状分析：** 当前 fetchers/cases.py 对所有机构使用同一搜索管线，
不区分文件类型（order vs meeting record），年份容差为 ±1 年。
**改动范围：** fetchers/cases.py, fetchers/statutes.py, bluebook.py
**实现思路：**
1. 在搜索 query 中解析 "(order)" / "(meeting)" 等文件类型标记
2. 在 CFTC 查询时添加文件类型过滤参数
3. 将年份容差从 ±1 年收紧为 ±0
4. 在 bluebook.py 中新增 Rule 14.3 的 CFTC 行政裁决识别逻辑
**风险点：** 收紧年份容差可能让真实但日期标注不完全的引用也搜不到，
需要做降级处理（先严格搜，搜不到再放宽）
**预估改动量：** ~80 行，涉及 3 个文件
```

#### 阶段三 + 四：实现 + 验收

我实现完 → push → 他在 Feedback-Log.md 里写验收报告。通过则关需求，不通过则反馈日志继续迭代。

---

### 5.6 一句话总结完整循环

```
他写需求（场景化故事 + 验收标准）
    │
    ▼
我写技术方案 → 实现 → push
    │
    ▼
他对照验收标准逐条测试 → Feedback-Log.md 记录结果
    │
    ├── 全过 → 关需求 ✅
    └── 有未过 → 反馈 → 我修 → 再来一轮
```

---

## 6. 一些约定俗成 (Norms)

- **Commit message 用英文**，格式：`feat(scope): 简短描述` 或 `fix(scope): 简短描述`。遵循 [Conventional Commits](https://www.conventionalcommits.org/)，GitHub 上好看，你能看懂，我不用翻译两遍。
- **Feedback-Log.md 用中文**，因为你写得最舒服，我也看得最准。
- **Force push 规则**：只允许在自己个人的 `feature/` 或 `fix/` 分支上使用 `git push --force-with-lease`（详见附录 A）。**永远不要**对 `master` 做 force push。
- **每次 pull 前确认自己没有未提交的改动**（`git status`），避免冲突。
- **遇到任何不确定的事，先写进 Feedback-Log.md**。不要猜，不要自己 debug 半个小时然后放弃——你放弃的半小时可能是我读一条 log 后五分钟解决的问题。

---

## 7. 最后的最后

> 你不是在写代码。你是在写**验收标准**。
>
> 我不是在写代码。我是在写**通过验收的通道**。
>
> AI 不是在取代我们。AI 是让我们用法律思维 + 工程思维 **并行推进**的加速器。

你负责把法律世界的复杂性翻译成清晰的命题，我负责把命题翻译成能跑的机器。这个 playbook 就是我们的翻译词典。

---

**签署（精神意义上的）：**

- [ ] 大状：我已读完，将在 Feedback-Log.md 中执行我的测试职责，并保证不给基建动刀。
- [ ] 架构师：我已读完，将优先处理 Feedback-Log.md 中的问题，并保证不篡改法律规则。

---

*下一次提交见。*

---

## 附录 A：Git 使用指南（团队版）

> **写给从未用过 Git 的队友。** 你不需要理解 Git 的原理，只需要记住 5 条命令就能活下来。其余的当字典查。

---

### A.1 这是什么？为什么用 Git？

| 你的日常类比 | Git 的对应 |
|-------------|-----------|
| 写论文时的"另存为 v2.docx"、"另存为 最终版.docx" | Git 自动帮你存档，不用手动另存 |
| Word 的"修订模式" | Git 的 `diff`——精确到每一行谁改了什么 |
| Dropbox 的同步 | `git push` / `git pull`——推上去 / 拉下来 |
| 写了一段觉得不对，想回到昨天的版本 | `git checkout <commit>`——时光机 |

一句话：**Git 就是带时间机器的同步网盘。** 你只需要学会存（commit）、拉（pull）、推（push）、开新轨道（branch）就行。

---

### A.2 分支模型

我们采用简化的 GitHub Flow（Rebase 版），目标是让提交历史像一条直线一样干净。

| 分支类型 | 命名格式 | 用途 | 谁能 push |
|----------|---------|------|-----------|
| `master` | 固定 | 始终可运行的稳定版本 | **禁止直接 push**（只有我通过 merge 更新） |
| `feature/<描述>` | e.g. `feature/add-cftc-rules` | 新功能开发 | 你自己的分支，随意 |
| `fix/<描述>` | e.g. `fix/bluebook-rule-14.3` | Bug 修复 | 你自己的分支，随意 |

**你的分支就在你的本地玩，改炸了也不影响我。**

---

### A.3 新手最小命令集（背这 5 条就够日常用了）

```bash
# 1. 开始干活前：同步最新代码
git checkout master
git pull --ff-only

# 2. 从 master 开一条你自己的分支
git checkout -b feature/<描述>

# 3. 存盘（提交你的改动）
git add .
git commit -m "feat(scope): 用英文写你改了什么"

# 4. 推到远程（这样我也能看到）
git push -u origin feature/<描述>

# 5. 切回 master 更新
git checkout master
git pull --ff-only
```

> **口诀：** checkout → pull → branch → add → commit → push。六步走，一步不落。

---

### A.4 进阶操作：同步 master + Rebase（保持历史干净）

当你的 feature 分支写了一段时间，`master` 上可能有我的新提交。你需要把 master 的最新代码"嫁接"到你的分支上：

```bash
# 1. 确保在 feature 分支上
git checkout feature/<描述>

# 2. 拉取远程最新信息
git fetch origin

# 3. 把你的分支"移植"到最新 master 上
git rebase origin/master

# 4. 如果有冲突（CONFLICT）：
#    → 打开冲突文件，找到 <<<<<<< 和 >>>>>>> 标记
#    → 手动决定保留哪段代码，删掉标记
#    → git add <修复后的文件>
#    → git rebase --continue

# 5. 强推到远程（仅限你自己的 feature 分支！）
git push --force-with-lease
```

> **为什么要 rebase？** 因为 rebase 让你的改动"接"在最新 master 的末尾，历史像一条直线。merge 会产生一个无意义的"合并节点"，如图：
>
> Rebase（干净）：`A → B → C → 你的改动`
> Merge（杂乱）：`A → B → C → (merge commit) ← 你的改动`

---

### A.5 Worktree：同时开多个分支目录

有时你想一边在 `master` 上跑测试，一边在另一个分支上改代码，不需要来回 `checkout`。

```bash
# 在仓库旁边再开一个工作目录，对应某条分支
git worktree add ../law-thesis-feature feature/<描述>

# 用法：会在上级目录创建一个 law-thesis-feature 文件夹，
# 里面的代码就是 feature/<描述> 分支的内容。
# 两个文件夹互不干扰，可以同时在两个 VS Code 窗口里打开。

# 查看所有 worktree
git worktree list

# 用完了删掉
git worktree remove ../law-thesis-feature
```

> **适用场景：** 你在 feature 分支上改 Bluebook 规则，同时想切回 master 跑一下我的最新测试。不用 stash、不用 commit，直接在新窗口打开 worktree 目录就行。

---

### A.6 Commit 规范

遵循 [Conventional Commits](https://www.conventionalcommits.org/)：

```
<type>(<scope>): <简短描述>
```

| Type | 含义 | 例子 |
|------|------|------|
| `feat` | 新功能 | `feat(parser): add CFTC administrative order support` |
| `fix` | 修 bug | `fix(search): enforce exact year-month match` |
| `docs` | 文档 | `docs(playbook): update git workflow section` |
| `refactor` | 重构（不改功能，只改结构） | `refactor(bluebook): extract rule 14.3 to separate function` |
| `test` | 测试 | `test(citation): add edge case for In re format` |

**每次 commit 只做一件事**，不要一个 commit 里又改规则又修 UI 又改文档——分开提交，方便回头找。

---

### A.7 冲突处理口诀

遇到 `CONFLICT` 不要慌，三个动作：

1. **找标记：** 打开冲突文件，搜 `<<<<<<<` 和 `>>>>>>>`
2. **做决定：** 两个版本选一个（或手动合并），删掉标记符号
3. **继续走：** `git add .` → `git rebase --continue`

搞不定？截图发我，或者直接把文件丢给我。

---

### A.8 明确禁止项

| 禁止事项 | 原因 |
|----------|------|
| 直接 `git push` 到 `master` | master 是稳定基线，只能通过 merge 进入 |
| 对 `master` 做 force push | 会覆盖远程历史，其他人的代码可能丢失 |
| 用 `git pull`（不带 `--ff-only`） | 默认会产生无意义的 merge commit |
| 在 `master` 上直接改代码 | 容易忘记切分支，混在一起 |
| 提交不完整的代码 | 让别人 pull 下来跑不动 |

---

### A.9 推荐一次性配置（让你少踩坑）

在你的终端里运行以下三行，以后 `pull` 就不会自动产生 merge commit 了：

```bash
git config --global pull.rebase true
git config --global pull.ff only
git config --global rebase.autoStash true
```

---

### A.10 新人最小命令集卡片（打印贴在显示器旁边）

```
┌─────────────────────────────────────────────────┐
│  Git 日常四步                                  │
│                                                 │
│  ① git pull --ff-only       拉最新             │
│  ② git checkout -b feat/xxx  开新分支           │
│  ③ git add . && git commit -m "feat: ..."  存盘 │
│  ④ git push -u origin feat/xxx  推到远程        │
│                                                 │
│  出冲突了？ git rebase --continue               │
│  搞不定？   直接微信找我                         │
└─────────────────────────────────────────────────┘
```

---

## 附录 B：AI 开场白模板（直接复制粘贴）

> **为什么需要这个？** 我们的 AI（Claude Code 和 Cursor）每次对话都是"失忆"的。你需要在一开始就告诉它你是谁、遵守什么规则、不要碰什么文件。下面的模板帮你一键搞定。

---

### B.1 他用 Claude Code 时的开场白

**每次开新对话，第一条消息粘贴以下内容：**

```
你是我的法律引用逻辑助手。在开始之前，请先理解以下协作规则：

【我的角色】
我是 JD 学生，负责法律引用规则的准确性和测试用例设计。

【我的权限范围】
我可以修改的文件：
- backend/bluebook.py（Bluebook 引用规范）
- backend/authority_splitter.py（引用拆分与机构识别）
- backend/citation_parser.py（引用字符串解析）

我绝对不能修改的文件（这些由我的工程合伙人管理）：
- backend/main.py
- backend/fetchers/ 下的任何文件
- backend/index.html（仅可改法律规则展示文案，不改结构）
- taskpane/ 下的任何文件

【项目背景】
我们在做一个法律论文引用自动检查工具。
核心逻辑是对照 Bluebook 规则验证引文格式、检索源文档、并返回验证结果。

【反馈规范】
如果我发现基建有问题影响了法律判断，
我会记录在项目根目录的 Feedback-Log.md 里，格式如下：
## [日期] 标题
**类型：** 逻辑规则 | 数据缺失
**发现：** [具体描述]
**预期：** [应该是什么]
**实际：** [AI 实际输出了什么]
**建议：** [修复方向]

现在请确认你已理解以上规则，然后我们开始。
```

---

### B.2 我用 Cursor 时的开场白

**复制以下内容作为 Cursor 对话的 context：**

```
你是我的全栈工程助手。请先阅读以下协作规则：

【我的角色】
我是全栈开发者，负责系统基建——搜索管线、API、UI 框架、部署。

【项目文件结构】
- backend/main.py — FastAPI 后端路由
- backend/fetchers/*.py — 搜索引擎 / 数据库 API 对接
- backend/gemini.py — Google Gemini API 调用
- backend/index.html — 前端 UI
- taskpane/ — Office 插件
- Vibe-Coding-Playbook.md — 协作公约
- Feedback-Log.md — 测试反馈日志

【当前任务模式】
我通常从 Feedback-Log.md 中读取我合伙人的测试反馈，
然后精准定位到对应代码文件修复。

Commit 规范：
- feat(scope): 描述
- fix(scope): 描述
- refactor(scope): 描述
- docs(scope): 描述

不允许做的事：
- 不修改法律规则文件（bluebook.py, citation_parser.py, authority_splitter.py）
- 不对 master 做 force push

请确认理解。然后我会给你具体的 bug 或需求。
```

---

### B.3 快速启动卡片（他贴 Claude Code 窗口旁边）

```
┌──────────────────────────────────────────────────────────┐
│  每次开 Claude Code，第一条消息：                        │
│                                                          │
│  "请阅读 Vibe-Coding-Playbook.md 的附录 B.1，            │
│   然后帮我 [具体任务]"                                   │
│                                                          │
│  或者直接复制粘贴附录 B.1 的完整模板。                    │
└──────────────────────────────────────────────────────────┘
```
