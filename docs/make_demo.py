#!/usr/bin/env python3
"""
產生 README 頂部的風格切換示意 GIF（docs/demo-3styles.gif）。
自包含：只讀 repo 內 docs/showcase/ 的圖，無外部路徑依賴。

用法：  python3 docs/make_demo.py
需求：  Pillow（pip install pillow）

設計要點（踩過的坑）：
- **不要用 disposal=2**：那會在每幀之間先清成背景色，背景索引若是黑 → 切換時閃黑。
  全幀都是不透明整張圖，用 disposal=1（後幀直接蓋前幀）即可，乾淨不閃。
- 共用調色盤要涵蓋所有場景（深 navy + 亮 meme + 暖 tyn），否則某場景會被量化歪。
- 卡片**等比縮放 + 垂直置中**，才能同時容納 4:5 直式與 1:1 方形而不變形。
- 換內容時把輸出檔名一起換（demo-*.gif），避免 GitHub camo 快取舊圖。
"""
import os
from PIL import Image, ImageDraw, ImageFont

DOCS = os.path.dirname(os.path.abspath(__file__))
SHOW = os.path.join(DOCS, "showcase")

# 三種風格各三張（皆為 repo 內 showcase 圖）
NAVY = [f"{SHOW}/now6pm-01-cover.png", f"{SHOW}/now6pm-02-data.png", f"{SHOW}/now6pm-03-cta.png"]
MEME = [f"{SHOW}/meme-01-cover.png", f"{SHOW}/meme-02-claudemd.png", f"{SHOW}/meme-03-skills.png"]
TYN = [f"{SHOW}/tyn-01-cover.png", f"{SHOW}/tyn-02-cal.png", f"{SHOW}/tyn-03-brand.png"]

CW = 280           # 卡片欄寬
CH = int(CW * 1.25)  # 直式卡高 350（方形卡會在此高度內垂直置中）
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
    """等比縮放到欄寬 CW，保留原比例（4:5 或 1:1 都不變形），白色細框。"""
    out = []
    for p in paths:
        im = Image.open(p).convert("RGB")
        h = round(im.height * (CW / im.width))
        im = im.resize((CW, h), Image.LANCZOS)
        fr = Image.new("RGB", (CW + 4, h + 4), (255, 255, 255))
        fr.paste(im, (2, 2))
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
        y = TOP + (CH - t.height) // 2      # 垂直置中：方形卡不變形、直式卡填滿
        im.paste(t, (x, y))
        x += CW + GAP
    return im


def build():
    scenes = [
        (base_frame(TYN, "STYLE 3 · client / food", (198, 166, 109)), "tyn"),
        (base_frame(NAVY, "STYLE 1 · navy poster", (90, 150, 255)), "navy"),
        (base_frame(MEME, "STYLE 2 · meme street", (255, 210, 40)), "meme"),
    ]
    # 首幀＝tyn（新加入的案例，一眼看到）→ navy → meme →（loop 回 tyn）
    HOLD, XF = 1500, 110
    xfades = [0.2, 0.4, 0.6, 0.8]
    frames, durations = [], []
    n = len(scenes)
    for i in range(n):
        cur = scenes[i][0]
        nxt = scenes[(i + 1) % n][0]
        frames.append(cur); durations.append(HOLD)
        for a in xfades:
            frames.append(Image.blend(cur, nxt, a)); durations.append(XF)

    # 共用調色盤：三場景疊起來一起量化
    combo = Image.new("RGB", (W, H * n))
    for i, (f, _) in enumerate(scenes):
        combo.paste(f, (0, H * i))
    pal = combo.quantize(colors=256, method=Image.FASTOCTREE)
    qframes = [f.quantize(palette=pal, dither=Image.NONE) for f in frames]

    gif = os.path.join(DOCS, "demo-3styles.gif")
    qframes[0].save(gif, save_all=True, append_images=qframes[1:],
                    duration=durations, loop=0, disposal=1, optimize=False)
    print("gif:", gif, os.path.getsize(gif) // 1024, "KB",
          "canvas", (W, H), "frames", len(frames))


if __name__ == "__main__":
    build()
