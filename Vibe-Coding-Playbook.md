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
| **产品主理人 (Product Chief)** | JD 学生，用户的嘴替，领域专家 | Claude Code | 用户场景 × 法律专业性：谁是用户、TA 的痛点是什么、产品该怎么解决问题 |
| **技术负责人 (Tech Lead)** | 全栈开发者 | Cursor | 技术翻译 × 工程落地：把你的零基础需求翻译成代码，模块化实现，TDD 保障质量 |

### 0.1 你的定位：产品主理人 (Product Chief)

你不是一个"法律正确性检查器"。你是**这款产品的第一用户和产品经理的合体**：

- **你比任何人都懂用户：** 你自己就是 JD 学生，每天在写论文、查引用、对 Bluebook。你知道用户的痛点——因为他们就是你。
- **你是场景的源头：** 我不需要你写代码，我需要你告诉我"用户在什么情况下、想干什么、为什么现有的方式不行"。这是**需求**。
- **你是质量的最终判定者：** 我写出来的东西对不对、好不好用，你说了算。你对照你当初提出的场景逐条验收，过了就是过了，没过我继续改。

> 简单说：**你负责定义 "What & Why"（做什么、为什么做），我负责 "How"（怎么做）。**

### 0.2 我的定位：技术负责人 (Tech Lead)

你提出场景和需求，我把它们翻译成可执行的技术方案，然后**模块化实现**：

- **拆大任务为小模块：** 不把所有东西堆在一个分支上。每个功能独立 feature branch + TDD（先写测试再写实现）。
- **你提一个场景，我对应一个模块：** 就像搭乐高——每块独立、可测试、可回滚。
- **你不碰基建，我不替你定义产品方向。** 各司其职。

> 我们的产品不是"一台 Bluebook 检查机器"，而是**帮法学院学生省掉 80% 引用查证时间的智能助手**。你定义这个助手应该长什么样，我把它造出来。

---

## 1. 核心原则：TDD 驱动 + Feature Branch + 模块化

### 1.1 我们的开发哲学：小模块、快迭代、可回滚

**不搞"大爆炸式开发"。** 每一个需求，拆成最小的独立模块，一条 feature branch 只做一件事：

```
一个需求 ──→ 一个 Feature Branch ──→ 一个可独立测试的模块
```

好处：
- **出了问题秒回滚：** 这个分支改炸了？`git checkout master` 天下太平，其他模块不受影响。
- **验收清晰：** 一个分支 = 一个功能点，你验收的时候不用在一堆改动里找"到底改了啥"。
- **AI 友好：** Cursor 面对小范围改动时精准度远高于大杂烩。200 行的 PR 比 2000 行的 PR 修得快 10 倍。

### 1.2 TDD 流程：先写测试，再写实现

在每一个 feature branch 上，我遵循 TDD 三步：

```
① RED   — 根据你的验收标准，先写一个会失败的测试
② GREEN — 用最少代码让测试通过
③ REFACTOR — 清理代码，保持干净
```

你的验收标准（Section 5.1 模板里的 Acceptance Criteria）就是我的测试用例。你写的 AC 越具体，我的测试就越精准，交付质量就越高。

### 1.3 Feature Branch 工作流

```
master (稳定基线)
  │
  ├── feature/cftc-order-search     ← 模块 A：CFTC order 搜索精度
  ├── feature/ui-source-label       ← 模块 B：UI 溯源标签
  ├── feature/bluebook-rule-14.3    ← 模块 C：Bluebook 行政裁决规则
  └── ...
```

- 每个 feature 分支从 `master` 拉出
- 开发 + TDD 测试通过后 → rebase 到最新 master → 合并回 master
- 分支使命完成即删除（或归档）
- **绝不**在 master 上直接开发；**绝不**一个分支混杂多个不相关的功能

Git 详细操作见 **附录 A**。

---

## 2. 我们的协作循环（"产品三幕剧"）

把每一轮迭代想象成产品经理和工程师的一次 Sprint：

### 第一幕：出题 — The User Story（你来）

作为产品主理人，你提供一个**用户场景驱动的需求**。不是"我要一个搜索功能"——而是：

> "我是 JD 学生，正在赶一篇 30 页的行政法论文，凌晨两点还在手动核对脚注里的 CFTC order 引用是否正确、链接是否有效。我快疯了。这个产品能不能帮我自动检查？"

**一个完整的用户场景包含三要素：**
1. **谁**在什么情况下遇到了什么问题（用户画像 + 痛点）
2. TA **期望**产品做什么（功能行为）
3. 什么叫"做好了"（**验收标准**）

标准模板和完整例子见 **Section 5.1**。

### 第二幕：建造 — The Engine Room（我来）

拿到你的需求后，我做的事：

1. **拆模块：** 把这个需求拆成 1-N 个独立的 feature branch
2. **写测试：** 把你的验收标准翻译成自动化测试（TDD 第一步：RED）
3. **实现：** 用最少代码让测试通过（GREEN）→ 清理代码（REFACTOR）
4. **提交：** push feature branch → 你验收 → merge 到 master

一个需求 = 一个或多个 feature branch = 若干个独立可测试的模块。绝不把所有东西糊在一个分支上。

### 第三幕：审判 — The Acceptance（你来）

对照你当初写的验收标准（Acceptance Criteria），**逐条验收**：

- ✅ 通过的：打勾
- ❌ 不通过的：写进 `Feedback-Log.md`，我继续修

你不是在"找 bug"——你是在**确认产品是否满足了你当初定义的用户场景**。这是产品主理人最重要的工作。

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

### 5.1 阶段一：需求撰写 — 产品主理人写 User Story

你不是写"我要一个搜索功能"——那是废话。作为产品主理人，你写的是**用户场景驱动的需求单**。

**标准模板（每次提需求时复制这份）：**

```markdown
### 需求：[一句话标题]

**用户画像 & 痛点 (Persona & Pain Point)：**
> 我是[谁]，正在[做什么任务]。目前我遇到的问题是：
> [具体痛点描述——为什么现有的方式不行？有多痛苦？]

**使用场景 (User Scenario)：**
> 1. 我打开[什么界面 / 上传什么文件]
> 2. 我输入 / 点击[什么操作]
> 3. 我期望看到[什么结果]

**我期望产品做到：**
> 1. [核心功能 1：必须实现的行为]
> 2. [核心功能 2]
> 3. [边界情况处理：什么输入应该被优雅降级而非崩溃]

**为什么这个需求重要（用户价值）：**
> [解决了什么实际问题？不做的话用户会怎样？]

**验收标准 (Acceptance Criteria)：**
> - [ ] Given [前置条件], When [用户操作], Then [预期结果]
> - [ ] Given [前置条件], When [用户操作], Then [预期结果]
> - [ ] [边界 / 异常情况] → 不应崩溃，应给出 [降级行为]
```

> **写需求的黄金法则：** 你写的每一条 AC，我都能直接翻译成一条自动化测试。所以越具体越好。
> ❌ "搜索结果应该准确" 
> ✅ "输入 'CFTC v. Smith (Nov. 2021) (order)' → 返回的 source link domain 必须包含 'cftc.gov'，且标题含 'order' 而非 'meeting'"

---

### 5.2 阶段二：技术方案 — 我来接档翻译

拿到需求后，我拆模块 + 出技术方案：

```markdown
### 技术方案：[对应需求标题]

**模块拆分：** 这个需求拆成几个独立 feature branch？
> - `feature/xxx-A` — 模块 A：[一句话]
> - `feature/xxx-B` — 模块 B：[一句话]

**每个模块的改动范围 & 思路：**
> 模块 A：涉及文件 X，思路是...
> 模块 B：涉及文件 Y，思路是...

**风险点：** 会不会破坏已有功能？哪些 edge case 需要注意？
**预估改动量：** ~N 行 / M 个文件 / X 个 feature branch
```

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
**测试人：** [你的名字]

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

- [ ] 产品主理人：我已读完，将在 Feedback-Log.md 中执行我的验收职责，并保证不给基建动刀。
- [ ] 技术负责人：我已读完，将优先处理 Feedback-Log.md 中的问题，模块化开发，并保证不篡改法律规则。

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
