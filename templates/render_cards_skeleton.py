#!/usr/bin/env python3
"""social-cards skeleton — copy + edit CARDS array for new topics.

Output: 6 cards (cover / 3 steps / 1 cost / 1 cta), 1080x1350 PNG.
"""
import subprocess
from pathlib import Path

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
PROJ   = Path(__file__).parent
TEMPLATE = (PROJ / "template.html").read_text(encoding="utf-8")

# === Edit handle + tag for your account ===
HANDLE = "@your_handle"
DEFAULT_TAG = "更少 X，更多 Y。"

# === Inline icon helpers (more in templates/icons.py) ===
def icon(svg_inner):
    return f'<svg viewBox="0 0 100 100" fill="none" stroke="currentColor" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round">{svg_inner}</svg>'

ARROW = icon('<line x1="50" y1="20" x2="50" y2="80"/><polyline points="35,65 50,80 65,65"/>')

def step(num, title, desc, icon_svg):
    return f"""
    <div class="step">
      <div class="num">{num}</div>
      <div class="body"><h3>{title}</h3><p>{desc}</p></div>
      <div class="icon">{icon_svg}</div>
    </div>"""

def arrow():
    return f'<div class="arrow-down">{ARROW}</div>'

# === EDIT THIS ARRAY for your topic ===
CARDS = [
    {
        "name": "card_1_cover",
        "body_class": "cover",
        "tag": "your tagline here",
        "content": """
  <div class="kicker">Your Kicker<span class="accent">×</span>secondary</div>
  <div class="title-bar"></div>
  <div class="title">主標題<br>第二行</div>
  <div class="subtitle">副標一句話<br>第二行（選用）</div>
  <div class="big-stat">$X<span class="unit">USD</span></div>
  <div class="stat-caption">數字旁邊的小註解</div>
""",
    },
    # ... add more cards (steps, cost, cta)
]

def build(c):
    h = TEMPLATE.replace("{{BODY_CLASS}}", c["body_class"])
    h = h.replace("{{CONTENT}}", c["content"])
    h = h.replace("{{TAG}}", c.get("tag", DEFAULT_TAG))
    h = h.replace("@yourhandle", HANDLE)
    return h

def render(c):
    name = c["name"]
    html = PROJ / f"{name}.html"
    png  = PROJ / f"{name}.png"
    html.write_text(build(c), encoding="utf-8")
    print(f"  rendering {name}.png  ", end="", flush=True)
    subprocess.run([CHROME, "--headless=new", "--disable-gpu",
                    "--no-sandbox", "--hide-scrollbars",
                    "--force-device-scale-factor=1",
                    "--window-size=1080,1350",
                    f"--screenshot={png}", f"file://{html}"],
                   capture_output=True, timeout=60)
    print(f"✓  {png.stat().st_size//1024} KB" if png.exists() else "✗")

if __name__ == "__main__":
    for c in CARDS:
        render(c)
    print(f"\nDone → {PROJ}")
