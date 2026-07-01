#!/usr/bin/env python3
"""Render 6 ELI5 social cards from a single template, export 1080x1350 PNGs.

Output:
  threads_cards/card_1_cover.png
  threads_cards/card_2_steps_part1.png
  threads_cards/card_3_steps_part2.png
  threads_cards/card_4_cost.png
  threads_cards/card_5_two_paths.png
  threads_cards/card_6_cta.png

Render via Chrome headless --screenshot.
"""
import subprocess
import sys
from pathlib import Path

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
PROJ = Path(__file__).resolve().parent
# 使用者 預設：IG SQUARE 1080x1080，navy 品牌識別 palette
TEMPLATE = (PROJ / "template_square.html").read_text(encoding="utf-8")
CANVAS_W, CANVAS_H = 1080, 1080

# === SVG ICONS (inline, brand color via currentColor) ===
ICON_SCISSORS = """<svg viewBox="0 0 100 100" fill="none" stroke="currentColor" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round">
<circle cx="20" cy="25" r="12"/><circle cx="20" cy="75" r="12"/>
<line x1="32" y1="33" x2="85" y2="65"/><line x1="32" y1="67" x2="85" y2="35"/>
<line x1="60" y1="50" x2="80" y2="50" stroke-dasharray="2 4"/>
</svg>"""

ICON_PALETTE = """<svg viewBox="0 0 100 100" fill="none" stroke="currentColor" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round">
<path d="M50 15 C25 15, 15 35, 15 55 C15 72, 28 85, 45 85 C50 85, 50 78, 47 75 C44 72, 50 68, 55 68 C70 68, 85 60, 85 45 C85 28, 70 15, 50 15Z"/>
<circle cx="32" cy="40" r="4" fill="currentColor"/><circle cx="50" cy="32" r="4" fill="currentColor"/>
<circle cx="68" cy="42" r="4" fill="currentColor"/><circle cx="68" cy="58" r="4" fill="currentColor"/>
</svg>"""

ICON_MIC = """<svg viewBox="0 0 100 100" fill="none" stroke="currentColor" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round">
<rect x="38" y="15" width="24" height="45" rx="12"/>
<path d="M28 50 C28 65, 38 75, 50 75 C62 75, 72 65, 72 50"/>
<line x1="50" y1="75" x2="50" y2="88"/><line x1="38" y1="88" x2="62" y2="88"/>
<line x1="20" y1="38" x2="14" y2="38"/><line x1="20" y1="48" x2="10" y2="48"/><line x1="20" y1="58" x2="14" y2="58"/>
</svg>"""

ICON_PUZZLE = """<svg viewBox="0 0 100 100" fill="none" stroke="currentColor" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round">
<path d="M15 25 H42 V20 C42 14, 48 14, 48 20 V25 H72 V47 H77 C83 47, 83 53, 77 53 H72 V75 H50 V70 C50 64, 44 64, 44 70 V75 H15 Z"/>
</svg>"""

ICON_MUSIC = """<svg viewBox="0 0 100 100" fill="none" stroke="currentColor" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round">
<path d="M35 70 V25 L75 18 V63"/>
<circle cx="30" cy="72" r="9" fill="currentColor"/><circle cx="70" cy="65" r="9" fill="currentColor"/>
</svg>"""

ICON_FILM = """<svg viewBox="0 0 100 100" fill="none" stroke="currentColor" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round">
<rect x="15" y="25" width="70" height="50" rx="4"/>
<line x1="22" y1="25" x2="22" y2="75"/><line x1="78" y1="25" x2="78" y2="75"/>
<circle cx="22" cy="35" r="2" fill="currentColor"/><circle cx="22" cy="50" r="2" fill="currentColor"/><circle cx="22" cy="65" r="2" fill="currentColor"/>
<circle cx="78" cy="35" r="2" fill="currentColor"/><circle cx="78" cy="50" r="2" fill="currentColor"/><circle cx="78" cy="65" r="2" fill="currentColor"/>
<polygon points="42,40 42,60 62,50" fill="currentColor"/>
</svg>"""

ICON_COIN = """<svg viewBox="0 0 100 100" fill="none" stroke="currentColor" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round">
<circle cx="50" cy="50" r="32"/><circle cx="50" cy="50" r="24"/>
<text x="50" y="60" text-anchor="middle" font-size="28" font-weight="900" fill="currentColor" stroke="none">$</text>
</svg>"""

ICON_LAYERS = """<svg viewBox="0 0 100 100" fill="none" stroke="currentColor" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round">
<polygon points="50,15 85,32 50,49 15,32"/>
<polyline points="15,50 50,67 85,50"/>
<polyline points="15,68 50,85 85,68"/>
</svg>"""

ICON_ROCKET = """<svg viewBox="0 0 100 100" fill="none" stroke="currentColor" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round">
<path d="M50 12 C62 25, 70 40, 70 58 V75 H30 V58 C30 40, 38 25, 50 12Z"/>
<circle cx="50" cy="42" r="7"/>
<path d="M30 60 L18 72 L25 80 M70 60 L82 72 L75 80"/>
<path d="M40 80 L42 90 M50 80 L50 92 M60 80 L58 90"/>
</svg>"""

ICON_BUBBLE = """<svg viewBox="0 0 100 100" fill="none" stroke="currentColor" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round">
<path d="M15 35 C15 22, 25 15, 38 15 H62 C75 15, 85 22, 85 35 V52 C85 65, 75 72, 62 72 H45 L25 85 V72 C20 72, 15 65, 15 52Z"/>
<circle cx="35" cy="44" r="3" fill="currentColor"/><circle cx="50" cy="44" r="3" fill="currentColor"/><circle cx="65" cy="44" r="3" fill="currentColor"/>
</svg>"""

ARROW = """<svg viewBox="0 0 100 100" fill="none" stroke="currentColor" stroke-width="4" stroke-linecap="round" stroke-linejoin="round">
<line x1="50" y1="20" x2="50" y2="80"/><polyline points="35,65 50,80 65,65"/>
</svg>"""


def step(num, title, desc, icon_svg):
    return f"""
    <div class="step">
      <div class="num">{num}</div>
      <div class="body"><h3>{title}</h3><p>{desc}</p></div>
      <div class="icon">{icon_svg}</div>
    </div>"""


def arrow():
    return f'<div class="arrow-down">{ARROW}</div>'


# ============= 6 CARDS =============

CARDS = [
    # ---------- 1 · Cover ----------
    {
        "name": "card_1_cover",
        "body_class": "cover",
        "tag": "Your Brand · tagline",
        "content": f"""
  <div class="kicker">AI 影片教學<span class="accent">×</span>製作流程公開</div>
  <div class="title-bar"></div>
  <div class="title">一篇文章<br>變 80 秒卡通片</div>
  <div class="subtitle">從劇本到影片，全自動 AI pipeline<br>單支總成本是…</div>
  <div class="big-stat">$18<span class="unit">NT</span></div>
  <div class="stat-caption">不到一杯手搖飲的價格</div>
""",
    },
    # ---------- 2 · Steps part 1 (1-3) ----------
    {
        "name": "card_2_steps_part1",
        "body_class": "",
        "tag": "Your Brand · tagline",
        "content": f"""
  <div class="kicker">AI Pipeline<span class="accent">×</span>4 個食材</div>
  <div class="title-bar"></div>
  <div class="title compact">4 個 AI 廚師<br>接力做的菜</div>
  <div class="steps" style="top: 360px;">
    {step("01", "剪劇本", "把文章剪成 23 句子幕，每句不超過 20 字", ICON_SCISSORS)}
    {arrow()}
    {step("02", "畫場景", "FLUX 生 7 張暖色 Q 版插畫，免費的 Pollinations 就行", ICON_PALETTE)}
    {arrow()}
    {step("03", "配音", "MiniMax voice clone 學你的聲音 30 秒就會講", ICON_MIC)}
  </div>
""",
    },
    # ---------- 3 · Steps part 2 (4-6) ----------
    {
        "name": "card_3_steps_part2",
        "body_class": "",
        "tag": "Your Brand · tagline",
        "content": f"""
  <div class="kicker">AI Pipeline<span class="accent">×</span>後段組裝</div>
  <div class="title-bar"></div>
  <div class="title compact">拼貼到上桌<br>2 分鐘交件</div>
  <div class="steps" style="top: 360px;">
    {step("04", "拼貼動畫", "HyperFrames + GSAP 自動把畫面、字幕、聲音對齊", ICON_PUZZLE)}
    {arrow()}
    {step("05", "配背景音樂", "Replicate Lyria 2 自動生 90 秒輕快 BGM", ICON_MUSIC)}
    {arrow()}
    {step("06", "渲染輸出", "ffmpeg 一鍵產出 IG 9:16 + YouTube 16:9 雙版本", ICON_FILM)}
  </div>
""",
    },
    # ---------- 4 · Cost breakdown ----------
    {
        "name": "card_4_cost",
        "body_class": "",
        "tag": "為什麼一支只要 NT$18？",
        "content": f"""
  <div class="kicker">Cost Breakdown<span class="accent">×</span>單支 NT$18</div>
  <div class="title-bar"></div>
  <div class="title compact">為什麼這麼<br>便宜？</div>
  <div class="steps" style="top: 360px;">
    {step("01", "畫圖 = $0", "Pollinations 免費，本地 ComfyUI 也是 $0", ICON_PALETTE)}
    {arrow()}
    {step("02", "配音 ≈ $0", "MiniMax 月費攤分，每支幾乎免費", ICON_MIC)}
    {arrow()}
    {step("03", "BGM = NT$5.4", "Lyria 2 一首 USD$0.18，可商用", ICON_COIN)}
  </div>
""",
    },
    # ---------- 5 · Two paths ----------
    {
        "name": "card_5_two_paths",
        "body_class": "",
        "tag": "你也可以升級。",
        "content": f"""
  <div class="kicker">Getting Started<span class="accent">×</span>兩條路給你選</div>
  <div class="title-bar"></div>
  <div class="title compact">完全不會程式<br>也能跑</div>
  <div class="steps" style="top: 360px;">
    {step("01", "最低門檻路線", "InVideo / CapCut 手動拼貼，每支 30-60 分鐘，免月費", ICON_LAYERS)}
    {arrow()}
    {step("02", "進階自動化路線", "我這套 illustrated-reel skill，每支 5 分鐘出片", ICON_ROCKET)}
  </div>
""",
    },
    # ---------- 6 · CTA ----------
    {
        "name": "card_6_cta",
        "body_class": "cta",
        "tag": "Your Brand · tagline",
        "content": f"""
  <div class="kicker">完整 Step-by-Step<span class="accent">×</span>免費領取</div>
  <div class="title-bar" style="top: 240px;"></div>
  <div class="title" style="top: 220px; font-size: 110px;">想要<br>完整教學？</div>
  <div class="cta-text">留言領取，我會把<br>完整腳本 + MD 教學傳給你</div>
  <div class="cta-bubble">「 +1 」</div>
""",
    },
]


def build_html(card):
    html = TEMPLATE.replace("{{BODY_CLASS}}", card["body_class"])
    html = html.replace("{{CONTENT}}", card["content"])
    html = html.replace("{{TAG}}", card["tag"])
    return html


def render(card):
    name = card["name"]
    html_path = PROJ / f"{name}.html"
    png_path  = PROJ / f"{name}.png"
    html_path.write_text(build_html(card), encoding="utf-8")
    print(f"  rendering {name}.png  ", end="", flush=True)
    cmd = [
        CHROME,
        "--headless=new",
        "--disable-gpu",
        "--no-sandbox",
        "--hide-scrollbars",
        "--force-device-scale-factor=1",
        f"--window-size={CANVAS_W},{CANVAS_H}",
        f"--screenshot={png_path}",
        f"file://{html_path}",
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    if png_path.exists():
        kb = png_path.stat().st_size // 1024
        print(f"✓  {kb} KB")
    else:
        print(f"✗  {r.stderr[-200:]}")


def main():
    print(f"=== Rendering {len(CARDS)} ELI5 social cards ({CANVAS_W}x{CANVAS_H} IG square) ===\n")
    for c in CARDS:
        render(c)
    print(f"\nOutput dir: {PROJ}")


if __name__ == "__main__":
    main()
