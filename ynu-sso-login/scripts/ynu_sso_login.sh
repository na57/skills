#!/usr/bin/env bash
# ynu_sso_login.sh — 登录云南大学（YNU）SSO 保护的管理后台（微信扫码）
#
# 原理：目标后台（minos / casp 融合门户 / ids 统一身份认证）底层都走
#       ids.ynu.edu.cn 的 CAS 统一身份认证。流程为：
#       打开目标 → 若停在本地登录页则点「统一身份认证登录」跳到 CAS
#       → CAS 页展示微信扫码二维码 → 用户扫码确认 → 自动跳回目标后台。
#
# 用法：
#   ynu_sso_login.sh <target>            # 全模式：打开+导航+截图二维码+轮询登录（一次性）
#   ynu_sso_login.sh <target> --qr-only  # 仅打开+导航到二维码页并截图，输出 QR 路径后退出
#   ynu_sso_login.sh <target> --wait     # 复用已打开的浏览器，仅轮询直到登录成功
#
# target 取值：
#   minos | casp | portal | 融合门户  → https://casp.ynu.edu.cn 或 https://minos.ynu.edu.cn
#   ids | auth | 统一身份认证         → https://ids.ynu.edu.cn
#   其他                               → 当作完整 URL 或 https://<target> 直接打开
#
# 环境变量：
#   YNU_QR_PATH   二维码截图保存路径（默认 /tmp/ynu_sso_qr.png）
#   YNU_POLL_SECS 轮询总时长上限，秒（默认 180）

set -uo pipefail

TARGET="${1:-minos}"
MODE="full"
[[ "${2:-}" == "--qr-only" ]] && MODE="qr"
[[ "${2:-}" == "--wait" ]] && MODE="wait"

QR_PATH="${YNU_QR_PATH:-/tmp/ynu_sso_qr.png}"
POLL_SECS="${YNU_POLL_SECS:-180}"

# 别名 → 真实入口 URL
case "$TARGET" in
  minos)                 URL="https://minos.ynu.edu.cn" ;;
  casp|portal|融合门户)   URL="https://casp.ynu.edu.cn" ;;
  ids|auth|统一身份认证)  URL="https://ids.ynu.edu.cn" ;;
  http://*|https://*)    URL="$TARGET" ;;
  *)                     URL="https://$TARGET" ;;
esac

ab() { agent-browser "$@"; }

open_and_navigate() {
  ab open "$URL"
  ab wait --load networkidle 2>/dev/null || true
  # 停在本地登录页时（minos 有「统一身份认证登录」入口），点它跳到 CAS
  local has
  has="$(ab eval "document.querySelector('.login-bottom-text') ? 'yes' : 'no'" 2>/dev/null || echo no)"
  if [[ "$has" == "yes" ]]; then
    ab eval "document.querySelector('.login-bottom-text').click()" 2>/dev/null \
      || ab click ".login-bottom-text"
    ab wait --load networkidle 2>/dev/null || true
  fi
  # 若页面有多个扫码方式 tab，确保选中「微信」（按文本点击；找不到则忽略）
  ab eval "(function(){var t=[...document.querySelectorAll('*')].find(e=>e.children.length===0&&e.textContent.trim()==='微信');if(t)t.click();})()" 2>/dev/null || true
  ab wait --load networkidle 2>/dev/null || true
}

screenshot_qr() {
  ab screenshot "$QR_PATH"
  echo "QR_READY:$QR_PATH"
}

poll_login() {
  local waited=0
  while (( waited < POLL_SECS )); do
    local url
    url="$(ab get url 2>/dev/null || true)"
    case "$url" in
      *ids.ynu.edu.cn*) ;;   # 仍在 CAS 登录页 → 继续等
      *) echo "LOGIN_OK:$url"; return 0 ;;
    esac
    sleep 4
    (( waited += 4 ))
  done
  echo "LOGIN_TIMEOUT: still on $url"
  return 1
}

case "$MODE" in
  qr)   open_and_navigate; screenshot_qr ;;
  wait) poll_login ;;
  full) open_and_navigate; screenshot_qr; poll_login ;;
esac
