---
name: ynu-eos8-flow-rest
description: "在云大低代码平台（EOS8，dev-idm.ynu.edu.cn）当前打开的 IDE 服务设计器中，使用 REST 服务图元调用外部/远程 REST 接口：配置请求 URL、Http Method、传参类型（URL/HEADER/BODY/QUERY/MULTI_BODY）、请求头凭证与返回值映射 → 保存 → 执行验证。当用户说「流程里调 REST 接口」「逻辑流调远程服务」「调个 HTTP 接口」时使用。流程：确认已登录 IDE → AskUserQuestion 确认接口信息 → 作用域确认 → 拖图元并配置 → 保存 → 执行验证。兼容 WorkBuddy 与 Trae 双浏览器运行时。⚠️ 任何「删除」按钮/图标/菜单项严禁点击；URL/请求头/请求体模板写入编辑器前必须先向用户展示并确认。"
agent_created: true
---

# REST 服务图元——调用远程服务（EOS8 服务设计器，WorkBuddy / Trae 双运行时兼容）

## Overview

在 EOS8 **服务设计器**中，
**REST 服务活动图元**用于调用一个外部 Rest 服务的接口
（如短信、地图等服务接口），实现与外部系统的数据交互。

官方要点：
- 输入参数和返回值支持 **SDO 数据格式**：入参可传
  DataObject 对象、DataObject 的 Xpath（如 `order/orderID`）
  或基本类型变量；返回值可得 DataObject 或基本类型，
  可封装为 `ResponseEntity` 对象。
- **URL 格式**：`http://{ip}:{port}/xxx`；
  也可用应用名称，如
  `http://SERVICE-PROVIDER:8080/api/user/getName/`，
  应用名称对应项目 `application.properties` 中的
  `spring.application.name`。
- **传参类型五种**：URL、HEADER、BODY、QUERY、MULTI_BODY；
  其中 "URI" 类型同时支持 Path 上的变量和 Query 的变量，
  如 `http://SERVICE-PROVIDER:8082/say-hi/{name}?username={name}`。
- 输入参数中可设置接口请求头 **Content-Type** 与
  **访问凭证（Authorization）**等信息。
- 参数与返回值的**名称、数据类型、传参类型**都必须与
  实际接口定义一致。
- 调用日志：记录在应用 `logs/eos-dap-trace.log`
  （`comp=REST_TEMPLATE` 行含请求头与入参出参）；
  需在后端 `application-afc.properties` 开启
  `eos.logging.inbound.enabled=true`、
  `eos.logging.outbound.enabled=true` 等配置。
- URL 中的服务地址支持**变量替换**
  （如 `${systemVars.xxx}`，见 `ynu-eos8-flow-env-vars`）。

流程概览：
确认 IDE 已登录 → AskUserQuestion 确认接口信息 →
作用域确认 → 拖图元入画布并连线 → 配置 URL/Method/参数 →
保存 → 执行验证。

**作用域铁律**：仅操作服务设计器中**当前打开的服务编排**，
不碰其他设计器、其他服务；不执行任何删除类按钮。

## When to use

- 用户想在流程/逻辑流里调用外部 REST 接口获取或推送数据。
- 用户描述「流程里调 HTTP 接口」「对接外部系统接口」等需求。

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

- **请求 URL**（必填）：完整接口地址。
- **Http Method**（必填）：GET/POST 等。
- **输入参数**（按需）：名称、数据类型、传参类型
  （URL/HEADER/BODY/QUERY/MULTI_BODY）。
- **请求头**（按需）：Content-Type、Authorization 凭证。
- **返回值**（按需）：类型与实际接口返回一致。

缺参数 → `AskUserQuestion` 询问，不要猜。

## Workflow

### Step 1 — 确认 IDE 已打开且已登录

复用 `ynu-lowcode-login` 等产出的 IDE 标签页/viewId；
未登录先执行 `ynu-lowcode-login`。

### Step 2 — 作用域确认（AskUserQuestion，必经）

确认：「将在服务设计器当前逻辑流中加入 REST 服务图元，
调用 <METHOD> <URL>，是否继续？」

### Step 3 — 定义参数并拖图元

1. 双击画布空白打开逻辑流属性设置，
   按接口定义创建输入参数与返回值。
2. 从元素面板把 **REST 服务图元**拖入画布
  （开始与结束之间），拉线连接。
   - 画布拖拽若为 HTML5 拖拽，程序化拖拽常失败：
     **两次失败即转用户手动拖拽**，agent 接手配置。

### Step 4 — 配置图元（双击图元打开属性弹窗）

1. 输入请求 URL；Http Method 选择框选对类型。
2. 逐项配置输入参数：名称、数据类型、**传参类型**
   与实际接口一致；Path/Query 占位用 "URI" 类型。
3. 需要鉴权/指定格式时，在输入参数中设置
   请求头 Content-Type 与 Authorization 凭证。
4. 返回值：填逻辑流返回值（SDO/DataObject、基本类型
   或 ResponseEntity）。
5. **代码红线**：URL、请求头、请求体模板等内容
   写入编辑器前，必须先向用户展示并确认。

### Step 5 — 保存与执行验证

1. 保存逻辑流。
2. 点击逻辑流编辑器**左上角执行图标**打开执行弹窗，
   输入参数后执行；可右键图元「设置断点」→ 左上角
   「开启调试」→ 执行，查看 rest 调用后的返回数据。
3. 验证以**返回值实际读出**为准，不以配置成功为准。
4. 外部调试方式（转述给用户）：每条逻辑流也是
   POST 类型接口 `/构件包编码.服务名.biz.ext`，
   可在 `swagger-ui.html?urls.primaryName=eosservice`
   查看，postman 调用需带 Authorization 请求凭证。
5. 排查调用问题：查 `logs/eos-dap-trace.log` 中
   `comp=REST_TEMPLATE` 日志行。

## 不变量

1. **作用域铁律**：只动当前打开的服务编排画布。
2. **删除红线**：任何「删除」按钮/图标/菜单项严禁点击。
3. **代码红线**：URL/请求头/请求体写入前先展示确认。
4. **行动后验证**：以执行返回值实际读出为准。
5. **失败即停**：拖拽两次失败转用户手动；连续失败即报告。

## Notes / gotchas

- **参数位置错配**：传参类型选错（如 Body 参数选成
  QUERY）是调用失败常见原因，配置时逐项核对接口文档。
- **URL 变量替换**：服务地址支持
  `${systemVars.编码}` 等写法，配置见
  `ynu-eos8-flow-env-vars`。
- **三方服务接口**：已导入三方服务的接口可从右侧
  三方服务树直接拖入画布，自动生成 rest 图元并
  自动填充 URL/Method/参数——见
  `ynu-eos8-flow-third-party`。
- **应用名 URL**：`http://应用名称:port/...` 依赖
  `spring.application.name`，跨环境部署时优先用变量替换。
- **画布拖拽**：元素面板→画布多为 HTML5 拖拽，
  程序化拖拽常失败，两次失败即请用户手动拖入。
- **ref 时效性**：画布/属性弹窗重渲染后旧 ref 失效，
  操作前重取快照。
- **CDP 超时（仅 WorkBuddy）**：点击前 focus + sleep 约 2 秒。
- **衔接**：三方服务 `ynu-eos8-flow-third-party`；
  环境变量 `ynu-eos8-flow-env-vars`；AI 服务图元
  `ynu-eos8-flow-ai-service`。
