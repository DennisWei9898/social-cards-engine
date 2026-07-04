#!/usr/bin/env python3
"""
產生 README 頂部的風格切換示意 GIF（docs/demo-styles.gif）。
自包含：只讀 repo 內 docs/showcase/ 的圖，無外部路徑依賴。

用法：  python3 docs/make_demo.py
需求：  Pillow（pip install pillow）

設計要點（踩過的坑）：
- **不要用 disposal=2**：那會在每幀之間先清成背景色，背景索引若是黑 → 切換時閃黑。
  全幀都是不透明整張圖，用 disposal=1（後幀直接蓋前幀）即可，乾淨不閃。
- 共用調色盤要涵蓋 navy(深) + meme(亮) 兩場景，否則深色場景會被量化歪掉。
"""
import os
from PIL import Image, ImageDraw, ImageFont

DOCS = os.path.dirname(os.path.abspath(__file__))
SHOW = os.path.join(DOCS, "showcase")

# 兩種風格各三張（皆為 repo 內 showcase 圖）
NAVY = [f"{SHOW}/now6pm-01-cover.png", f"{SHOW}/now6pm-02-data.png", f"{SHOW}/now6pm-03-cta.png"]
MEME = [f"{SHOW}/meme-01-cover.png", f"{SHOW}/meme-02-claudemd.png", f"{SHOW}/meme-03-skills.png"]

CW = 280
CH = int(CW * 1.25)
GAP, MARGIN, TOP = 24, 34, 128
W = MARGIN * 2 + CW * 3 + GAP * 2
H = TOP + CH + 34
BG = (23, 27, 38)
FG = (238, 240, 245)
SUB = (150, 160, 180)


def font(size, bold=True):
    cands = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ]
    for c in cands:
        if os.path.exists(c):
            try:
                return ImageFont.truetype(c, size)
            except Exception:
                pass
    return ImageFont.load_default()


F_TITLE, F_SUB, F_LABEL = font(38), font(20, False), font(26)


def thumbs(paths):
    out = []
    for p in paths:
        t = Image.open(p).convert("RGB").resize((CW, CH), Image.LANCZOS)
        fr = Image.new("RGB", (CW + 4, CH + 4), (255, 255, 255))
        fr.paste(t, (2, 2))
        out.append(fr)
    return out


def base_frame(paths, label, accent):
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    d.text((MARGIN, 26), "social-cards-engine", font=F_TITLE, fill=FG)
    d.text((MARGIN, 74), "one engine  →  swap brand pack  →  new style", font=F_SUB, fill=SUB)
    lw = d.textlength(label, font=F_LABEL)
    pad = 14
    x1 = W - MARGIN - lw - pad * 2
    d.rounded_rectangle([x1, 30, W - MARGIN, 68], radius=19, fill=accent)
    d.text((x1 + pad, 36), label, font=F_LABEL, fill=(20, 20, 24))
    x = MARGIN
    for t in thumbs(paths):
        im.paste(t, (x, TOP))
        x += CW + GAP
    return im


def build():
    navy_f = base_frame(NAVY, "STYLE 1 · navy poster", (90, 150, 255))
    meme_f = base_frame(MEME, "STYLE 2 · meme street", (255, 210, 40))

    HOLD, XF = 1500, 110
    xfades = [0.2, 0.4, 0.6, 0.8]  # 多兩級中間幀，過場更平滑
    frames, durations = [], []
    # meme 先（首幀即見風格差異）→ 淡入 navy → navy → 淡回 meme（loop）
    frames.append(meme_f); durations.append(HOLD)
    for a in xfades:
        frames.append(Image.blend(meme_f, navy_f, a)); durations.append(XF)
    frames.append(navy_f); durations.append(HOLD)
    for a in xfades:
        frames.append(Image.blend(navy_f, meme_f, a)); durations.append(XF)

    # 共用調色盤：涵蓋 navy+meme 兩場景（垂直疊起來一起量化）
    combo = Image.new("RGB", (W, H * 2))
    combo.paste(navy_f, (0, 0)); combo.paste(meme_f, (0, H))
    pal = combo.quantize(colors=256, method=Image.FASTOCTREE)
    qframes = [f.quantize(palette=pal, dither=Image.NONE) for f in frames]

    gif = os.path.join(DOCS, "demo-styles.gif")
    # disposal=1（不清除背景）→ 切換不閃黑；optimize=False 保整張不透明幀
    qframes[0].save(gif, save_all=True, append_images=qframes[1:],
                    duration=durations, loop=0, disposal=1, optimize=False)
    print("gif:", gif, os.path.getsize(gif) // 1024, "KB",
          "canvas", (W, H), "frames", len(frames))


if __name__ == "__main__":
    build()
