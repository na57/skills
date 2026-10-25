---
name: ynu-eos8-flow-env-vars
description: "在云大低代码平台（EOS8，dev-idm.ynu.edu.cn）中查看与使用环境变量：在服务设计器逻辑流中通过上下文内置对象 systemVars（平台系统变量）、appSystemVars（应用系统变量）与 MUO（当前登录用户，m:userObject/xxx）取值、赋值与变量替换（${systemVars.编码} 等）；变量本体的管理在 AFCenter 平台系统变量菜单。当用户说「流程里用系统变量」「环境变量怎么取」「服务地址用变量替换」时使用。流程：确认已登录 IDE → AskUserQuestion 确认变量与用途 → 作用域确认 → 取值/赋值/替换配置 → 保存 → 执行验证。兼容 WorkBuddy 与 Trae 双浏览器运行时。⚠️ 任何「删除」按钮/图标/菜单项（删图元、删变量）严禁点击。"
agent_created: true
---

# 环境变量（EOS8 服务设计器 + AFCenter 管理页，WorkBuddy / Trae 双运行时兼容）

## Overview

环境变量让应用程序适应不同运行环境
（开发/测试/生产用不同变量配置行为），并可在逻辑流中
传递参数与赋值（官方「环境变量」文档）。

**入口与作用域说明（本 skill 与纯画布 skill 不同）**：
- **取值与引用**在服务设计器逻辑流内：逻辑流上下文中
  平台系统变量 `systemVars` 与当前应用的应用系统变量
  `appSystemVars` 作为**全局变量默认存在**，
  通过 `systemVars/xxx`、`appSystemVars/xxx` 取值；
  当前登录用户信息在 MUO 中，通过
  `m:userObject/xxx` 取值（如 `m:userObject/userId`）。
- **变量本体的管理与维护在 AFCenter 平台**（不在服务
  设计器内）：系统变量在 AFCenter **系统变量菜单**；
  应用系统变量在 **AFCenter 应用门户内的系统变量菜单**。
  本 skill 默认只读浏览该页面；新增/修改须用户明确要求。

变量替换写法（用于三方服务集的服务地址/认证方式、
rest 服务地址等配置位）：
- `${systemVars.变量编码}` —— 平台系统变量；
- `${appSystemVars.应用系统变量编码}` —— 应用系统变量；
- `${bizVars.逻辑流变量定义名称}` —— 逻辑流内置变量。

流程概览：
确认 IDE 已登录 → AskUserQuestion 确认变量与用途 →
作用域确认 → （按需）AFCenter 查看变量定义 →
逻辑流内取值/赋值/替换 → 保存 → 执行验证。

**作用域铁律**：逻辑流操作仅限**当前打开的服务编排**；
AFCenter 变量页面只读浏览，不碰任何删除按钮。

## When to use

- 用户想在逻辑流里读取系统变量/应用系统变量/登录用户信息。
- 用户想让服务地址、三方服务集配置按环境切换
  （变量替换）。
- 用户想查看某环境变量当前值。

## Step 0 — 运行时探测（必须最先执行）

- 工具列表含 `mcp__browser__browsers_list` → **WorkBuddy 模式**：
  用 mcp__browser__* 工具操作；take_snapshot 取可交互元素快照，
  ref 有时效性，画布重渲染后须重取快照；点击前可先对目标元素
  focus 并 sleep 约 2 秒，避免 CDP 超时。
- 工具列表含 integrated_code_mode 的 `Exec`（`await tools.browser_*`）→
  **Trae 模式**：用该运行时操作；同样注意快照 ref 时效性，
  每次操作前重取快照。
- 两者都不可用 → 终止并告知用户当前无可用浏览器运行时。

## 参数

- **变量对象**（必填）：systemVars / appSystemVars /
  MUO（m:userObject）。
- **变量编码/属性**（按需）：如 `systemVars.threeServiceUrl`、
  `m:userObject/userId`；不知道编码可先查。
- **用途**（必填）：赋值给逻辑流变量 / 配置替换 / 仅查看值。

缺参数 → `AskUserQuestion` 询问，不要猜。

## Workflow

### Step 1 — 确认 IDE 已打开且已登录

复用 `ynu-lowcode-login` 等产出的 IDE 标签页/viewId；
未登录先执行 `ynu-lowcode-login`。

### Step 2 — 作用域确认（AskUserQuestion，必经）

确认：「将在服务设计器当前逻辑流中
<把 systemVars.xxx 赋值 / 用 ${...} 替换配置 /
查看变量值>，是否继续？」
若需进 AFCenter 变量菜单查看定义，一并确认
（该页面只读浏览）。

### Step 3 — 查看变量值（断点调试，官方验证方式）

1. 打开目标逻辑流：右键任意图元「设置断点」→
   左上角「开启调试」→ 执行逻辑流。
2. 在调试信息中查看当前逻辑流上下文：
   可见 `systemVars`、`appSystemVars`、
   MUO 用户信息及其属性字段值。
3. 只读查看，不修改调试界面之外的任何配置。

### Step 4 — 逻辑流内取值/赋值

1. 双击画布空白打开逻辑流属性设置，
   定义用于承接值的变量（如 `params`）。
2. 在**赋值图元**中：左值设为目标变量，
   右值取系统变量属性值（点 V 图标打开选择值弹窗，
   选择 `systemVars/xxx` / `appSystemVars/xxx`；
   MUO 用 `m:userObject/xxx`，如 userId）。
3. 保存逻辑流。

### Step 5 — 配置位变量替换（按需）

1. 三方服务集服务地址/认证方式、rest 服务地址等
   支持替换：打开对应配置弹窗，
   将值写为 `${systemVars.编码}` /
   `${appSystemVars.编码}` / `${bizVars.变量名}`。
2. **代码红线**：替换串写入编辑器前必须先向用户
   展示并确认。
3. 保存后执行验证。

### Step 6 — 执行验证

1. 点击逻辑流编辑器**左上角执行图标**打开执行弹窗，
   执行并核对：变量承接值正确读出
   （断点调试看赋值结果，或经返回值带出）。
2. 验证以**变量值实际读出**为准，
   不以赋值图元配置成功为准。

## 不变量

1. **作用域铁律**：逻辑流只动当前打开的服务编排；
   AFCenter 变量页面只读。
2. **删除红线**：任何「删除」按钮/图标/菜单项
   （含系统变量菜单中的删除）严禁点击。
3. **代码红线**：`${...}` 替换串写入前先展示确认。
4. **行动后验证**：以断点调试/返回值中变量实际读出为准。
5. **失败即停**：找不到变量编码时停下询问用户，不猜编码。

## Notes / gotchas

- **两套入口别混淆**：变量**本体**的增改在
  AFCenter（系统变量菜单/应用门户-系统变量菜单），
  服务设计器内只能**取值引用**；用户要求新增/修改变量
  本体时说明入口差异并征得同意。
- **取值语法两处不同**：赋值图元/选择值弹窗用
  `systemVars/xxx`、`m:userObject/xxx` 斜杠路径；
  配置替换串用 `${systemVars.xxx}` 花括号点号写法。
- **作用域层级**：systemVars 平台级、appSystemVars
  应用级、bizVars 逻辑流级，选择时按层级取。
- **MUO 常用属性**：`m:userObject/userId` 取当前
  登录用户 ID；其余属性可在断点调试中查看全集。
- **ref 时效性**：画布/弹窗/平台页面重渲染后旧 ref 失效，
  操作前重取快照。
- **CDP 超时（仅 WorkBuddy）**：点击前 focus + sleep 约 2 秒。
- **衔接**：三方服务变量替换 `ynu-eos8-flow-third-party`；
  rest 地址替换 `ynu-eos8-flow-rest`；
  赋值图元细节 `ynu-eos8-flow-variable-assign`。
