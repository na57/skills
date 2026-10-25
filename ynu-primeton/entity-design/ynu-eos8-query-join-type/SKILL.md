---
name: ynu-eos8-query-join-type
description: "在云大低代码平台（EOS8，dev-idm.ynu.edu.cn）当前打开的 IDE 实体设计器中，为查询实体添加连接类型（数据库跨平台：在 SQL 编辑区 tab 上点「+」为不同类型数据库配置各自的 SQL）。当用户说「添加连接类型」「跨数据库 SQL」「给查询实体配 oracle/mysql 的 SQL」时使用。流程：确认已登录 IDE → AskUserQuestion 确认目标查询实体与目标数据库类型 → 双击查询实体 → tab 上点「+」→ 新增连接类型并配置 SQL → 验证 default 仍在。兼容 WorkBuddy 与 Trae 双浏览器运行时。⚠️ 界面上的「删除」按钮/图标/菜单项严禁点击，严禁删除或清空 default 连接类型。"
agent_created: true
---

# 查询实体添加连接类型（数据库跨平台）（EOS8 实体设计器，WorkBuddy / Trae 双运行时兼容）

## Overview

在 EOS8 实体设计器中为查询实体做**数据库跨平台**配置。
官方描述：单击 SQL 编辑区 **tab 中的「+」**（官方图一位置 2）
可以**添加连接类型**；可对不同类型的数据库指定查询的 sql 语句，
但**必须指定一个 default 类型的配置**——EOS 在程序运行时
根据数据库连接自动判断数据库类型，按该类型的配置获取数据，
找不到对应配置时使用 default 类型的配置；
**生成实体时按照 default 类型进行查询**。

流程概览：
确认 IDE 已登录 → AskUserQuestion 确认目标查询实体、
目标数据库类型与对应 SQL → 双击查询实体 →
tab 栏点「+」添加连接类型 → 在新 tab 配置该类型 SQL →
验证 default 配置仍在 → 汇报。

**作用域铁律**：仅在当前已打开的实体设计器内操作，
不新建构件包、不碰无关资源。

## When to use

- 用户要为查询实体增加某种数据库类型（如 oracle、mysql）的
  专属 SQL 配置，实现一套查询实体跨多种数据库运行。

## Step 0 — 运行时探测（必须最先执行）

- 工具列表含 `mcp__browser__browsers_list` → **WorkBuddy 模式**。
- 工具列表含 integrated_code_mode 的 `Exec`（`await tools.browser_*`）→ **Trae 模式**。
- 两者都没有 → 提示用户启用对应浏览器扩展，终止流程。

## 参数

- **目标查询实体**（必填）：画布上的查询实体名称。
- **目标连接类型**（必填）：要新增的数据库类型（如 oracle、mysql）。
- **该类型 SQL**（必填）：该数据库方言的 SELECT 语句
  （或用户口述意图，经确认后落为 SQL）。

缺参数 → `AskUserQuestion` 询问，不要猜。

## Workflow

### Step 1 — 确认 IDE 已打开且已登录

复用 `ynu-lowcode-login` 等产出的 IDE 标签页/viewId；
未登录先执行 `ynu-lowcode-login`。

### Step 2 — 作用域确认（AskUserQuestion，必经）

确认：「将在 <设计器> 中为查询实体 <实体名> 添加连接类型
<数据库类型>，default 配置保持不变，是否继续？」

### Step 3 — 打开查询实体的 SQL 编辑区

1. 前置条件：画布上须已存在目标查询实体且已完成 default SQL 配置；
   没有则提示先走 `ynu-eos8-query-edit-sql` 配好 default，本 skill 终止。
2. **双击**目标查询实体进入配置界面。
3. 定位 SQL 编辑区顶部的 **tab 栏**（各连接类型一个 tab，
   其中含 default）。

### Step 4 — 点「+」添加连接类型并配置

1. 点击 tab 栏中的**「+」**（官方图一位置 2）。
2. 在新增的连接类型处选择目标数据库类型
   （新增 tab 后的具体表单/下拉文档未详述，以实际界面为准）。
3. 切换到新 tab，输入该数据库方言的 SQL 语句。
4. **不要触碰 default tab**：不切换删除、不清空、不改写。

### Step 5 — 验证与汇报

1. **验证方式**：tab 栏出现新增的连接类型 tab 且可切换；
   default tab 仍然存在且 SQL 完好（生成实体时按 default 类型查询，
   default 缺失会导致实体无法生成）。
2. 若用户要求，可点「查询」在新 tab 试跑——查询后数据库记录
   展示在查询条件下方的表格中，以表格为准。
3. 向用户汇报：新增的连接类型、该类型 SQL 要点、default 状态。

## 不变量

1. **default 红线**：default 连接类型必须保留；
   任何针对 default 的删除/清空操作严禁执行。
2. **删除红线**：界面上任何「删除」按钮/图标/菜单项（含 tab 上的
   删除图标）严禁点击。
3. **SQL 只读红线**：只允许 SELECT 语义（查询实体只能用于查询）。
4. **行动后验证**：以 tab 实际出现与 default 实际完好为准，
   不以点击成功为准。
5. **失败即停**：tab 上找不到「+」、新增失败，停止并汇报，
   转用户手动。

## Notes / gotchas

- **default 是兜底**：运行时按数据库连接自动判断类型，
  未匹配到已配置的连接类型时使用 default；因此 default 必填且不可动。
- **生成实体按 default 查询**：点击确认生成查询实体时
  按 default 类型的 SQL 执行查询。
- **新增 tab 的表单细节待人工核对**：官方文档仅说明
  「单击 tab 中『+』可以添加连接类型」，新增后的类型选择方式
  以实际界面为准。
- **id 保留字 / 重名列别名**：查询实体不能定义属性名叫 id 的属性
  （唯一标识对应属性可用 id）；SQL 有 2 个相同列名需起不同别名。
- **右键菜单可能无反应**：降级路线 ①重取快照重试 →
  ②键盘 ContextMenu 键 → ③hover 看图标 → ④请用户手动点出菜单。
- **Vue 条件渲染**：hover 图标以 `<!---->` 占位可能不因合成事件渲染，
  两次失败转用户手动。
- **ref 时效性（Trae）**：快照变化后旧 ref 失效，重新取。
- **CDP 超时（仅 WorkBuddy）**：点击前 focus + sleep 约 2 秒。
- **衔接**：default SQL 配置见 `ynu-eos8-query-edit-sql`；
  SQL 助手见 `ynu-eos8-query-sql-assistant`。
