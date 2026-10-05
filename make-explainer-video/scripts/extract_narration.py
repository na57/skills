#!/usr/bin/env python3
"""从课件 HTML 提取 data-narration → script.json（TTS 批量）+ meta.json（组装用）。
推导互动页在「你推出来了吗？」处拆成 a/b 两段，中间由组装脚本插入静音停顿。"""
import html as htmllib
import json
import re
import sys

SRC = "/Users/na57/Library/Mobile Documents/iCloud~md~obsidian/Documents/no2/AI 工作区/高考备考/物理/3.1 运动学复习讲解-课件.html"
OUT_DIR = "/Users/na57/.workbuddy/tmp/kinematics_video"
PAUSE_SECONDS = 20
SPLIT_RE = re.compile(r"你?(推出来了吗|证明了吧|发现了吧|算出来了吗)[？?]?")


def clean(text: str) -> str:
    text = text.replace("<b>", "").replace("</b>", "")
    text = re.sub(r"\$([^$]*)\$", r"\1", text)
    # 口语化替换（让 TTS 念得自然）
    text = text.replace("v0", "v 零")
    text = re.sub(r"x([123])(?![0-9])", lambda m: "x " + "一二三"[int(m.group(1)) - 1], text)
    text = text.replace("x-t", "x t").replace("v-t", "v t")
    text = text.replace("v 下标 x/2", "v x 二分之一")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def main():
    src = open(SRC, encoding="utf-8").read()
    narrs = re.findall(r'<section class="slide[^"]*"\s+data-narration="([^"]*)">', src)
    if len(narrs) != 33:
        print(f"FATAL: expect 33 slides, got {len(narrs)}", file=sys.stderr)
        sys.exit(1)

    script, meta = [], []
    for i, raw in enumerate(narrs, 1):
        text = clean(htmllib.unescape(raw))
        sid = f"s{i:02d}"
        m = SPLIT_RE.search(text)
        if m:
            a_text = text[: m.start()].rstrip("。，, ") + "。"
            b_text = text[m.start():]
            script.append({"id": sid + "a", "text": a_text})
            script.append({"id": sid + "b", "text": b_text})
            meta.append({"slide": i, "id": sid, "parts": [sid + "a", sid + "b"], "pause": PAUSE_SECONDS})
            print(f"slide {i:2d} SPLIT  a={len(a_text)}ch  b={len(b_text)}ch")
        else:
            script.append({"id": sid, "text": text})
            meta.append({"slide": i, "id": sid, "parts": [sid]})
            print(f"slide {i:2d}        {len(text)}ch")

    with open(f"{OUT_DIR}/script.json", "w", encoding="utf-8") as f:
        json.dump(script, f, ensure_ascii=False, indent=1)
    with open(f"{OUT_DIR}/meta.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=1)
    print(f"OK: {len(script)} tts entries, {len(meta)} slides")


if __name__ == "__main__":
    main()
