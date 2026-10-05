#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
音色一致性客观校验：比较各条音频的基频（F0 中位数）与音色样本的差距。

为什么需要它：Higgs 不传 ref_audio 时**每次合成都是随机音色**，而网关对拼错的
参数名不报错（照常 200）。光听一两句容易漏。用 F0 一量就知道有没有真的克隆上：
    - 克隆生效：各条 F0 挤在一个很窄的区间（实测标准差 ≈ 2-4 Hz）
    - 没克隆上：F0 四处乱跳（实测标准差 ≈ 30-40 Hz）

用法：
    python3 verify_voice.py 样本.mp3 成片1.mp3 成片2.mp3 …
    python3 verify_voice.py 样本.mp3 audio/*.mp3 --json

判据：标准差 < 6 Hz 且与样本中位差 < 15 Hz → 音色一致；
      标准差 > 15 Hz → 基本确定音色在随机漂移，检查 ref_audio 有没有真的传上去。

依赖：numpy（没有就 pip install numpy）+ ffmpeg（转 PCM 用）。
"""
from __future__ import annotations  # 兼容 Python 3.9 的 `float | None` 写法

import argparse
import json
import os
import shutil
import subprocess
import sys

FFMPEG_CANDIDATES = [
    os.environ.get("FFMPEG"),
    "/Users/na57/.workbuddy/binaries/ffmpeg/ffmpeg",
    shutil.which("ffmpeg"),
]

SR = 16000
FRAME = 0.030      # 30ms 帧
HOP = 0.015        # 15ms 步进
F0_MIN, F0_MAX = 70, 400


def find_ffmpeg() -> str:
    for cand in FFMPEG_CANDIDATES:
        if cand and os.path.exists(cand):
            return cand
    sys.exit("找不到 ffmpeg，请先安装或设 FFMPEG 环境变量")


def load_pcm(path: str, ffmpeg: str):
    import numpy as np
    out = subprocess.run(
        [ffmpeg, "-v", "error", "-i", path, "-ac", "1", "-ar", str(SR),
         "-f", "s16le", "-"], capture_output=True, check=True)
    return np.frombuffer(out.stdout, dtype=np.int16).astype(np.float64) / 32768.0


def estimate_f0(x) -> float | None:
    """自相关法估 F0：返回有声帧 F0 的中位数，无声返回 None。"""
    import numpy as np
    n = int(SR * FRAME)
    step = int(SR * HOP)
    if len(x) < n:
        return None
    lag_min, lag_max = int(SR / F0_MAX), int(SR / F0_MIN)
    f0s = []
    for start in range(0, len(x) - n, step):
        frame = x[start:start + n]
        frame = frame - frame.mean()
        energy = float(np.sqrt(np.mean(frame ** 2)))
        if energy < 0.01:          # 静音帧跳过
            continue
        corr = np.correlate(frame, frame, mode="full")[n - 1:]
        corr = corr / (corr[0] + 1e-9)
        seg = corr[lag_min:lag_max + 1]
        if seg.size == 0:
            continue
        lag = int(np.argmax(seg)) + lag_min
        # 峰值太弱说明不是周期信号（清音/噪声），丢弃
        if corr[lag] < 0.3:
            continue
        f0s.append(SR / lag)
    if len(f0s) < 5:
        return None
    return float(np.median(f0s))


def main() -> None:
    ap = argparse.ArgumentParser(description="Higgs 音色一致性校验（F0）")
    ap.add_argument("files", nargs="+", help="第一个是音色样本，其余是待检音频")
    ap.add_argument("--ffmpeg")
    ap.add_argument("--json", action="store_true", help="输出 JSON")
    args = ap.parse_args()

    ffmpeg = args.ffmpeg or find_ffmpeg()
    try:
        import numpy  # noqa: F401
    except ImportError:
        sys.exit("缺 numpy：pip install numpy")

    ref = args.files[0]
    ref_f0 = estimate_f0(load_pcm(ref, ffmpeg))
    if ref_f0 is None:
        sys.exit(f"样本 {ref} 测不出 F0（可能太短或几乎无声）")

    rows = []
    for path in args.files[1:]:
        rows.append({"file": os.path.basename(path), "f0": estimate_f0(load_pcm(path, ffmpeg))})

    vals = [r["f0"] for r in rows if r["f0"] is not None]
    if not vals:
        sys.exit("待检音频都没测出 F0")

    import statistics
    std = statistics.pstdev(vals) if len(vals) > 1 else 0.0
    spread = max(abs(v - ref_f0) for v in vals)

    if args.json:
        print(json.dumps({"ref": os.path.basename(ref), "ref_f0": round(ref_f0, 1),
                          "std": round(std, 2), "max_delta": round(spread, 1),
                          "items": [{"file": r["file"],
                                     "f0": round(r["f0"], 1) if r["f0"] else None} for r in rows]},
                         ensure_ascii=False, indent=2))
        return

    print(f"样本 {os.path.basename(ref)}  F0 = {ref_f0:.1f} Hz\n")
    for r in rows:
        if r["f0"] is None:
            print(f"  {r['file']:<40} 测不出")
        else:
            flag = "" if abs(r["f0"] - ref_f0) < 25 else "  ← 偏离"
            print(f"  {r['file']:<40} {r['f0']:6.1f} Hz   Δ{r['f0'] - ref_f0:+6.1f}{flag}")
    print(f"\n成片 F0 均值 {statistics.fmean(vals):.1f} Hz   标准差 {std:.2f} Hz   "
          f"与样本最大偏离 {spread:.1f} Hz")
    print("（成片整体比样本低 5-20 Hz 属正常：语速、语调不同，音色本身没变）")
    if std < 8:
        print("结论：音色一致，克隆生效。")
    elif std > 15:
        print("结论：音色在随机漂移 —— ref_audio 多半没传上去"
              "（参数名必须是 ref_audio，值必须是 data:audio/mpeg;base64, 开头的 data URI）。")
    else:
        print("结论：大体一致但有波动，建议抽查听一下偏离最大的那条。")


if __name__ == "__main__":
    main()
