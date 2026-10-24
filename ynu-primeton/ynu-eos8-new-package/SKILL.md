---
name: ynu-eos8-new-package
description: "在云大低代码平台（EOS8，dev-idm.ynu.edu.cn）当前打开的 IDE 中新建一个构件包。当用户要新建/创建构件包、构建包时使用。流程：确认已打开并登录 IDE（未登录则先调用 ynu-lowcode-login）→ 点工具栏「新建构件包」图标 → 下拉菜单中选「新建构件包」→ 弹窗填编码与名称 → 点「创建」→ 验证左侧资源树出现新包。使用 WorkBuddy Browser（mcp__browser__* 工具）操作。参数：包编码（必填）、包名称（必填）。"
agent_created: true
---

# 新建构件包（EOS8 低代码平台）

## Overview

在云南大学低代码开发平台（普元 EOS8，`dev-idm.ynu.edu.cn`）**当前打开的 IDE** 中
新建一个构件包（平台 UI 术语为「**构件包**」，不是"构建包"）。

流程概览：
确认 IDE 已打开且已登录 → 点工具栏「新建构件包」图标 → 下拉菜单中选「新建构件包」
→ 弹窗填编码 / 名称 → 点「创建」→ 验证资源树出现新包。

**作用域铁律**：构件包创建在「当前打开的 IDE 所属应用」下。创建前必须向用户
确认当前应用与目标作用域；只操作用户指定的范围，不碰其他应用 / 其他构建包。

## When to use

- 用户说「新建构件包 / 构建包」「建一个包」且上下文是云大低代码平台（EOS8）。
- 注意：平台需校园网或 WebVPN 环境。

## 参数

- **包编码**（必填）：如 `xmcbgl`。若用户给的是带前缀形式（如 `xmcbgl.xxx`），
  弹窗编码框应填**完整编码**。
- **包名称**（必填）：如「采购项目储备管理」。

缺任一参数 → 用 `AskUserQuestion` 询问，不要猜。

## Workflow

### Step 0 — 确认 IDE 已打开且已登录

1. `mcp__browser__browsers_list` 获取浏览器（取 `browser_id`），
   `mcp__browser__user_open_tabs` 列出已打开标签页。
2. **已有 IDE 页面**（URL 含 `/ide/index.html`，标题 Primeton-IDE）→
   `mcp__browser__tabs_claim` 接管，直接进 Step 1。
   - ⚠️ `appName` 参数值不固定（随用户所选应用变化），不要假设它是某个特定值；
     只要页面是 IDE 且已登录即可。
3. **没有 IDE 页面或未登录** → 调用 `ynu-lowcode-login` skill（它会引导登录、
   选应用、落到对应 IDE），完成后回来从其结果中认领 IDE 标签页。
4. `mcp__browser__dom_cua_get_visible_dom` 读 DOM，确认已登录且能看到左侧
   资源树（含「资源」与构件包名）。
5. **作用域确认**：告诉用户「当前应用是 XXX，构件包将建在其下」，开始执行。

### Step 1 — 点「新建构件包」图标，展开下拉菜单

1. 读 DOM，找到工具栏按钮：`role="button" title="新建构件包"`。
2. **先判断菜单状态**：若 DOM 中已出现独立的「导入构件包」div 节点，
   说明菜单**已展开**——再点图标会把菜单**关掉**（toggle 行为），此时跳过点击。
3. 点击图标（`mcp__browser__dom_cua_click`）。若遇 CDP 超时，见下方 gotcha 重试。
4. 等待约 1-2 秒，重读 DOM 确认菜单已展开（「导入构件包」div 出现即成功）。

### Step 2 — 菜单中选「新建构件包」

1. 菜单项在 DOM 快照中**没有独立节点**（内容被并入首个大 div），无法直接点击。
2. **最稳路线：键盘选择**。菜单展开时按 `ArrowDown` 高亮第一项，再 `Enter` 确认
   （`mcp__browser__dom_cua_keypress`）。
   - 菜单第一项 = **新建构件包**，第二项 = 导入构件包。**勿误选「导入构件包」**。
3. 等待约 2 秒，重读 DOM 确认弹窗已出现。

**弹窗特征**（用于验证）：两个 `type="text"` 输入框（① 编码 ② 名称）、
一个 `role="switch"` 开关、「取消」「创建」两个按钮、右上角 Close 图标。

### Step 3 — 填写编码与名称

1. `mcp__browser__dom_cua_click` 点第 1 个输入框 → `mcp__browser__dom_cua_type`
   输入**包编码**（支持中文/英文直接输入）。
2. 重读 DOM 确认 value 已写入。
3. 同法点第 2 个输入框，输入**包名称**，重读 DOM 确认。
4. 若两个字段任一为空（点击/输入失败），重试一次；仍失败则停下报告，不要提交半空表单。

### Step 4 — 点「创建」并验证

1. `mcp__browser__dom_cua_click` 点「创建」按钮。
2. 等待约 3 秒，重读 DOM 验证：
   - 弹窗已关闭；
   - **左侧资源树出现新包名称**，其下含「实体 / 页面 / 流程 / 服务 / 通用业务」子节点。
3. 两者都满足 → 成功，向用户汇报「构件包 <名称>(<编码>) 已创建」。
4. 弹窗未关或有报错提示 → 原样报告错误信息，不动其他内容。

### Step 5 — 保留会话

保持标签页打开，登录态与页面状态供后续 skill 复用。不要为清理而关闭页面。

## Notes / gotchas

- **CDP 输入超时频发**：`dom_cua_click` / `cua_click` 偶发
  `Input.dispatchMouseEvent timed out`（窗口在后台时必现）。对策：
  1. 每次点击前先 `mcp__browser__tab_focus` 置前，并 sleep 约 2 秒；
  2. 超时后等 5-15 秒，再 focus 重试，通常第 2-3 次恢复；
  3. 键盘事件通道（`dom_cua_keypress` / `dom_cua_type`）比鼠标通道稳定，
     能用键盘就用键盘（这也是 Step 2 用 ↓+Enter 选菜单的原因）。
- **菜单是 toggle**：图标点击在菜单已展开时会收起菜单。每次点击前先看
  DOM 里有没有「导入构件包」独立节点来判断菜单状态。
- **dom_cua_click 不认 CSS 选择器**：传 `#dropdown-menu-8076 > li` 这类
  选择器会报 stale。node_id 只能来自最近一次 DOM 快照。
- **验证手段**：截图工具会落盘（`/Users/na57/.workbuddy/blobs/...`）但**当前模型
  不支持读图**；一律以 DOM 快照作为验证依据。
- **测试包勿遗留**：测试产生的构件包若不再需要，提醒用户手动删除
  （或经用户确认后删除），保持环境干净。
