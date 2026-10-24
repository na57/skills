---
name: ynu-lowcode-login
description: "打开并登录云南大学低代码开发平台（EOS8，dev-idm.ynu.edu.cn）。当用户要打开/进入云大低代码平台、低开平台、dev-idm、EOS8 设计器，或要进入某个低代码应用时使用。流程：导航到开发者中心 → 若停在统一身份认证登录页则请用户手动登录（工号+密码+图形验证码，或微信/企业微信/今日校园扫码）→ 轮询等待进入平台 → 列出应用让用户选择 → 直接导航到所选应用的 IDE。使用 WorkBuddy Browser（mcp__browser__* 工具）操作。可选参数可直接传入应用编码 appName 跳过选择步骤。"
agent_created: true
---

# 打开并登录云大低代码平台

## Overview

打开云南大学信息技术中心的低代码开发平台（普元 EOS8，部署在 `dev-idm.ynu.edu.cn`），
完成统一身份认证登录，并进入指定应用的 IDE 设计器。

这是一个人机协作流程：本技能负责**打开浏览器、导航、检测登录页、轮询等待、读取应用清单、
直接跳转到 IDE**；**登录这一步必须由用户手动完成**（工号+密码+图形验证码，或手机扫码），
技能不会、也不该替用户输入密码或保存凭证。

平台入口：
- 开发者中心（登录后落地页）：`https://dev-idm.ynu.edu.cn/#/dev_center/index`
- 应用 IDE（设计态）：`https://dev-idm.ynu.edu.cn/ide/index.html?appName=<应用编码>`
  （例：信息技术中心应用 → `appName=zxwyy`）

## When to use

- 用户说「打开云大低代码平台 / 低开平台 / dev-idm / EOS8」「登录低代码平台」「进一下低代码设计器」。
- 用户要在某个低代码应用（如「采购项目储备管理」）里做后续操作，但需要先进入其 IDE。
- 注意：该地址需要在校园网或已在校内的网络环境才能访问（校外先连 WebVPN）。

## Prerequisites

- 已安装并启用 **WorkBuddy 浏览器扩展**（设置 > 智能体 > 浏览器操控）。
- 浏览器会话中的登录态（cookie）会被保留——若本轮已登录过低代码平台或同套 CAS，
  再次打开可能免登录直接进平台，属正常现象。

## 参数（可选）

技能可接收一个可选参数，直接指定要进入的应用编码，跳过「选择应用」步骤：

- `appName=xxx`：如 `appName=zxwyy`，则登录成功后直接导航到对应 IDE。
- 不传参数：登录成功后读取应用清单，用问答组件让用户选择。

## Workflow

### Step 1 — 打开浏览器并导航到开发者中心

1. `mcp__browser__browsers_list` 获取可用浏览器（取 `browser_id`，通常 WorkBuddy Browser = 1）。
2. `mcp__browser__browser_info`（传 `browser_id`）确认能力，应为 `multi_tab` 模式。
3. `mcp__browser__tabs_new`（传 `browser_id`）新开标签页。
4. `mcp__browser__tab_goto` 导航到 `https://dev-idm.ynu.edu.cn/#/dev_center/index`。
5. 稍等页面加载（约 2 秒），进入状态检测。

### Step 2 — 检测登录状态

读取当前页面，判断处于「登录页」还是「平台页」：

- 用 `mcp__browser__tab_title` 读标题，**或** `mcp__browser__dom_cua_get_visible_dom` 读可见 DOM。
- **判定为登录页**（需手动登录）满足任一：
  - 标题含「统一身份认证」；
  - DOM 含「请输入学号/工号」「请输入密码」「请输入验证码」「账号登录」等字样。
- **判定为平台页**（已登录，可直接进 Step 3）满足任一：
  - 标题含「云大低开平台」或「开发中心」；
  - DOM 含「搜索应用名称」（应用搜索框占位符）。

### Step 3 — 若停在登录页：请用户手动登录并轮询等待

1. 提示用户在浏览器中**手动完成登录**，说明支持两种方式任选其一：
   - 账号登录：输入工号 + 密码 + 图形验证码，点「登录」；
   - 扫码登录：微信 / 企业微信 / 今日校园 APP 扫码确认。
   （可用 `mcp__browser__tab_screenshot` 截一张登录页给用户参考。）
2. **轮询等待进入平台**（不阻塞、不代输密码）：
   - 每 ~5 秒用 `mcp__browser__tab_title` 检查一次；
   - 一旦标题变为「云大低开平台」/「开发中心」或 DOM 出现「搜索应用名称」，即视为登录成功，跳出轮询；
   - 累计超过 **300 秒（5 分钟）** 仍是登录页 → 输出 `LOGIN_TIMEOUT`，提示用户刷新页面重试或检查网络，结束流程。
3. 若二维码/页面过期（长时间无变化），提示用户点登录页的「刷新」或让本技能 `mcp__browser__tab_reload` 后重新等待。

> 已登录场景：若 Step 2 直接判定为平台页，跳过本步。

### Step 4 — 读取应用清单，确定要进入的应用

1. `mcp__browser__dom_cua_get_visible_dom` 读取开发中心页面，找出所有应用卡片
   （DOM 中形如「<应用名> 负责人：…」的卡片，配合「搜索应用名称」搜索框、「全部/运行中/已停止/其他」筛选按钮）。
2. 汇总应用名称清单：
   - **若收到 `appName` 参数**：直接用该编码，跳到 Step 5。
   - **否则**：用 `AskUserQuestion` 向用户展示应用清单，让用户选择要进入的应用。
3. 取得所选应用的**应用编码（appName）**：
   - 优先：从开发中心页面 / 应用卡片链接中解析出 `?appName=xxx`（部分页面卡片或详情带有该参数）；
   - 兜底：点击所选应用卡片一次（`mcp__browser__dom_cua_click`）触发跳转，再从 `mcp__browser__tab_url`
     返回的 `/ide/index.html?appName=xxx` 中解析出 `xxx`。若点击超时，重试一次；仍失败则请用户直接告知 appName。

### Step 5 — 直接导航到所选应用的 IDE

1. `mcp__browser__tab_goto` 导航到
   `https://dev-idm.ynu.edu.cn/ide/index.html?appName=<应用编码>`。
2. 用 `mcp__browser__dom_cua_get_visible_dom` 或 `mcp__browser__tab_title` 验证已停在 IDE 页面
   （地址栏含 `/ide/index.html`，标题应为应用设计器）。
3. 告知用户「已进入 <应用名> 的 IDE」，流程结束。

### Step 6 — 保留会话

保持浏览器标签页打开，登录态可供后续操作复用。无需主动关闭。

## Notes / gotchas

- **SSO 会话复用**：`dev-idm.ynu.edu.cn` 与学校其他系统共用 `ids.ynu.edu.cn` 的 CAS。
  若本轮已登录过任意 YNU 系统，再开低代码平台可能免登录直接进，属正常现象。
- **不碰密码**：本技能绝不读取、缓存或代填用户密码 / 验证码；登录完全由用户手动完成。
  图形验证码无法自动识别，这也是默认走「用户手动登录」的原因。
- **网络环境**：`dev-idm.ynu.edu.cn` 需校园网或 WebVPN，否则页面打不开——若 Step 1 导航失败，
  先提示用户确认网络。
- **点击卡片偶发超时**：开发中心点击应用卡片时 `dispatchMouseEvent` 偶发超时，属页面瞬时卡顿，
  非流程错误；Step 4 已用「直接解析 appName + 直接导航」规避，不必依赖卡片点击成功。
- **应用编码已知映射**（备查，非硬编码依赖）：信息技术中心应用 → `zxwyy`。
  新增应用时以页面实际解析到的 `appName` 为准。
