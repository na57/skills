---
name: ynu-eos8-create-entity-set
description: "在云大低代码平台（EOS8，dev-idm.ynu.edu.cn）当前打开的 IDE 中，为指定构件包创建实体集。当用户要新建/创建实体集时使用。流程：确认已登录 IDE（未登录先调用 ynu-lowcode-login）→ AskUserQuestion 确认构件包与实体集编码/名称 → 左侧资源树右键构件包的「实体」资源 → 菜单选「新建实体集」→ 弹窗填编码与名称 → 验证树中出现。兼容 WorkBuddy 与 Trae 双浏览器运行时，启动时自动探测。编码规则：仅英文字母/数字/下划线、字母或下划线开头、非空、不可重复。"
agent_created: true
---

# 创建实体集（EOS8 低代码平台，WorkBuddy / Trae 双运行时兼容）

## Overview

在云南大学低代码开发平台（普元 EOS8，`dev-idm.ynu.edu.cn`）当前打开的 IDE 中，
为指定构件包创建一个**实体集**。实体集是包含一组具有共同属性或特征的实体的集合，
位于资源树「构件包 → 实体」之下。

流程概览：
确认 IDE 已打开且已登录 → AskUserQuestion 确认构件包与实体集信息 →
资源树右键「实体」资源 → 菜单选「新建实体集」→ 弹窗填编码 / 名称 →
验证资源树出现新实体集。

**作用域铁律**：创建前必须用 `AskUserQuestion` 确认目标构件包与实体集编码/名称
（单向播报不算确认）；只操作用户指定的构件包，不碰其他包。

## When to use

- 用户说「新建实体集」「建一个实体集」「创建实体集」且上下文是云大低代码平台（EOS8）。
- 平台需校园网或 WebVPN 环境。

## Step 0 — 运行时探测（必须最先执行）

- 工具列表含 `mcp__browser__browsers_list` → **WorkBuddy 模式**：
  直接调用 `mcp__browser__*`（一次一个操作），页面感知用 DOM 读取。
- 工具列表含 integrated_code_mode 的 `Exec`（浏览器工具在 Exec 内以
  `await tools.browser_*` 调用）→ **Trae 模式**：可合并 3~8 个操作减少往返；
  感知用 `browser_snapshot` 可访问性树，**ref 仅在最近一次快照内可靠**。
- 两者都没有 → 提示用户启用对应浏览器扩展，终止流程。

## 参数

- **目标构件包**（必填）：构件包名称或编码。树节点只显示**名称**不显示编码。
- **实体集编码**（必填），规则：
  ① 不能留空；② 只能英文字母、数字或下划线，**不能包含汉字**；
  ③ 必须以字母或下划线开头；④ 不允许重复。
- **实体集名称**（必填）：不能留空。

缺任一参数或编码不合规 → 用 `AskUserQuestion` 询问/纠正，不要猜、不要带病提交。

## Workflow

### Step 1 — 确认 IDE 已打开且已登录

1. **优先复用上下文**：若本轮 `ynu-lowcode-login` / `ynu-eos8-new-package`
   刚执行过，直接使用其产出的 IDE 标签页（WorkBuddy：browser_id+标签页；
   Trae：viewId），跳过重新探测。
2. 否则列已打开标签页，找 URL 含 `/ide/index.html`（标题 Primeton-IDE）的页面；
   没有 IDE 页面或未登录 → 先执行 `ynu-lowcode-login`。
3. Trae 多标签场景后续操作要**显式锁定 viewId**。

### Step 2 — 作用域确认（AskUserQuestion，必经）

1. 在左侧资源树确认目标构件包节点存在（Element Plus el-tree，
   节点只显示名称；层级可用 `closest('.el-tree-node')` 祖先计数判断）。
2. **必须**用 `AskUserQuestion` 确认：「当前应用 XXX 下构件包 <名称>，
   将创建实体集 <名称>(<编码>)，是否继续？」
3. 确认后继续；编码先按规则自查一遍再提交。

### Step 3 — 右键「实体」资源打开菜单

1. 展开目标构件包节点，找到其下的「实体」资源节点。
2. 右键该节点（Trae：`browser_click({ button: 'right', ref })`；
   WorkBuddy：对应右键工具），期待出现上下文菜单，其中含「新建实体集」。
3. **右键可能无反应**（实测：Trae 合成右键对部分树节点不触发自定义菜单，
   只会展开节点）。对策按序尝试：① 重取快照后重试一次右键；
   ② 键盘 ContextMenu 键；③ hover 节点看是否出现操作图标；
   ④ 仍不行则如实告知用户自动化无法呼出右键菜单，请用户手动点出菜单，
   然后从 Step 4 继续。
4. ⚠️ 红线：菜单中若出现任何「删除」项，一律不点击。

### Step 4 — 菜单中选「新建实体集」

- Trae：菜单项在快照中通常是独立节点，直接 `browser_click({ ref })`；
- WorkBuddy：DOM 中定位「新建实体集」菜单项后 `dom_cua_click`；
  若菜单项无独立节点，用键盘 `ArrowDown` 高亮 + `Enter` 确认。
- 等待弹窗出现（Trae：`browser_wait_for({ text: "实体集", timeout: 10 })`；
  WorkBuddy：轮询 DOM 约 2 秒）。

### Step 5 — 填写编码与名称

- **Trae**：优先 `browser_fill_form` 一次填两个字段，再重取快照确认 value。
- **WorkBuddy**：逐字段 click + type，每填一个重读 DOM 确认。
- 任一字段为空 → 重试一次；仍失败停下报告，不要提交半空表单。

### Step 6 — 提交并验证

1. 点弹窗的确认/创建按钮。
2. **成功验证以资源树为准**：重取快照/DOM，确认「实体」资源下出现新实体集名称
   （`wait_for` 命中的文本可能来自弹窗而非树，不能只凭它判定成功）。
3. 弹窗未关或有报错提示（如编码重复、格式不合规）→ 原样报告错误，不动其他内容。

### Step 7 — 保留会话

保持标签页打开，登录态与页面状态供后续 skill 复用。

## 不变量

1. **作用域必确认**：AskUserQuestion 确认构件包与实体集信息后方可提交。
2. **编码先自查**：汉字、空格、非法开头字符在提交前拦下。
3. **行动后验证**：每次点击后用快照/DOM 确认结果再继续；成功以资源树出现为准。
4. **失败即停**：不提交半空表单，不无限重试。
5. **删除红线**：任何「删除」入口一律不点击、不尝试。

## Notes / gotchas

- **右键菜单是最大风险点**：见 Step 3 的降级路线；不要反复硬试右键。
- **树技术栈**：左侧资源树是 Element Plus el-tree（非 antd Tree），
  节点只显示名称不显示编码；树节点上实测无悬停操作图标。
- **ref 时效性（Trae）**：弹窗出现/树刷新后旧 ref 失效（报 not visible），
  重新快照取新 ref，不要用旧 ref 硬重试。
- **CDP 输入超时（仅 WorkBuddy）**：点击前 `tab_focus` 置前并 sleep 约 2 秒；
  超时后等 5-15 秒再重试；键盘通道比鼠标稳。
- **Trae Exec 输出通道**：Exec 常规输出可能为空，需要数据时可用
  `throw new Error(JSON.stringify(data))` 从错误通道带出（调试手段）。
- **后续衔接**：实体集建好后，创建实体用 `ynu-eos8-import-entity`，
  生成表用 `ynu-eos8-generate-table`。
