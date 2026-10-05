#!/usr/bin/env python3
"""重新组装运动学讲解视频：停顿 20s->2s，并烧入中文字幕（PingFang SC）。
素材从原工作区拷贝到 /tmp/kin_vid（无空格路径，规避 filtergraph 转义问题）。
"""
import json, subprocess, os, shutil, sys

FF = "/Users/na57/.workbuddy/binaries/ffmpeg/ffmpeg"
FP = "/Users/na57/.workbuddy/binaries/ffmpeg/ffprobe"
SRC = "/Users/na57/.workbuddy/tmp/kinematics_video"   # 原工程：shots/, audio/, timing.json, script.json, meta.json
OUT = "/tmp/kin_vid"
PAUSE = 2.0      # 第2点：推导停顿由 20s 缩短为 2s
TAIL = 0.8
SR = 44100

os.makedirs(f"{OUT}/shots", exist_ok=True)
os.makedirs(f"{OUT}/audio", exist_ok=True)
os.makedirs(f"{OUT}/audio_full", exist_ok=True)
os.makedirs(f"{OUT}/segs", exist_ok=True)

def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print("CMD FAIL:", " ".join(cmd)[:300], file=sys.stderr)
        print(r.stderr[-1500:], file=sys.stderr)
        sys.exit(1)
    return r

def dur_of(path):
    r = subprocess.run([FP, "-v", "error", "-show_entries", "format=duration",
                        "-of", "csv=p=0", path], capture_output=True, text=True)
    return float(r.stdout.strip())

# ---- 拷贝 shots / audio ----
for f in os.listdir(f"{SRC}/shots"):
    shutil.copy(f"{SRC}/shots/{f}", f"{OUT}/shots/{f}")
for f in os.listdir(f"{SRC}/audio"):
    shutil.copy(f"{SRC}/audio/{f}", f"{OUT}/audio/{f}")

script = {e["id"]: e["text"] for e in json.load(open(f"{SRC}/script.json"))}
timing = {it["id"]: it["dur"] for it in json.load(open(f"{SRC}/timing.json"))["items"]}
meta = json.load(open(f"{SRC}/meta.json"))

# 校验：所有 part 的 id 都在 timing/script 中
for m in meta:
    for p in m["parts"]:
        assert p in timing, f"missing timing {p}"
        assert p in script, f"missing script {p}"

def srt_time(t):
    h = int(t // 3600); t -= h*3600
    m = int(t // 60); t -= m*60
    s = int(t); ms = int(round((t - s)*1000))
    if ms == 1000:
        s += 1; ms = 0
    return f"{h:02}:{m:02}:{s:02},{ms:03}"

MAXLEN = 36  # 每条字幕最多字数（中文）；含公式短句最长约33字，留余量；1920宽/40px下约1440px仍安全

PAUSE_CUE = "（暂停视频，拿出纸笔推导，推完再继续播放）"

# 公式段落的「显示版」字幕：旁白仍念口语稿（v 减 v 零），但字幕显示标准公式记法。
# 仅覆盖含公式念白的段落；其余段落沿用口语稿（口语=字面，无需替换）。
DISPLAY = {
 "s12a": "我们要推导第一个，速度公式。已知的出发点只有一个：加速度的定义式， a = (v − v₀) ⁄ t 。现在，请暂停视频，拿出纸笔，独立把它变形为 v = v₀ + at ，推完之后再继续播放。",
 "s12b": "你推出来了吗？把分母 t 乘到左边，就得到 v − v₀ = at，也就是 v = v₀ + at。记住它是矢量式，v₀、a、v 都要带符号，适用条件就是匀变速直线运动、a 恒定。",
 "s13a": "第二个，位移公式，这是三个里最容易写错的一个。已知两个东西：匀变速运动中速度均匀变化，所以平均速度等于初末速度的平均值；以及我们刚推出来的速度公式。现在请暂停视频，拿出纸笔，由位移等于平均速度乘时间，把 v 用 v₀ + at 代入，自己整理出位移公式，推完之后再继续播放。",
 "s13b": "你推出来了吗？代入后整理，得到的就是 x = v₀t + ½at²。注意，位移和时间成二次函数关系，它同样是矢量式。",
 "s14a": "第三个，速度位移公式，三个里推导最繁琐、但考试最常用。思路是：从速度公式解出时间 t，代入位移公式，通分化简，把 t 消掉。现在请暂停视频，拿出纸笔，独立推出 v² − v₀² = 2ax ，推完之后再继续播放。",
 "s14b": "你推出来了吗？从速度公式得 t = (v − v₀) ⁄ a，代入位移公式后通分、展开、消去 t，最终得到 v² − v₀² = 2ax。它最大的特点是不含时间 t，所以当题目根本没给时间、也不求时间时，用它最方便。",
 "s15":  "三个公式怎么选？原则只有一个：看已知量和待求量里包含哪几个字母。速度公式 v = v₀ + at；位移公式 x = v₀t + ½at²；速度位移公式 v² − v₀² = 2ax。说白了，哪个公式已知的量最多、未知的量最少，就先选哪个。不要拿起来就套，先看清楚再动手。",
 "s16":  "在三个基本公式之上，我们还能推出三个重要推论。推论一：平均速度等于中间时刻的瞬时速度，即 v(t/2)，打点计时器求某点速度就靠它。推论二：中间位置的速度 v(x/2) = √[(v₀² + v²) ⁄ 2]。推论三：连续相等时间内的位移差 Δx = aT²，也就是逐差公式，用来求加速度、判断是不是匀变速。这三个推论，考试极高频，也必须会推导。",
 "s17a": "推论一，平均速度等于中间时刻的瞬时速度，这是打点计时器求某点速度的理论依据。已知中间时刻的速度 v(t/2) = v₀ + a·t⁄2，以及位移公式。现在请暂停视频，拿出纸笔，自己证明平均速度也等于这个值，并进一步写成初末速度的平均值，推完之后再继续播放。",
 "s17b": "你证明了吧？把位移公式除以 t，得到 v₀ + at⁄2，和中间时刻速度 v(t/2) 完全一样；再代入 v = v₀ + at，也就等于初末速度的平均值 (v₀ + v)⁄2。",
 "s18a": "推论二，中间位置的速度。把总位移分成前后两段，每段都是 x⁄2。对前半段用一次速度位移公式，对后半段再用一次，两个式子右边都等于 ax。现在请暂停视频，拿出纸笔，由这两个式子相等，自己移项推出 v(x/2) = √[(v₀² + v²) ⁄ 2] ，推完之后再继续播放。",
 "s18b": "推出来了吗？让两式相等、移项，就得到 2v(x/2)² = v₀² + v²，开方即得 v(x/2) = √[(v₀² + v²) ⁄ 2]。这里有个有意思的结论：无论加速还是减速，中间位置的速度都大于中间时刻的速度，只有匀速时才相等。",
 "s19a": "推论三，逐差公式。已知第1个 T 内和第2个 T 内的位移表达式。现在请暂停视频，拿出纸笔，自己写出第3个 T 内的位移 x₃，并计算相邻两段的位移差 x₂ − x₁、x₃ − x₂，观察规律，推完之后再继续播放。",
 "s19b": "你发现了吧？x₁ = v₀T + ½aT²，x₂ = v₀T + (3⁄2)aT²，相邻相减，v₀T 项消掉，差正好是 aT²。推广一下，第 m 段减第 n 段等于 (m − n)aT²。",
 "s20":  "初速度为零的匀加速运动，有一组漂亮的比例关系，是快速解题的利器。五个比例： 各时刻速度比 v₁∶v₂∶v₃ = 1∶2∶3； 各段位移比 x₁∶x₂∶x₃ = 1²∶2²∶3²； 连续相等时间内位移比 1∶3∶5； 通过前 x、前 2x 的时间比 t₁∶t₂∶t₃ = 1∶√2∶√3； 通过连续相等位移的时间比 1∶(√2−1)∶(√3−√2)。记住，这些只适用于初速度为零的匀加速。",
 "s23":  "再看 v−t 图象，这是更重要的一个。纵坐标瞬时速度，横坐标时间，斜率代表加速度。水平直线是匀速，倾斜直线是匀变速，曲线是变加速。最关键的是：图线和时间轴围成的面积代表位移，上方为正，下方为负。注意一个高频坑：两 v−t 图线交点表示速度相等，绝不是相遇！纵轴截距是初速度。",
 "s30b": "你算出来了吗？常规做法先算刹车时间只有4秒，说明5秒时车已停，再用 v² = 2ax 求出位移；逆向思维更妙：把刹车倒过来看成从静止匀加速4秒，位移 x = ½ × 5 × 16 = 40 米。重点提醒：刹车问题一定要先算刹车时间，题目给的时间可能比刹车时间长，车早停了！",
}

def chunk_text(t, maxlen=MAXLEN):
    """按标点切分 + 贪心合并，保证每条 <= maxlen。"""
    import re
    segs = [s for s in re.split(r"(?<=[，。！？；：、])", t) if s]
    chunks, buf = [], ""
    for s in segs:
        if len(buf) + len(s) <= maxlen:
            buf += s
        else:
            if buf:
                chunks.append(buf.strip())
            while len(s) > maxlen:          # 单个分句超长则硬切
                chunks.append(s[:maxlen].strip())
                s = s[maxlen:]
            buf = s
    if buf:
        chunks.append(buf.strip())
    return chunks

def cues_for_span(st, en, text):
    """把 [st,en] 按 chunk 字数比例切成多条字幕。"""
    chunks = chunk_text(text)
    total_chars = sum(len(c) for c in chunks)
    out, cur = [], st
    for i, c in enumerate(chunks):
        if i == len(chunks) - 1:
            nxt = en
        else:
            nxt = cur + (en - st) * len(c) / total_chars
        out.append((cur, nxt, c))
        cur = nxt
    return out

# ---- 1) 互动页音频：a + 2s 静音 + b ----
for m in meta:
    sid, parts = m["id"], m["parts"]
    if len(parts) == 1:
        continue
    out = f"{OUT}/audio_full/{sid}.mp3"
    run([FF, "-y", "-i", f"{OUT}/audio/{parts[0]}.mp3",
         "-f", "lavfi", "-t", str(PAUSE), "-i", f"anullsrc=r={SR}:cl=stereo",
         "-i", f"{OUT}/audio/{parts[1]}.mp3",
         "-filter_complex",
         f"[0:a]aresample={SR},aformat=channel_layouts=stereo[a0];"
         f"[2:a]aresample={SR},aformat=channel_layouts=stereo[a2];"
         f"[a0][1:a][a2]concat=n=3:v=0:a=1[a]",
         "-map", "[a]", "-b:a", "192k", out])
    print(f"{sid}: full={dur_of(out):.2f}s (a={timing[parts[0]]:.2f}+{PAUSE}+b={timing[parts[1]]:.2f})")

# ---- 2) 逐页字幕 SRT + 分段视频 ----
FONT_DIR = f"{OUT}/fonts"
FONT_NAME = "PingFang SC"
list_lines = []
total = 0.0
for m in meta:
    sid = m["id"]; parts = m["parts"]
    # 字幕 cue（本地时间轴，0 基），长旁白按标点切成 <=30 字短句
    # 公式段落优先用 DISPLAY 显示版（保留口语旁白不变，字幕显示标准公式记法）
    cues = []
    if len(parts) == 1:
        cues = cues_for_span(0.0, timing[parts[0]], DISPLAY.get(parts[0], script[parts[0]]))
    else:
        a = timing[parts[0]]; b = timing[parts[1]]
        cues += cues_for_span(0.0, a, DISPLAY.get(parts[0], script[parts[0]]))
        cues.append((a, a + PAUSE, PAUSE_CUE))
        cues += cues_for_span(a + PAUSE, a + PAUSE + b, DISPLAY.get(parts[1], script[parts[1]]))
    srt_path = f"{OUT}/segs/{sid}.srt"
    with open(srt_path, "w", encoding="utf-8") as f:
        for i, (st, en, txt) in enumerate(cues, 1):
            f.write(f"{i}\n{srt_time(st)} --> {srt_time(en)}\n{txt}\n\n")

    apath = f"{OUT}/audio_full/{sid}.mp3" if len(parts) > 1 else f"{OUT}/audio/{sid}.mp3"
    d = dur_of(apath) + TAIL
    shot = f"{OUT}/shots/slide_{sid[1:]}.png"
    seg = f"{OUT}/segs/{sid}.mp4"

    vf = (f"scale=1920:1080:flags=lanczos,format=yuv420p,"
          f"subtitles={srt_path}:fontsdir={FONT_DIR}:"
          f"force_style='FontName={FONT_NAME},FontSize=40,PrimaryColour=&HFFFFFF,"
          f"OutlineColour=&H000000,Outline=3,Shadow=1,Alignment=2,MarginV=70,"
          f"PlayResX=1920,PlayResY=1080'")

    run([FF, "-y", "-loop", "1", "-framerate", "25", "-i", shot,
         "-i", apath,
         "-vf", vf,
         "-t", f"{d:.3f}", "-r", "25",
         "-c:v", "libx264", "-preset", "medium", "-crf", "18",
         "-c:a", "aac", "-b:a", "192k", "-ar", str(SR), "-ac", "2", seg])
    total += d
    list_lines.append(f"file '{seg}'")
    print(f"{sid}: seg {d:.2f}s  cues={len(cues)}")

with open(f"{OUT}/concat.txt", "w") as f:
    f.write("\n".join(list_lines) + "\n")

final = f"{OUT}/final.mp4"
run([FF, "-y", "-f", "concat", "-safe", "0", "-i", f"{OUT}/concat.txt", "-c", "copy", final])
print(f"DONE final={final} est_total={total:.1f}s = {total/60:.1f}min")
