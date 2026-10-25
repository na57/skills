---
name: ynu-eos8-toggle-audit-fields
description: "在云大低代码平台（EOS8，dev-idm.ynu.edu.cn）当前打开的 IDE 实体设计器中，通过 toolbar 的审计字段按钮切换系统字段（createUser/createTime/updateUser/updateTime）的显示与隐藏。当用户说「显示审计字段」「看看系统字段」「隐藏审计字段」时使用。默认这些字段隐藏。流程：确认已登录 IDE → 确认期望开关方向 → 打开实体设计器 → 点 toolbar 审计字段按钮 → 验证。兼容 WorkBuddy 与 Trae 双浏览器运行时。"
agent_created: true
---

# 显示/隐藏审计字段（EOS8 实体设计器 toolbar，WorkBuddy / Trae 双运行时兼容）

## Overview

EOS8 实体设计器 **toolbar** 提供「审计字段显示」按钮，控制一组
审计（系统）字段的显示与隐藏：
- `createUser`（创建用户）
- `createTime`（创建时间）
- `updateUser`（更新用户）
- `updateTime`（更新时间）

**默认隐藏**，需主动操作显示。toolbar 同区还有画布全屏、放大、缩小、
百分比调整等按钮，注意别点错。

流程概览：
确认 IDE 已登录 → 确认期望方向 → 打开实体设计器 →
点 toolbar 审计字段按钮 → 验证字段显示/隐藏。

## When to use

- 用户说「显示审计字段」「看看 createUser/createTime 这些系统字段」「隐藏审计字段」。

## Step 0 — 运行时探测（必须最先执行）

- 工具列表含 `mcp__browser__browsers_list` → **WorkBuddy 模式**。
- 工具列表含 integrated_code_mode 的 `Exec`（`await tools.browser_*`）→ **Trae 模式**。
- 两者都没有 → 提示用户启用对应浏览器扩展，终止流程。

## 参数

- **目标状态**（必填）：`显示` 或 `隐藏`。
- **目标设计器**（按需）：在哪个构件包的实体设计器中操作。

缺参数 → `AskUserQuestion` 询问，不要猜。

## Workflow

### Step 1 — 确认 IDE 已打开且已登录

复用 `ynu-lowcode-login` 等产出的 IDE 标签页/viewId；
未登录先执行 `ynu-lowcode-login`。

### Step 2 — 状态确认（AskUserQuestion，必经）

确认：「将在 <设计器> 中把审计字段切换为 <显示/隐藏>，是否继续？」

### Step 3 — 打开实体设计器，判断当前状态

1. 资源树双击实体集/实体打开实体设计器。
2. 定位 toolbar 中的审计字段显示按钮。
3. **toggle 先判态**：观察画布中实体是否已显示四个审计字段
   （createUser/createTime/updateUser/updateTime）：
   - 已是目标状态 → 不点击，直接汇报；
   - 不是 → 继续。

### Step 4 — 点击审计字段按钮

1. 点击 toolbar 审计字段按钮（按钮可能是图标态，
   按 title/结构定位，别点成全屏/缩放按钮）。
2. 定位不到（Vue 条件渲染/图标无文字）：① 重取快照重试一次；
   ② 请用户手动点击，agent 接手验证。

### Step 5 — 验证

1. 重取快照/DOM：实体属性中四个审计字段出现（或消失），
   与目标状态一致。
2. 不一致 → 再点一次复验（至多一次）；仍不对如实报告。

### Step 6 — 保留会话

保持标签页与设计器打开，供后续 skill 复用。

## 不变量

1. **toggle 先判态**：已是目标状态不点击。
2. **行动后验证**：以实体上审计字段的实际显示/隐藏为准。
3. **失败即停**：重试至多一次后转用户手动。
4. **删除红线**：操作中出现的任何「删除」入口一律不点击。

## Notes / gotchas

- **toolbar 按钮密集**：全屏/放大/缩小/百分比与审计字段按钮同区，
  定位时核对 title/结构，防误点。
- **默认隐藏**：用户第一次找「createUser 字段」找不到时，
  主动建议本 skill。
- **ref 时效性（Trae）**：状态切换后旧 ref 失效，重新快照。
- **CDP 超时（仅 WorkBuddy）**：点击前 focus + sleep 约 2 秒。
- **衔接**：字段级编辑见 `ynu-eos8-edit-entity`（含「添加审计字段」快捷按钮）。
