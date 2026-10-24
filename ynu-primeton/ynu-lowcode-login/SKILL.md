---
name: ynu-lowcode-login
description: "打开并登录云南大学低代码开发平台（EOS8，dev-idm.ynu.edu.cn）。当用户要打开/进入云大低代码平台、低开平台、dev-idm、EOS8 设计器，或要进入某个低代码应用时使用。流程：导航到开发者中心 → 若停在统一身份认证登录页则请用户手动登录（工号+密码+图形验证码，或微信/企业微信/今日校园扫码）→ 等待进入平台 → 列出应用让用户选择（单应用也须确认）→ 直接导航到所选应用的 IDE。兼容两种浏览器运行时：WorkBuddy Browser（mcp__browser__* 工具）与 Trae（integrated_code_mode 的 Exec 内 browser_* 工具），启动时自动探测。可选参数 appName 可直接传入应用编码跳过选择步骤。"
agent_created: true
---
# 打开并登录云大低代码平台（WorkBuddy / Trae 双运行时兼容）

## Overview
打开云南大学信息技术中心的低代码开发平台（普元 EOS8，部署在 `dev-idm.ynu.edu.cn`），
完成统一身份认证登录，并进入指定应用的 IDE 设计器。
这是一个人机协作流程：本技能负责**打开浏览器、导航、检测登录页、等待、读取应用清单、
跳转到 IDE**；**登录这一步必须由用户手动完成**（工号+密码+图形验证码，或手机扫码），
技能不会、也不该替用户输入密码或保存凭证。

平台入口：
- 开发者中心（登录后落地页）：`https://dev-idm.ynu.edu.cn/#/dev_center/index`
- 应用 IDE（设计态）：`https://dev-idm.ynu.edu.cn/ide/index.html?appName=<应用编码>`
  （例：信息技术中心应用 → `appName=zxwyy`）

页面标题特征（用于状态判定）：
- 登录页：`统一身份认证平台`（重定向到 `ids.ynu.edu.cn/authserver/login`）
- 开发中心：`云大低开平台`
- 应用 IDE：`Primeton-IDE`

## When to use
- 用户说「打开云大低代码平台 / 低开平台 / dev-idm / EOS8」「登录低代码平台」「进一下低代码设计器」。
- 用户要在某个低代码应用（如「采购项目储备管理」）里做后续操作，但需要先进入其 IDE。
- 注意：该地址需要校园网或已在校内的网络环境才能访问（校外先连 WebVPN）。

## Step 0 — 运行时探测（必须最先执行）
检查当前环境可用的工具集，确定运行模式，后续所有步骤按对应绑定执行：
- 工具列表含 `mcp__browser__browsers_list` → **WorkBuddy 模式**
- 工具列表含 integrated_code_mode 的 `Exec`（浏览器工具在 Exec 内以 `await tools.browser_*` 调用）→ **Trae 模式**
- 两者都没有 → 提示用户启用对应浏览器扩展，终止流程。

两种模式的关键差异：
| 差异点 | WorkBuddy | Trae |
|---|---|---|
| 页面定位 | `browser_id` + 标签页 | `viewId`（标签视图 ID） |
| 调用方式 | 直接调用 `mcp__browser__*` | 浏览器工具必须在 Exec 内 `await tools.*` 调用，可多操作合并一次往返 |
| 等待手段 | 无条件等待工具，靠轮询 | `browser_wait_for`（可等文本/选择器出现，条件触发） |
| 移交用户 | 文字提示 + 轮询检测 | `browser_waiting_for_user_interaction`（**独立调用，不与其他工具并行**，可传 `viewId`） |

## 能力映射表
| 能力 | WorkBuddy 绑定 | Trae 绑定 |
|---|---|---|
| 新开标签 | `tabs_new(browser_id)` | `browser_navigate`（无打开标签时自动新建，无需显式 tabs_new） |
| 导航 | `tab_goto` | `browser_navigate`（从返回快照记录 `viewId`） |
| 读标题/URL/状态 | `tab_title` / `tab_url` | `browser_snapshot({compact})`（头部含 URL、标题） |
| 读页面结构 | `dom_cua_get_visible_dom` | `browser_snapshot`（可访问性树，带 `ref` 元素标识） |
| 点击元素 | `dom_cua_click` | `browser_click({ref})`（ref 来自快照） |
| 截图 | `tab_screenshot` | `browser_take_screenshot` |
| 等待条件 | 轮询 `tab_title`（每 ~5s） | `browser_wait_for({ text, timeout })` |
| 移交用户登录 | 文字提示 + 轮询 | `browser_waiting_for_user_interaction`（显式传 `viewId`） |
| 询问用户 | `AskUserQuestion` | `AskUserQuestion` |
| 页面 JS 提取 | `dom_cua_evaluate`（如有） | `browser_evaluate`（**只读**，禁止改 DOM） |

## 参数（可选）
技能可接收一个可选参数，直接指定要进入的应用编码，跳过「选择应用」步骤：
- `appName=xxx`：如 `appName=zxwyy`，则登录成功后直接导航到对应 IDE。
- 不传参数：登录成功后读取应用清单，**必须**用问答组件让用户选择（单应用也须确认，见不变量 3）。

## Workflow

### Step 1 — 导航到开发者中心
- **WorkBuddy**：`browsers_list` 取 `browser_id` → `tabs_new` → `tab_goto` 到 `https://dev-idm.ynu.edu.cn/#/dev_center/index` → 等约 2s。
- **Trae**：Exec 内 `browser_navigate`（无标签时自动新建）→ 从返回快照**记录 `viewId`** → `browser_wait_for({ time: 2 })`。
- 导航失败先提示用户确认校园网/WebVPN，不要直接判失败。

### Step 2 — 检测登录状态（三态判定）
读取标题与关键文本，判定当前处于哪一态：
| 状态 | 判定特征（满足任一） |
|---|---|
| 登录页 | 标题含「统一身份认证」；DOM 含「请输入学号/工号」「请输入验证码」 |
| 平台页（开发中心） | 标题为「云大低开平台」；DOM 含「搜索应用名称」「开发中心」 |
| IDE 页（已登录） | URL 含 `/ide/index.html?appName=`；标题为「Primeton-IDE」 |

- 判定为平台页或 IDE 页 → 已登录，跳到 Step 4（IDE 页则流程已完成，向用户确认即可）。
- 判定为登录页 → 进入 Step 3。

### Step 3 — 请用户手动登录，等待进入平台
1. 提示用户手动完成登录（账号+密码+图形验证码，或微信/企业微信/今日校园扫码），可截图登录页供参考。
   **绝不读取、缓存或代填密码/验证码。**
2. 等待方式（二选一，按运行时）：
   - **WorkBuddy**：每 ~5s 轮询 `tab_title`；标题变为「云大低开平台」即成功；累计超 **300s** 输出 `LOGIN_TIMEOUT`，提示刷新重试。
   - **Trae**：独立调用 `browser_waiting_for_user_interaction`（**必须显式传 `viewId` 锁定本流程标签页**，不传会跟随活动标签漂移——实测踩坑）。用户完成并交回控制权后，**第一件事**：重新快照并向用户播报「已检测到登录成功，当前在 X 页面」，再继续后续步骤。
3. 若二维码过期（长时间无变化），提示用户点登录页「刷新」或重新加载后继续等待。

### Step 4 — 确定要进入的应用（必经用户确认）
1. 读取开发中心页面，汇总应用卡片清单（卡片含「<应用名> 负责人：…」及表单/流程/数据集/服务统计）。
2. **无论清单里有几个应用，必须用 `AskUserQuestion` 让用户确认**——单应用也做轻量确认，禁止自动跳过（卡片可见 ≠ 应用全集，且进错应用代价高）。
3. 获取所选应用的**应用编码（appName）**，解析顺序：
   - 若收到 `appName` 参数 → 直接使用，跳到 Step 5；
   - **点击所选应用卡片一次，触发跳转后从 URL 读 `/ide/index.html?appName=xxx`**；
   - 兜底：已知映射表（见 Notes）。
   - ⚠️ 实测结论：开发中心的应用卡片**不是 `<a>` 链接，DOM 里没有 appName**——不要试图用选择器/JS 从开发中心 DOM 解析 `appName`，只会拿到「负责人：」之类的碎片文本。
4. 点击卡片若超时（WorkBuddy 下 `dispatchMouseEvent` 偶发超时），重试一次；仍失败请用户直接告知 appName。

### Step 5 — 导航到所选应用的 IDE
1. 直接导航到 `https://dev-idm.ynu.edu.cn/ide/index.html?appName=<应用编码>`。
2. ⚠️ 从开发中心进入应用会**开新标签页**（实测）：
   - WorkBuddy：点击卡片跳转后用 `tab_url` 确认落在哪个标签页，后续操作锁定该页；
   - Trae：导航后从返回快照确认当前 `viewId`，**后续所有 IDE 内操作显式带该 `viewId`**。
3. 等待 IDE 加载完成：优先条件等待（Trae：`browser_wait_for({ text: "资源信息加载完毕", timeout: 20 })`）；WorkBuddy 轮询 `tab_title` 变为 `Primeton-IDE`。
4. 用快照/标题验证已在 IDE 页，向用户播报「已进入 <应用名> 的 IDE」，流程结束。

### Step 6 — 保留会话
保持浏览器标签页打开，登录态可供后续操作复用。无需主动关闭。

## 不变量（两种运行时都必须遵守）
1. **不碰密码**：绝不读取、缓存或代填用户密码/验证码；登录完全由用户手动完成。
2. **交回即播报**：用户完成手动操作、控制权交回后，先快照确认并播报当前状态，再执行后续动作——让用户能看到流程续接。
3. **选择必确认**：应用选择必须经 `AskUserQuestion`，单应用也不例外。
4. **appName 来源受限**：只能来自用户参数、卡片点击后的 URL、已知映射表三者之一。
5. **行动后验证**：每次导航/点击后用快照（或标题/URL）确认结果再继续，便于当场发现漏发导航、页面未跳转等问题。
6. **Trae 特有**：浏览器工具一律在 Exec 内调用（可合并 3~8 个顺序操作减少往返）；`browser_waiting_for_user_interaction` 必须独立调用且显式传 `viewId`。

## Notes / gotchas
- **SSO 会话复用**：`dev-idm.ynu.edu.cn` 与学校其他系统共用 `ids.ynu.edu.cn` 的 CAS。
  若本轮已登录过任意 YNU 系统，再开低代码平台可能免登录直接进，属正常现象。
  需要重新走完整登录流程时，可先访问 `https://ids.ynu.edu.cn/authserver/logout` 注销（实测返回「注销成功」页）。
- **网络环境**：`dev-idm.ynu.edu.cn` 需校园网或 WebVPN，否则页面打不开——导航失败先提示用户确认网络。
- **应用编码已知映射**（备查，非硬编码依赖）：信息技术中心应用 → `zxwyy`。
  新增应用时以卡片点击后实际解析到的 `appName` 为准。
- **Trae 标签页行为**：`browser_navigate` 在无打开标签时会自动新建，无需显式 tabs_new；
  接管工具不传 `viewId` 会跟随「当前活动标签页」，多标签场景必须显式锁定。
