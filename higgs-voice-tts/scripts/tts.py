#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Higgs 音色克隆 TTS —— 用固定音色样本把文本转成 mp3。

核心事实（踩过的坑，别再试错）：
  1. Higgs（bosonai/higgs-audio-v3-tts-4b）的 voice 参数只有 "default" 有效，
     不给参考音频时**每句话音色都随机**，整批音频会出现好几个人在说话。
  2. 网关认的参数名就是 ref_audio / ref_text。写成 reference_audio、
     speaker_audio 之类**不会报错**，会静默忽略并返回 200，你以为克隆了其实没有。
  3. ref_audio 必须是 **data URI**（data:audio/mpeg;base64,xxx）。
     传裸 base64 或本地文件路径都会 400。

用法：
    python3 tts.py "一句话" -o out.mp3                 # 单句
    python3 tts.py --batch script.json -d audio/        # 批量
    python3 tts.py --text-file 讲稿.txt -o 讲稿.mp3      # 整篇
    python3 tts.py --selftest                           # 冒烟：生成一句并报时长
    python3 tts.py --probe                              # 只打印当前配置

批量 JSON 格式（二选一）：
    [{"id": "s1", "text": "……"}, {"id": "s2", "text": "……"}]
    {"items": [{"id": "s1", "text": "……"}]}
输出文件名取 id（无 id 则按顺序 0001、0002…），另写一份 timing.json 记录时长。

音色样本：默认用本技能自带的 assets/3-higgs-平台听力训练在用.mp3（云南大学信息
技术中心「听力训练」应用在用的那把男声）。换样本用 --ref-audio，并**务必**同步
给 --ref-text（样本内容的原文），克隆质量高度依赖它。

环境：
    YNU_NEW_API_KEY       必填，Higgs TTS 网关密钥（已在本机 ~/.zshrc 配置）
    YNU_NEW_API_ENDPOINT  覆盖内置网关地址（可选）
"""
from __future__ import annotations  # 兼容 Python 3.9 的 `str | None` 写法

import argparse
import base64
import json
import os
import shutil
import struct
import subprocess
import sys
import time
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(HERE)

API_KEY = os.environ.get("YNU_NEW_API_KEY")
if not API_KEY:
    raise SystemExit(
        "请先设置环境变量 YNU_NEW_API_KEY（本机已写入 ~/.zshrc）"
    )
ENDPOINT = os.environ.get("YNU_NEW_API_ENDPOINT") or "https://new-api-itc.ynu.edu.cn/v1/audio/speech"

DEFAULT_MODEL = "bosonai/higgs-audio-v3-tts-4b"
DEFAULT_VOICE = "default"
DEFAULT_REF_AUDIO = os.path.join(SKILL_DIR, "assets", "3-higgs-平台听力训练在用.mp3")
# 样本音频的原文。换样本时必须改，否则克隆会跑偏。
DEFAULT_REF_TEXT = (
    "云南大学信息技术中心依托自主研发的三A平台，建成校园网IT资产全息图谱，"
    "覆盖全校215个信息系统、7228项资产。"
)

FFPROBE_CANDIDATES = [
    os.environ.get("FFPROBE"),
    "/Users/na57/.workbuddy/binaries/ffmpeg/ffprobe",
    shutil.which("ffprobe"),
]

# MP3 码率表（MPEG1 Layer3 / MPEG2 Layer3），用于没有 ffprobe 时估算时长
_MP3_BITRATES = {
    (1, 3): [0, 32, 40, 48, 56, 64, 80, 96, 112, 128, 160, 192, 224, 256, 320, 0],
    (2, 3): [0, 8, 16, 24, 32, 40, 48, 56, 64, 80, 96, 112, 128, 144, 160, 0],
}
_MP3_RATES = {1: [44100, 48000, 32000], 2: [22050, 24000, 16000]}


# --------------------------------------------------------------------------- 时长
def _mp3_duration_fallback(path: str) -> float | None:
    """纯 Python 解析 mp3 时长：优先 Xing/VBRI 帧数，退回 CBR 位速估算。"""
    with open(path, "rb") as f:
        data = f.read()
    if len(data) < 4:
        return None
    pos = 0
    if data[:3] == b"ID3":  # 跳过 ID3v2
        size = ((data[6] & 0x7F) << 21) | ((data[7] & 0x7F) << 14) \
            | ((data[8] & 0x7F) << 7) | (data[9] & 0x7F)
        pos = 10 + size
    # 找第一个帧同步
    start = None
    while pos < len(data) - 4:
        if data[pos] == 0xFF and (data[pos + 1] & 0xE0) == 0xE0:
            start = pos
            break
        pos += 1
    if start is None:
        return None
    b1, b2 = data[start + 1], data[start + 2]
    ver_id = (b1 >> 3) & 0x03          # 3=MPEG1, 2=MPEG2, 0=MPEG2.5
    layer = (b1 >> 1) & 0x03           # 3=Layer I, 1=Layer III
    if layer != 1:
        return None
    version = 1 if ver_id == 3 else 2
    bitrate = _MP3_BITRATES.get((version, 3), [0] * 16)[(b2 >> 4) & 0x0F]
    sample_rate = _MP3_RATES.get(version, [0, 0, 0])[(b2 >> 2) & 0x03]
    if not bitrate or not sample_rate:
        return None
    frame_len = int(144 * bitrate * 1000 / sample_rate) + ((b2 >> 1) & 0x01)
    # Xing / VBRI：直接给总帧数
    off = start + 4 + (32 if version == 1 else 17)  # side info 之后
    tag = data[off:off + 4]
    if tag in (b"Xing", b"Info"):
        flags = struct.unpack(">I", data[off + 4:off + 8])[0]
        if flags & 0x01:
            frames = struct.unpack(">I", data[off + 8:off + 12])[0]
            return round(frames * 1152 / sample_rate, 3)
    if data[start + 36:start + 40] == b"VBRI":
        frames = struct.unpack(">I", data[start + 46:start + 50])[0]
        return round(frames * 1152 / sample_rate, 3)
    return round((len(data) - start) * 8 / (bitrate * 1000.0), 3)  # CBR 估算


def duration(path: str) -> float:
    for cand in FFPROBE_CANDIDATES:
        if cand and os.path.exists(cand):
            out = subprocess.run(
                [cand, "-v", "error", "-show_entries", "format=duration",
                 "-of", "default=nw=1:nk=1", path],
                capture_output=True, text=True,
            )
            if out.returncode == 0 and out.stdout.strip():
                try:
                    return round(float(out.stdout.strip()), 3)
                except ValueError:
                    pass
            break
    est = _mp3_duration_fallback(path)
    if est is None:
        raise RuntimeError(f"无法探测时长（本机无 ffprobe）：{path}")
    return est


# --------------------------------------------------------------------------- TTS
def tts(text: str, out_path: str, model: str = DEFAULT_MODEL, voice: str = DEFAULT_VOICE,
        ref_audio: str | None = DEFAULT_REF_AUDIO, ref_text: str | None = DEFAULT_REF_TEXT,
        retries: int = 3, timeout: int = 300, quiet: bool = False) -> bool:
    """合成一句。ref_audio 传 None / 空串 = 不克隆（音色会随机，一般别这么干）。"""
    body = {"model": model, "input": text, "voice": voice, "response_format": "mp3"}
    if ref_audio:
        if not os.path.exists(ref_audio):
            raise FileNotFoundError(f"音色样本不存在：{ref_audio}")
        with open(ref_audio, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        body["ref_audio"] = "data:audio/mpeg;base64," + b64
        if ref_text:
            body["ref_text"] = ref_text
    payload = json.dumps(body, ensure_ascii=False).encode("utf-8")

    last = ""
    for attempt in range(retries):
        try:
            req = urllib.request.Request(
                ENDPOINT, data=payload,
                headers={"Authorization": f"Bearer {API_KEY}",
                         "Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                raw = resp.read()
            if not raw:
                raise RuntimeError("网关返回空响应")
            os.makedirs(os.path.dirname(os.path.abspath(out_path)) or ".", exist_ok=True)
            with open(out_path, "wb") as f:
                f.write(raw)
            return True
        except Exception as exc:  # noqa: BLE001
            last = f"{type(exc).__name__}: {exc}" if not isinstance(exc, urllib.error.HTTPError) else f"HTTP {exc.code} {exc.reason}"
            if isinstance(exc, urllib.error.HTTPError):
                try:
                    last += " " + exc.read().decode("utf-8", "ignore")[:300]
                except Exception:  # noqa: BLE001
                    pass
            if not quiet:
                print(f"    重试 {attempt + 1}/{retries}：{last}")
            if attempt < retries - 1:
                time.sleep(2 * (attempt + 1))
    if not quiet:
        print(f"    ✗ 失败：{last}")
    return False


# --------------------------------------------------------------------------- CLI
def load_batch(path: str) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict):
        data = data.get("items") or data.get("beats") or []
    out = []
    for i, item in enumerate(data, 1):
        if isinstance(item, str):
            out.append({"id": f"{i:04d}", "text": item})
        else:
            out.append({"id": item.get("id") or f"{i:04d}", "text": item["text"],
                        "label": item.get("label", "")})
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description="Higgs 音色克隆 TTS")
    ap.add_argument("text", nargs="?", help="要合成的文本")
    ap.add_argument("-o", "--out", help="输出 mp3 路径")
    ap.add_argument("-d", "--out-dir", help="批量输出目录")
    ap.add_argument("--batch", help="批量 JSON 文件路径")
    ap.add_argument("--text-file", help="从文本文件读取（utf-8）")
    ap.add_argument("--voice", default=DEFAULT_VOICE)
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--ref-audio", default=DEFAULT_REF_AUDIO,
                    help=f"音色样本（默认 {DEFAULT_REF_AUDIO}）")
    ap.add_argument("--ref-text", default=DEFAULT_REF_TEXT, help="样本音频的原文")
    ap.add_argument("--no-ref", action="store_true", help="不克隆（音色会随机，慎用）")
    ap.add_argument("--force", action="store_true", help="已存在也重新生成")
    ap.add_argument("--timing", help="批量时把时长表写到该路径")
    ap.add_argument("--selftest", action="store_true", help="生成一句示例音频做冒烟测试")
    ap.add_argument("--probe", action="store_true", help="打印配置后退出")
    ap.add_argument("-q", "--quiet", action="store_true")
    args = ap.parse_args()

    ref_audio = None if args.no_ref else args.ref_audio
    ref_text = None if args.no_ref else args.ref_text

    if args.probe:
        print(f"endpoint : {ENDPOINT}")
        print(f"model    : {args.model}")
        print(f"voice    : {args.voice}")
        if ref_audio:
            kb = os.path.getsize(ref_audio) // 1024 if os.path.exists(ref_audio) else -1
            print(f"ref_audio: {ref_audio} ({kb} KB)")
            print(f"ref_text : {ref_text[:40]}…" if ref_text and len(ref_text) > 40 else f"ref_text : {ref_text}")
        else:
            print("ref_audio: （关闭）警告：Higgs 音色将随机")
        print(f"ffprobe  : {next((c for c in FFPROBE_CANDIDATES if c and os.path.exists(c)), '无，走纯 Python 估算')}")
        return

    if args.selftest:
        out = args.out or os.path.join("/tmp", "higgs_selftest.mp3")
        ok = tts("音色克隆自检，这一句用于确认参考音频生效。", out,
                 args.model, args.voice, ref_audio, ref_text, quiet=args.quiet)
        if not ok:
            sys.exit("自检失败")
        print(f"自检通过：{out}  {duration(out):.2f}s  "
              f"{os.path.getsize(out) // 1024} KB")
        return

    if args.batch:
        items = load_batch(args.batch)
        out_dir = args.out_dir or os.path.join(os.path.dirname(os.path.abspath(args.batch)), "audio")
        os.makedirs(out_dir, exist_ok=True)
        timing, total = [], 0.0
        for item in items:
            dst = os.path.join(out_dir, f"{item['id']}.mp3")
            if args.force or not os.path.exists(dst):
                if not args.quiet:
                    print(f"  → {item['id']}  {item.get('label', '')}")
                if not tts(item["text"], dst, args.model, args.voice,
                           ref_audio, ref_text, quiet=args.quiet):
                    sys.exit(f"失败：{item['id']}")
            d = duration(dst)
            total += d
            timing.append({"id": item["id"], "label": item.get("label", ""), "dur": d})
            if not args.quiet:
                print(f"  ✓ {item['id']}  {d:6.2f}s")
        tpath = args.timing or os.path.join(os.path.dirname(out_dir), "timing.json")
        with open(tpath, "w", encoding="utf-8") as f:
            json.dump({"generatedAt": time.strftime("%Y-%m-%d %H:%M:%S"),
                       "model": args.model, "voice": args.voice,
                       "refAudio": ref_audio, "total_s": round(total, 3),
                       "items": timing}, f, ensure_ascii=False, indent=2)
        print(f"共 {len(items)} 条 / {total:.1f}s = {total / 60:.2f} 分钟 → {out_dir}")
        print(f"时长表 → {tpath}")
        return

    text = args.text
    if args.text_file:
        with open(args.text_file, encoding="utf-8") as f:
            text = f.read()
    if not text:
        ap.error("缺少文本：给位置参数、--text-file 或 --batch")
    text = " ".join(text.split())
    if len(text) > 800 and not args.quiet:
        print(f"提示：文本 {len(text)} 字偏长，建议按句号拆成多条批量生成（长句易截断或音质下降）")
    out = args.out or "tts_output.mp3"
    if not tts(text, out, args.model, args.voice, ref_audio, ref_text, quiet=args.quiet):
        sys.exit("合成失败")
    print(f"✓ {out}  {duration(out):.2f}s  {os.path.getsize(out) // 1024} KB")


if __name__ == "__main__":
    main()
