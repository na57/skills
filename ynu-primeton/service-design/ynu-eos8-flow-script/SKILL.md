---
name: ynu-eos8-flow-script
description: "在云大低代码平台（EOS8，dev-idm.ynu.edu.cn）当前打开的 IDE 服务设计器中，使用脚本图元编写 Groovy 脚本处理业务逻辑：拖入脚本图元、通过选择值弹窗引用变量/入参/返回值、context 上下文与环境变量访问、helper.echo 调试。当用户说「加个脚本」「写段 Groovy」「用脚本处理」时使用。流程：确认已登录 IDE → AskUserQuestion 明确脚本职责 → 作用域确认 → 脚本草稿经用户确认 → 拖入脚本图元写入 → 保存执行验证。兼容 WorkBuddy 与 Trae 双浏览器运行时。⚠️ 代码红线：脚本内容写入编辑器前必须先向用户展示并确认；删除类按钮/图标严禁点击。"
agent_created: true
---

# 脚本元素（EOS8 服务设计器，WorkBuddy / Trae 双运行时兼容）

## Overview

在 EOS8 服务设计器中用**脚本图元**编写脚本、
简化数据处理。官方要点：
- 脚本编写规则与 **Groovy** 一致（基于 JVM，
  可直接调用 Java 类和方法）。
- 脚本中**直接用参数名即可获取逻辑流入参**，
  无需额外配置。
- 可读写已定义的**变量、输入参数、返回值**
  （脚本图元属性设置中打开「选择值」弹窗，
  在变量类型区域选择已定义的变量与参数，
  减少手敲出错）。
- 支持通过 `import` 调用 Java 类与
  AFCENTER SDK 接口。
- **环境变量**：系统变量 `context.systemVars.get("键名")`；
  应用系统变量 `context.appSystemVars.get("键名")`；
  用户变量 `userObject.getUserId()`（也可在
  选择值弹窗的方法区域选择）。
- **调试日志**：内置 `helper.echo(obj)` 输出变量值，
  断点调试时在变量区查看
  `___echoMessage_invokePojo2` 等输出变量。

**代码红线（本 skill 核心约束）**：
脚本内容是代码——**写入编辑器前必须先向用户
展示脚本全文并获确认**，未确认不得写入。

流程概览：确认 IDE 已登录 → AskUserQuestion 明确
脚本职责 → 作用域确认 → 脚本草稿展示确认 →
拖入脚本图元写入 → 保存执行验证。

**作用域铁律**：仅操作服务设计器中当前打开的服务编排，
不碰其他设计器与其他服务。

## When to use

- 赋值图元/常规图元表达不了的灵活逻辑
  （集合处理、条件组合、调用 SDK 等）。
- 用户明确要求用脚本/Groovy 实现。

## Step 0 — 运行时探测（必须最先执行）

- 工具列表含 `mcp__browser__browsers_list` → **WorkBuddy 模式**：
  用 mcp__browser__* 工具操作；take_snapshot 取可交互元素快照，
  ref 有时效性，画布/编辑器重渲染后须重取快照；点击前可先对
  目标元素 focus 并 sleep 约 2 秒，避免 CDP 超时。
- 工具列表含 integrated_code_mode 的 `Exec`（`await tools.browser_*`）→
  **Trae 模式**：用该运行时操作；同样注意快照 ref 时效性，
  每次操作前重取快照。
- 两者都不可用 → 终止并告知用户当前无可用浏览器运行时。

## 参数

- **脚本职责**（必填）：输入（读哪些变量/入参）、
  处理逻辑、输出（写哪个变量/返回值）。
- **脚本内容**（必填）：Groovy 脚本全文；
  **写入前向用户展示并确认**。

缺参数 → `AskUserQuestion` 询问，不要猜。

## Workflow

### Step 1 — 确认 IDE 已打开且已登录

复用 `ynu-lowcode-login` 等产出的 IDE 标签页/viewId；
未登录先执行 `ynu-lowcode-login`。

### Step 2 — 作用域确认（AskUserQuestion，必经）

确认：「将在服务设计器中为 <服务/流程名> 添加脚本图元，
实现 <脚本职责概述>，是否继续？」

### Step 3 — 编写脚本草稿并展示确认（代码红线）

1. 按职责起草 Groovy 脚本（语法备忘见下方 gotchas）。
2. **将脚本全文展示给用户并确认后**才可进入 Step 5 写入；
   用户未确认前不得写入编辑器。

### Step 4 — 拖入脚本图元

从元素面板将**脚本**图元拖入画布目标位置并接入连线；
程序化拖拽两次失败即转用户手动拖入。

### Step 5 — 写入脚本内容

1. 打开脚本图元属性设置的脚本编辑器。
2. 写入已确认的脚本内容（优先用**选择值弹窗**
   插入变量/参数引用，避免手拼写错）。
3. 需要调试输出时加入 `helper.echo(...)`。

### Step 6 — 保存并执行验证

1. 保存逻辑流。
2. 执行弹窗输入参数执行；断点调试查看变量区
   （含 `___echoMessage_invokePojo2` 的 echo 输出）；
   **以变量/返回值实际读出为准**。
3. 结果不符 → 回到 Step 3 修改草稿并**重新展示确认**。

## 不变量

1. **作用域铁律**：只动当前打开的服务编排画布。
2. **代码红线**：脚本全文未经用户确认不得写入编辑器；
   每次修改后须重新确认。
3. **删除红线**：任何「删除」按钮/图标严禁点击。
4. **行动后验证**：以断点/返回值中实际数据为准。
5. **失败即停**：编辑器两次定位失败即报告，
   不盲目重试。

## Notes / gotchas

- **Groovy 语法备忘**：`def name = "John"` 定义变量；
  支持 if/else、switch、while、for；
  集合 `[1,2,3]`、`size()`、`each{}`；
  闭包 `{ a -> a + 1 }`；直接调用 Java 类与方法；
  更多看 Groovy 官方文档。
- **脚本中访问本流变量用 `context.xxx`**
  （如 `context.out = ...`、`context.sysVar = ...`）。
- **SDO 取属性必须用 get**：
  `context.model.get("type")`，
  **不要** `context.model.type`——
  字段名撞逻辑流内部关键字时打点取不到值。
- **数组/对象是引用传递**：把数组赋给新变量后改新变量
  会连带改原数组；需要独立副本用
  `context.arrays.clone()`。
- **数组↔集合互转**：数组转集合
  `new HashSet<>(numbers)`；集合转数组
  `numberSet.toArray(new Integer[0])`。
- **Map 转 SDO 实体**：
  `JsonUtil.toJson(param)` 后
  `JsonUtil.toObject(json, DataObjectType.createType("实体全名"))`；
  或 `helper.cast(obj, context.out.class)`。
- **ref 时效性**：脚本编辑器重渲染后旧 ref 失效，
  操作前重取快照。
- **CDP 超时（仅 WorkBuddy）**：点击前 focus + sleep 约 2 秒。
- **衔接**：简单赋值优先用赋值图元
  `ynu-eos8-flow-variable-assign`；
  参数定义用 `ynu-eos8-flow-io-params`。
