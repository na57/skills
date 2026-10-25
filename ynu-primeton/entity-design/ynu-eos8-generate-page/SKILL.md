---
name: ynu-eos8-generate-page
description: "在云大低代码平台（EOS8，dev-idm.ynu.edu.cn）当前打开的 IDE 中，由实体生成页面。当用户说「生成页面」「建页面」「用实体生成表单」时使用。两种入口：右键实体→生成页面；或构件包下「页面」资源右键→生成页面。流程：确认已登录 IDE → AskUserQuestion 确认入口与目标 → 右键目标 → 菜单选「生成页面」→ 按向导完成 → 验证页面出现。兼容 WorkBuddy 与 Trae 双浏览器运行时。"
agent_created: true
---

# 生成页面（EOS8 低代码平台，WorkBuddy / Trae 双运行时兼容）

## Overview

在 EOS8 IDE 中由实体生成页面。官方提供两种入口：
1. **通过实体生成页面**：右键点击**实体** → 生成页面；
2. **通过资源树生成页面**：构件包下选**页面**资源，右键 → 生成页面。

流程概览：
确认 IDE 已登录 → AskUserQuestion 确认入口与目标 → 右键目标 →
菜单「生成页面」→ 按向导完成配置 → 验证页面生成。

**作用域铁律**：生成前必须用 `AskUserQuestion` 确认目标实体
（或目标构件包的页面资源）与生成选项；单向播报不算确认。

## When to use

- 用户说「生成页面」「给实体建页面」「生成表单页面」。
- 前置：目标实体已存在（`ynu-eos8-import-entity` /
  `ynu-eos8-drag-create-entity` / `ynu-eos8-create-entity-from-datasource`），
  持久化实体需先有表（`ynu-eos8-generate-table`）。

## Step 0 — 运行时探测（必须最先执行）

- 工具列表含 `mcp__browser__browsers_list` → **WorkBuddy 模式**。
- 工具列表含 integrated_code_mode 的 `Exec`（`await tools.browser_*`）→ **Trae 模式**。
- 两者都没有 → 提示用户启用对应浏览器扩展，终止流程。

## 参数

- **入口**（必填二选一）：`通过实体`（需实体名）或 `通过页面资源`（需构件包名）。
- **生成选项**（按向导实际项）：如页面类型/模板等，向导中出现时
  将默认值汇报给用户确认后再继续。

缺参数 → `AskUserQuestion` 询问，不要猜。

## Workflow

### Step 1 — 确认 IDE 已打开且已登录

复用 `ynu-lowcode-login` 等产出的 IDE 标签页/viewId；
未登录先执行 `ynu-lowcode-login`。

### Step 2 — 作用域确认（AskUserQuestion，必经）

确认：「将通过 <实体 XXX / 构件包 XXX 的页面资源> 生成页面，是否继续？」
若用户已指定页面类型等选项，一并在确认中列出。

### Step 3 — 右键目标打开菜单

1. 入口为实体 → 资源树（或设计画布）中右键目标实体节点；
   入口为页面资源 → 展开构件包，右键「页面」资源节点。
2. **右键可能无反应**（合成右键对部分节点不触发自定义菜单）。
   降级路线：① 重取快照重试一次；② 键盘 ContextMenu 键；
   ③ hover 看操作图标；④ 请用户手动点出菜单后继续。
3. ⚠️ 红线：菜单中任何「删除」项一律不点击。

### Step 4 — 菜单选「生成页面」

- 快照/DOM 中定位「生成页面」菜单项点击；无独立节点时
  键盘 `ArrowDown` + `Enter`。
- 等待生成向导/弹窗出现（Trae：`browser_wait_for` 特征文本；
  WorkBuddy：轮询 DOM）。

### Step 5 — 完成向导

1. 逐项读取向导字段（页面名称、类型等）。
2. 用户未指定的选项：向用户汇报默认值并确认后再改/再下一步；
   用户指定的按指定值填写（Trae：`browser_fill_form` 优先；
   WorkBuddy：逐字段 click + type）。
3. 每填一步重取快照确认 value 已写入。

### Step 6 — 提交并验证

1. 点完成/生成按钮。
2. **成功验证以资源树为准**：重取快照/DOM，确认构件包「页面」资源下
   出现新页面节点（或实体「查看页面」中能看到新页面）。
3. 有报错 → 原样报告，不动其他内容。

### Step 7 — 保留会话

保持标签页打开，供后续 skill 复用；可用 `ynu-eos8-view-entity-pages`
核对实体关联页面。

## 不变量

1. **生成前必确认**：入口、目标、关键选项经 AskUserQuestion 确认。
2. **行动后验证**：成功以资源树出现新页面为准，不以向导关闭为准。
3. **失败即停**：报错原样报告，不擅自改配置重试超过一次。
4. **删除红线**：任何「删除」入口一律不点击、不尝试。

## Notes / gotchas

- **右键菜单降级路线**见 Step 3；不要反复硬试右键。
- **树技术栈**：Element Plus el-tree，节点只显示名称不显示编码。
- **ref 时效性（Trae）**：向导出现/树刷新后旧 ref 失效，重新快照。
- **CDP 超时（仅 WorkBuddy）**：点击前 focus + sleep 约 2 秒。
- **衔接**：生成后可用 `ynu-eos8-view-entity-pages` 查看实体全部页面。
