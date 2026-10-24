---
name: ynu-eos8-new-package
description: "在云大低代码平台（EOS8，dev-idm.ynu.edu.cn）当前打开的 IDE 中新建一个构件包。当用户要新建/创建构件包、构建包时使用。流程：确认已打开并登录 IDE（未登录则先调用 ynu-lowcode-login）→ AskUserQuestion 确认作用域 → 点工具栏「新建构件包」图标 → 下拉菜单中选「新建构件包」→ 弹窗填编码与名称 → 点「创建」→ 验证左侧资源树出现新包。兼容两种浏览器运行时：WorkBuddy Browser（mcp__browser__* 工具）与 Trae（integrated_code_mode 的 Exec 内 browser_* 工具），启动时自动探测。参数：包编码（必填）、包名称（必填）。实测结论：编码中的点号只是普通字符（如 xmcbgl.sub 建成的是顶层包，不产生嵌套）。"
agent_created: true
---

# 新建构件包（EOS8 低代码平台，WorkBuddy / Trae 双运行时兼容）

## Overview

在云南大学低代码开发平台（普元 EOS8，`dev-idm.ynu.edu.cn`）**当前打开的 IDE** 中
新建一个构件包（平台 UI 术语为「**构件包**」，不是"构建包"）。

流程概览：
确认 IDE 已打开且已登录 → AskUserQuestion 确认作用域 → 点工具栏「新建构件包」图标
→ 下拉菜单选「新建构件包」→ 弹窗填编码 / 名称 → 点「创建」→ 验证资源树出现新包。

**作用域铁律**：构件包创建在「当前打开的 IDE 所属应用」下。创建前必须用
`AskUserQuestion` 向用户确认当前应用与目标作用域（单向播报不算确认）；
只操作用户指定的范围，不碰其他应用 / 其他构件包。

## When to use

- 用户说「新建构件包 / 构建包」「建一个包」且上下文是云大低代码平台（EOS8）。
- 注意：平台需校园网或 WebVPN 环境。

## Step 0 — 运行时探测（必须最先执行）

检查当前环境可用的工具集，确定运行模式，后续所有步骤按对应绑定执行：
- 工具列表含 `mcp__browser__browsers_list` → **WorkBuddy 模式**
- 工具列表含 integrated_code_mode 的 `Exec`（浏览器工具在 Exec 内以 `await tools.browser_*` 调用）→ **Trae 模式**
- 两者都没有 → 提示用户启用对应浏览器扩展，终止流程。

两种模式的关键差异：
| 差异点 | WorkBuddy | Trae |
|---|---|---|
| 调用方式 | 直接调用 `mcp__browser__*`，一次一个操作 | 必须在 Exec 内 `await tools.browser_*`，可合并 3~8 个操作减少往返 |
| 页面感知 | `dom_cua_get_visible_dom` 读 DOM | `browser_snapshot` 可访问性树（带 `ref`），操作后 ref 可能失效需重取 |
| 表单填写 | `dom_cua_click` + `dom_cua_type` 逐字段 | `browser_fill_form` 一次填多个字段（优先） |
| 等待手段 | 无条件等待工具，靠轮询 | `browser_wait_for({ text, timeout })` 条件等待（优先于固定 sleep） |
| CDP 超时 | `dispatchMouseEvent timed out` 频发，需 focus+sleep 重试 | 实测未出现 |

## 参数

- **包编码**（必填）：如 `xmcbgl`。若用户给的是带前缀形式（如 `xmcbgl.sub`），
  弹窗编码框填**完整编码**。
  ⚠️ **实测结论**：编码中的点号只是普通字符——填 `xmcbgl.sub` 创建成功且不报错，
  但建成的是**编码带点的顶层包**（与 `xmcbgl` 平级），**不会产生嵌套父子结构**。
  本弹窗没有「父包」概念。若用户期望建子包，先与用户确认实际意图再执行。
- **包名称**（必填）：如「采购项目储备管理」。

缺任一参数 → 用 `AskUserQuestion` 询问，不要猜。

## Workflow

### Step 1 — 确认 IDE 已打开且已登录

1. **优先复用上下文**：若本轮 `ynu-lowcode-login` 刚执行过，直接使用其产出的
   IDE 标签页（WorkBuddy：`browser_id`+标签页；Trae：`viewId`），跳过重新探测。
2. 否则列出已打开标签页（WorkBuddy：`browsers_list`+`user_open_tabs`；
   Trae：Exec 内 `browser_tabs({ action: 'list' })`），找 URL 含 `/ide/index.html`
   （标题 Primeton-IDE）的页面。
   - ⚠️ `appName` 参数值不固定（随应用变化），不要假设某个特定值。
   - ⚠️ Trae 多标签场景后续操作要**显式锁定 viewId**，不传会跟随活动标签漂移。
3. **没有 IDE 页面或未登录** → 调用 `ynu-lowcode-login` skill，完成后回来认领 IDE 标签页。
4. 读取页面确认已登录且左侧资源树已加载：
   - Trae：`browser_wait_for({ text: "资源信息加载完毕", timeout: 20 })`；
   - WorkBuddy：轮询 DOM 直到资源树出现（含「资源」与构件包名）。

### Step 2 — 作用域确认（AskUserQuestion，必经）

1. 从 IDE 页面 URL 或页面上下文确定当前应用名。
2. **必须**用 `AskUserQuestion` 确认：「当前应用是 XXX，构件包 <名称>(<编码>)
   将建在其下，是否继续？」——禁止只播报不确认（进错应用代价高）。
3. 用户确认后继续；用户改主意则按新指示处理。

### Step 3 — 点「新建构件包」图标，展开下拉菜单

1. 快照/DOM 中找工具栏按钮：`role="button" title="新建构件包"`。
2. **先判断菜单状态**（菜单是 toggle，已展开时再点会收起）：
   - Trae：快照中若已出现 `list → listitem "新建构件包" (+ listitem "导入构件包")` 结构，说明菜单已展开，跳过点击；
   - WorkBuddy：DOM 中已出现独立的「导入构件包」div 节点即已展开，跳过点击。
3. 点击图标展开菜单（Trae：`browser_click({ ref })`；WorkBuddy：`dom_cua_click`，
   点击前先 `tab_focus` 置前并 sleep 约 2 秒防 CDP 超时）。

### Step 4 — 菜单中选「新建构件包」（按运行时分支）

- **Trae（实测推荐）**：菜单项在快照中是**独立 `listitem` 节点**，直接
  `browser_click({ ref: <「新建构件包」listitem 的 ref> })`。无需键盘路线。
  第二项是「导入构件包」，注意别点错。
- **WorkBuddy（实测）**：菜单项在 DOM 中**没有独立节点**（内容被并入首个大 div），
  无法直接点击。**最稳路线是键盘选择**：菜单展开时 `dom_cua_keypress` 按
  `ArrowDown` 高亮第一项，再 `Enter` 确认。第一项 = 新建构件包，
  **勿误选「导入构件包」**。
- 等待弹窗出现（Trae：`browser_wait_for({ text: "创建构件包", timeout: 10 })`；
  WorkBuddy：轮询 DOM 约 2 秒）。

**弹窗特征**（实测，用于验证）：`role="dialog"` 标题「创建构件包」，
含两个 textbox（① 构件包代码 ② 构件包名称）、一个 switch（「是否报表构件包」，
默认禁用）、「取消」「创建」按钮、右上角 Close 图标。

### Step 5 — 填写编码与名称

- **Trae**：优先 `browser_fill_form` 一次填两个字段（编码框、名称框的 ref 来自
  最新快照），然后重取快照确认 value 已写入。
- **WorkBuddy**：`dom_cua_click` 点第 1 个输入框 → `dom_cua_type` 输入**包编码**
  → 重读 DOM 确认；同法填第 2 个输入框（**包名称**）。
- 任一字段为空 → 重试一次；仍失败停下报告，不要提交半空表单。

### Step 6 — 点「创建」并验证

1. 点「创建」按钮（Trae：`browser_click({ ref })`；WorkBuddy：`dom_cua_click`）。
2. 等待结果（Trae：`browser_wait_for({ text: "<包名称>", timeout: 12 })`；
   WorkBuddy：轮询约 3 秒）。
3. **成功验证以资源树为准**：`wait_for` 等到的文本可能来自弹窗而非树，
   最终必须重取快照/DOM 确认**左侧资源树出现新包名称**，其下含
   「实体 / 页面 / 流程 / 服务 / 通用业务」子节点。
   - 树技术栈提示：左侧资源树是 **Element Plus el-tree**（非 antd Tree），
     节点只显示**名称**不显示编码。
4. **「生成页面」引导弹窗**（实测：首次创建后出现，内容含包名下拉；
   再次创建未必复现，出现条件待定）：
   - 这是平台创建成功后的引导步骤，**不影响包已创建的事实**；
   - 优先点其 Close/取消关闭；若按钮 ref 报 not visible，重新快照取新 ref 再试；
   - 仍关不掉时不要反复重试，如实告知用户手动关闭即可，主流程继续。
5. 树中出现新包 → 向用户汇报「构件包 <名称>(<编码>) 已创建」。
6. 弹窗未关或有报错提示 → 原样报告错误信息，不动其他内容。

### Step 7 — 保留会话

保持标签页打开，登录态与页面状态供后续 skill 复用。不要为清理而关闭页面。

## 不变量（两种运行时都必须遵守）

1. **作用域必确认**：创建前必须 `AskUserQuestion` 确认应用与包信息，单向播报不算。
2. **编码点号不嵌套**：编码中的点只是普通字符；用户提到「子包」时先确认意图。
3. **行动后验证**：每次点击后用快照/DOM 确认结果再继续；最终成功判定以
   **资源树出现新包**为准，不以 `wait_for` 命中或弹窗关闭为准。
4. **失败即停**：字段填不上、创建报错时原样报告，不提交半空表单、不重试超过约定次数。
5. **测试包勿遗留**：树节点无右键菜单、无悬停操作图标，删除入口不在左树上；
   测试产生的构件包提醒用户手动删除（或经用户确认后另行处理）。

## Notes / gotchas

- **CDP 输入超时（仅 WorkBuddy）**：`dom_cua_click` / `cua_click` 偶发
  `Input.dispatchMouseEvent timed out`（窗口在后台时必现）。对策：
  每次点击前 `tab_focus` 置前并 sleep 约 2 秒；超时后等 5-15 秒再 focus 重试，
  通常第 2-3 次恢复；键盘通道（`dom_cua_keypress` / `dom_cua_type`）比鼠标稳。
- **菜单是 toggle**：图标点击在菜单已展开时会收起菜单。每次点击前先判断菜单状态
  （见 Step 3）。
- **ref/节点时效性**：Trae 的 ref 只在最近一次快照内可靠，页面变化（弹窗出现/
  关闭、树刷新）后旧 ref 会失效（报 not visible 等）——重新快照取新 ref，
  不要用旧 ref 硬重试。
- **Trae Exec 输出通道**：Exec 的常规输出可能为空，需要数据时可用
  `throw new Error(JSON.stringify(data))` 从错误通道带出（调试手段，勿留在正式流程）。
- **验证手段**：验证以**快照/DOM**为准；截图可作辅助。操作后等页面稳定
  （条件等待优先，固定 sleep 次之）再验证。
- **skill 间衔接**：本 skill 应优先复用 `ynu-lowcode-login` 产出的 IDE 标签页 /
  viewId，避免重复列标签页；无法获取时再自行探测。
