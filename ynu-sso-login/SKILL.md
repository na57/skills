---
name: ynu-sso-login
description: "Log into Yunnan University (云南大学) SSO-protected admin backends — minos (CASP 管控台), 融合门户/casp, 统一身份认证/ids — through the unified identity authentication (ids.ynu.edu.cn CAS) WeChat scan-code flow. Use this skill whenever the user asks to open or log into any YNU internal admin console (minos.ynu.edu.cn, casp.ynu.edu.cn, ids.ynu.edu.cn) and complete the WeChat QR-code login. The skill accepts a service alias (minos, casp, portal, ids, auth) or a full URL as its argument."
agent_created: true
---

# YNU SSO 登录（微信扫码）

## Overview

登录云南大学统一身份认证（CAS）保护的后台管理系统。所有目标（minos 管控台、融合门户 casp、
统一身份认证 ids）底层共用同一套 `ids.ynu.edu.cn` 的 CAS，登录流程完全一致：打开目标 → 跳到
统一认证页 → 展示微信扫码二维码 → 用户扫码确认 → 自动跳回目标后台。

本 skill 不能自动「替用户扫码」（二维码必须由用户手机扫），因此流程是**人机协作**：脚本负责
打开/导航/截图二维码/轮询，AI 负责把二维码展示给用户并等待扫码结果。

## When to use

- 用户说「登录 minos / 融合门户 / casp / 统一身份认证 / ids」「打开某某后台并登录」。
- 用户在 YNU 内部管理系统要做后续操作，但需要先完成登录。
- 注意：这些系统都需要校园网或已在校内的网络环境才能访问。

## Prerequisites

- 本机已安装 `agent-browser`：`npm install -g agent-browser && agent-browser install`。
- 浏览器 daemon 由 `agent-browser` 自动拉起；同一会话内 cookie / 登录态会保留。
- 用户手机装有**微信**（或企业微信 / 今日校园 APP，按需切换 tab）。

## Targets（服务别名 → 入口）

| 别名 | 入口 URL |
|------|----------|
| `minos` | https://minos.ynu.edu.cn |
| `casp` / `portal` / `融合门户` | https://casp.ynu.edu.cn |
| `ids` / `auth` / `统一身份认证` | https://ids.ynu.edu.cn |

也可以直接传完整 URL（如 `https://minos.ynu.edu.cn/router/index`）。

## Workflow

### Step 1 — 打开并导航到二维码页

运行 helper 脚本（仅导航 + 截图二维码，不阻塞等待）：

```bash
bash ~/.workbuddy/skills/ynu-sso-login/scripts/ynu_sso_login.sh <target> --qr-only
```

脚本会：
1. `agent-browser open <URL>`；
2. 若停在本地登录页（minos 有「统一身份认证登录」入口 `.login-bottom-text`），点击它跳到
   `ids.ynu.edu.cn/authserver/login?service=...`；
3. 确保页面停在 CAS 扫码页（标题「请使用微信、企业微信 或今日校园APP扫码登录」），并尽量选中
   「微信」tab；
4. 截图二维码到 `$YNU_QR_PATH`（默认 `/tmp/ynu_sso_qr.png`），输出 `QR_READY:<path>`。

若不用脚本，等价手动命令：

```bash
agent-browser open https://<target>
agent-browser wait --load networkidle
# 若当前页有 .login-bottom-text，则：
agent-browser click ".login-bottom-text"
agent-browser wait --load networkidle
agent-browser screenshot /tmp/ynu_sso_qr.png
```

### Step 2 — 把二维码展示给用户并请其扫码

用 `present_files` 展示 Step 1 输出的二维码截图，并提示用户：**用微信扫码，在手机上点「确认登录」**。
若页面默认不是微信二维码（显示的是企业微信/今日校园），先点「微信」tab 再截一次图。

### Step 3 — 轮询登录结果

```bash
bash ~/.workbuddy/skills/ynu-sso-login/scripts/ynu_sso_login.sh <target> --wait
```

脚本每 4 秒检查一次当前 URL：一旦离开 `ids.ynu.edu.cn` 即视为登录成功，输出 `LOGIN_OK:<最终URL>`；
超过 `YNU_POLL_SECS`（默认 180 秒）仍在 CAS 页则输出 `LOGIN_TIMEOUT`。

等价手动轮询：

```bash
for i in $(seq 1 45); do
  url=$(agent-browser get url 2>/dev/null)
  case "$url" in *ids.ynu.edu.cn*) sleep 4;; *) echo "LOGIN_OK:$url"; break;; esac
done
```

### Step 4 — 处理二维码过期

二维码通常约 2 分钟失效。若 `LOGIN_TIMEOUT`：

1. `agent-browser reload` 刷新页面（换新二维码）；
2. 重新 `screenshot` 并再次 `present_files` 展示；
3. 重新 `--wait` 轮询。

从 Step 2 循环即可，无需关闭浏览器。

### Step 5 — 确认并保留会话

登录成功后 `get url` 应回到目标后台（如 `https://minos.ynu.edu.cn/router/index`）。
**保持浏览器 daemon 打开**，登录态可用于后续操作。任务全部完成时再 `agent-browser close`。

## Notes / gotchas

- **SSO 会话复用**：若本轮已登录过某个 YNU 系统，再开其他 YNU 后台可能免扫码直接跳回（CAS
  ticket 仍有效）。此时 `--wait` 会立刻返回 `LOGIN_OK`，属于正常现象。
- **minos 本地登录页有验证码**：账号密码 + 图片验证码无法自动识别，所以统一改走「统一身份认证
  登录」→ 微信扫码路线，这也是本 skill 的默认路径。
- **`.login-bottom-text` 是 div 不是 a**：早期直接 `click "统一身份认证登录"` 文本选择器会失败，
  必须按 CSS 类 `.login-bottom-text` 点或 `eval` 触发，脚本已处理。
- **网络环境**：校外需先连校园网 / WebVPN，否则 `ids.ynu.edu.cn` 打不开。
