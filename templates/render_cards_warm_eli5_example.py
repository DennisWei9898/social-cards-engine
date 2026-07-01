#!/usr/bin/env python3
"""Loop Engineering IG 輪播 · warm-earth 版（對齊 reports ELI5 簡報視覺 DNA）.

視覺 DNA 萃取自 ./examples/loop-engineering-eli5/封面-cover.png
+ build_part1.py 色票：espresso 背景 + 赤陶橙圓 + 米白 callout 卡 + 琥珀金/鴨綠 accent。
出圖：HTML+CSS → Chrome headless → 1080x1080 PNG。
"""
import subprocess
from pathlib import Path

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
PROJ = Path(__file__).resolve().parent
CANVAS_W, CANVAS_H = 1080, 1080

TEMPLATE = """<!doctype html>
<html lang="zh-Hant"><head><meta charset="UTF-8"><style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;500;700;900&display=swap');
:root{
  --bg:#2A1208;          /* espresso 深咖啡 */
  --bg2:#371A0C;         /* 稍亮咖啡 */
  --terra:#C85A3C;       /* 赤陶橙 主色 */
  --terra-deep:#B83A2C;  /* 深赤陶 / 警示 */
  --cream:#F5EBDC;       /* 暖米白文字 */
  --card:#FBF4E8;        /* callout 米白卡 */
  --gold:#C8951E;        /* 琥珀金 accent */
  --teal:#3A9E8F;        /* 鴨綠 第二 accent */
  --brown:#7A4A38;       /* 棕灰 次要文字 */
  --peach:#E8B98C;       /* 蜜桃 裝飾 */
  --ink:#2A1208;         /* 卡內深字 */
}
*{margin:0;padding:0;box-sizing:border-box;-webkit-font-smoothing:antialiased;}
html,body{width:1080px;height:1080px;background:var(--bg);overflow:hidden;position:relative;
  font-family:'Noto Sans TC','PingFang TC',sans-serif;color:var(--cream);}
/* 簽名裝飾圓 */
.circle-tl{position:absolute;top:-300px;left:-230px;width:560px;height:560px;border-radius:50%;
  background:var(--terra);}
.circle-tr{position:absolute;top:-230px;right:-210px;width:470px;height:470px;border-radius:50%;
  background:var(--terra);opacity:.92;}
.circle-br{position:absolute;bottom:-220px;right:-180px;width:420px;height:420px;border-radius:50%;
  background:var(--peach);opacity:.9;}
.circle-br.dim{opacity:.14;}
/* Header */
.kicker{position:absolute;top:96px;left:90px;font-size:30px;font-weight:700;color:var(--terra);
  letter-spacing:3px;}
.kicker.on-terra{color:var(--cream);opacity:.92;}
.bar{position:absolute;left:90px;width:9px;background:var(--terra);border-radius:3px;}
.title{position:absolute;left:118px;font-weight:900;line-height:1.12;letter-spacing:-1px;color:var(--cream);}
.sub{position:absolute;left:90px;width:900px;font-size:33px;font-weight:500;line-height:1.5;color:var(--peach);}
.sub b{color:var(--gold);font-weight:900;}
/* steps（米白 callout 卡） */
.steps{position:absolute;left:90px;width:900px;display:flex;flex-direction:column;gap:24px;}
.step{background:var(--card);border-radius:26px;padding:28px 34px;display:flex;align-items:center;gap:26px;
  box-shadow:0 10px 30px rgba(0,0,0,.28);}
.step .num{flex-shrink:0;width:74px;height:74px;border-radius:50%;background:var(--terra);color:var(--card);
  font-size:30px;font-weight:900;display:flex;align-items:center;justify-content:center;letter-spacing:-1px;}
.step.warn .num{background:var(--terra-deep);}
.step.fix .num{background:var(--teal);}
.step .b{flex:1;}
.step .b h3{font-size:40px;font-weight:900;line-height:1.12;color:var(--ink);margin-bottom:4px;}
.step .b p{font-size:25px;font-weight:500;line-height:1.42;color:var(--brown);}
.step .ic{flex-shrink:0;width:92px;height:92px;display:flex;align-items:center;justify-content:center;color:var(--terra);}
.step.fix .ic{color:var(--teal);} .step.warn .ic{color:var(--terra-deep);}
.step .ic svg{width:100%;height:100%;}
.arrow{width:40px;height:40px;margin:-8px auto;color:var(--peach);opacity:.8;}
.arrow svg{width:100%;height:100%;}
/* footer */
.divider{position:absolute;bottom:118px;left:90px;width:900px;height:2px;background:var(--terra);opacity:.35;}
.footer{position:absolute;bottom:58px;left:90px;width:900px;display:flex;justify-content:space-between;
  align-items:center;font-size:25px;font-weight:700;}
.footer .h{color:var(--cream);} .footer .t{color:var(--peach);font-weight:500;opacity:.85;}
.page{position:absolute;bottom:60px;right:54px;font-size:24px;font-weight:700;color:var(--peach);opacity:.6;}
/* cover big stat */
.bigstat{position:absolute;left:90px;width:900px;text-align:center;font-weight:900;color:var(--terra);
  line-height:.9;letter-spacing:-6px;}
.bigstat .u{font-size:.34em;vertical-align:super;}
.statcap{position:absolute;left:90px;width:900px;text-align:center;font-size:34px;font-weight:900;color:var(--cream);}
/* cover callout strip */
.swipe{position:absolute;left:90px;width:900px;background:var(--card);border-radius:24px;padding:30px 36px;
  box-shadow:0 10px 30px rgba(0,0,0,.3);font-size:32px;font-weight:900;color:var(--terra-deep);
  display:flex;align-items:center;gap:16px;}
/* cta */
.ctatext{position:absolute;left:90px;width:900px;text-align:center;font-size:42px;font-weight:700;
  line-height:1.5;color:var(--cream);}
.bubble{position:absolute;left:50%;transform:translateX(-50%);background:var(--terra);color:var(--card);
  border-radius:30px;padding:34px 54px;font-size:80px;font-weight:900;box-shadow:0 12px 36px rgba(0,0,0,.35);}
</style></head><body>{{DECO}}{{CONTENT}}
<div class="divider"></div>
<div class="footer"><div class="h">@yourhandle</div><div class="t">{{TAG}}</div></div>
<div class="page">{{PAGE}}</div>
</body></html>"""

# ---- icons (line-art, currentColor) ----
I_TARGET='<svg viewBox="0 0 100 100" fill="none" stroke="currentColor" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"><circle cx="50" cy="50" r="30"/><circle cx="50" cy="50" r="17"/><circle cx="50" cy="50" r="5" fill="currentColor"/><line x1="50" y1="6" x2="50" y2="20"/><line x1="80" y1="50" x2="94" y2="50"/></svg>'
I_ROBOT='<svg viewBox="0 0 100 100" fill="none" stroke="currentColor" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"><rect x="22" y="34" width="56" height="42" rx="10"/><circle cx="40" cy="54" r="5" fill="currentColor"/><circle cx="60" cy="54" r="5" fill="currentColor"/><line x1="50" y1="22" x2="50" y2="34"/><circle cx="50" cy="17" r="5"/></svg>'
I_TASTE='<svg viewBox="0 0 100 100" fill="none" stroke="currentColor" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"><path d="M30 18 H70 L64 50 C64 60 56 66 50 66 C44 66 36 60 36 50 Z"/><line x1="50" y1="66" x2="50" y2="84"/><line x1="36" y1="84" x2="64" y2="84"/></svg>'
I_LOOP='<svg viewBox="0 0 100 100" fill="none" stroke="currentColor" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"><path d="M78 40 A30 30 0 1 0 82 58"/><polyline points="64,32 80,38 86,22"/></svg>'
I_FEED='<svg viewBox="0 0 100 100" fill="none" stroke="currentColor" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"><path d="M26 36 A28 28 0 0 1 78 46"/><polyline points="78,24 80,48 58,44"/><path d="M74 64 A28 28 0 0 1 22 54"/><polyline points="22,76 20,52 42,56"/></svg>'
I_EXAM='<svg viewBox="0 0 100 100" fill="none" stroke="currentColor" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"><rect x="26" y="16" width="48" height="68" rx="6"/><line x1="37" y1="36" x2="63" y2="36"/><polyline points="37,58 45,66 65,48"/></svg>'
I_WARN='<svg viewBox="0 0 100 100" fill="none" stroke="currentColor" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"><path d="M50 18 L86 80 H14 Z"/><line x1="50" y1="42" x2="50" y2="60"/><circle cx="50" cy="70" r="2.5" fill="currentColor"/></svg>'
I_SCALE='<svg viewBox="0 0 100 100" fill="none" stroke="currentColor" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"><line x1="50" y1="20" x2="50" y2="80"/><line x1="34" y1="80" x2="66" y2="80"/><line x1="22" y1="34" x2="78" y2="34"/><path d="M12 56 L22 34 L32 56 A10 10 0 0 1 12 56Z"/><path d="M68 56 L78 34 L88 56 A10 10 0 0 1 68 56Z"/></svg>'
I_SPLIT='<svg viewBox="0 0 100 100" fill="none" stroke="currentColor" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"><circle cx="50" cy="22" r="10"/><line x1="50" y1="32" x2="50" y2="50"/><path d="M50 50 L26 64"/><path d="M50 50 L74 64"/><circle cx="22" cy="74" r="9"/><circle cx="78" cy="74" r="9"/></svg>'
ARROW='<svg viewBox="0 0 100 100" fill="none" stroke="currentColor" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"><line x1="50" y1="22" x2="50" y2="78"/><polyline points="34,62 50,78 66,62"/></svg>'

def step(num, title, desc, icon, cls=""):
    return (f'<div class="step {cls}"><div class="num">{num}</div>'
            f'<div class="b"><h3>{title}</h3><p>{desc}</p></div>'
            f'<div class="ic">{icon}</div></div>')
def arr(): return f'<div class="arrow">{ARROW}</div>'

CARDS = [
    # 1 · Cover
    {"name":"w1_cover","tag":"Loop Engineering · 迴圈工程","page":"01",
     "deco":'<div class="circle-tl"></div><div class="circle-br dim"></div>',
     "content":f"""
  <div class="kicker on-terra">ELI5 白話導讀 · 2026 最紅 AI 工作法</div>
  <div class="bar" style="top:182px;height:200px;"></div>
  <div class="title" style="top:170px;font-size:88px;">「我已經不<br>prompt AI 了」</div>
  <div class="sub" style="top:430px;">Loop Engineering（迴圈工程）到底有沒有效？<br>關鍵，只有<b>一條鐵律</b>。</div>
  <div class="swipe" style="top:610px;">👉 90% 的人都把這條鐵律搞反了 — 滑下去看</div>
  <div class="bigstat" style="top:760px;font-size:150px;">100<span class="u">%</span></div>
"""},
    # 2 · 核心比喻
    {"name":"w2_analogy","tag":"核心比喻 · 廚房裡的兩個角色","page":"02",
     "deco":'<div class="circle-tr"></div><div class="circle-br dim"></div>',
     "content":f"""
  <div class="kicker">先記這個畫面 · 一間廚房</div>
  <div class="bar" style="top:150px;height:144px;"></div>
  <div class="title" style="top:142px;font-size:72px;">師傅做菜，<br>試吃員驗收</div>
  <div class="sub" style="top:336px;font-size:30px;">迴圈工程 = 讓 AI 一直做，<br>再請一個<b>獨立的人</b>用客觀標準退件重做</div>
  <div class="steps" style="top:486px;">
    {step("師","師傅（生成）","AI 一直做菜，一個版本接一個版本端出來",I_ROBOT)}
    {arr()}
    {step("審","獨立試吃員（驗收）","拿客觀標準驗收，不合格就退回重做",I_TASTE,"fix")}
  </div>
"""},
    # 3 · 迴圈骨架
    {"name":"w3_skeleton","tag":"自動回鍋食譜 · 4 個方格","page":"03",
     "deco":'<div class="circle-tr"></div><div class="circle-br dim"></div>',
     "content":f"""
  <div class="kicker">迴圈長什麼樣 · 拆成 3 步</div>
  <div class="bar" style="top:152px;height:140px;"></div>
  <div class="title" style="top:144px;font-size:74px;">迴圈長<br>什麼樣？</div>
  <div class="steps" style="top:344px;">
    {step("01","設定目標 goal","先說清楚「要做出什麼、怎樣才算過關」",I_TARGET)}
    {arr()}
    {step("02","生成 → 驗收","AI 先做一版，把關者跑檢查（過 / 不過）",I_LOOP)}
    {arr()}
    {step("03","回饋 → 重複","沒過？把錯誤餵回去重做，直到過或喊停",I_FEED)}
  </div>
"""},
    # 4 · 兩大地雷
    {"name":"w4_traps","tag":"90% 的人都踩這兩個雷","page":"04",
     "deco":'<div class="circle-tr" style="background:var(--terra-deep);"></div><div class="circle-br dim"></div>',
     "content":f"""
  <div class="kicker" style="color:var(--terra-deep);">為什麼你的迴圈沒效 · 2 大地雷</div>
  <div class="bar" style="top:152px;height:140px;background:var(--terra-deep);"></div>
  <div class="title" style="top:144px;font-size:74px;">最常見的<br>兩個雷</div>
  <div class="sub" style="top:312px;">迴圈有沒有效，<b style="color:var(--terra-deep);">100% 看把關者夠不夠硬</b></div>
  <div class="steps" style="top:452px;">
    {step("雷1","師傅當自己的試吃員","同個 AI 又寫又審，會學會騙過自己的評分",I_EXAM,"warn")}
    {arr()}
    {step("雷2","用「感覺」驗收","靠 AI 覺得不錯，而不是測試過沒過這種硬標準",I_WARN,"warn")}
  </div>
"""},
    # 5 · 兩個解藥
    {"name":"w5_fix","tag":"工具會換，這兩條鐵律不會","page":"05",
     "deco":'<div class="circle-tr" style="background:var(--teal);"></div><div class="circle-br dim"></div>',
     "content":f"""
  <div class="kicker" style="color:var(--teal);">解藥 · 兩個關鍵詞</div>
  <div class="bar" style="top:152px;height:140px;background:var(--teal);"></div>
  <div class="title" style="top:144px;font-size:74px;">記住這<br>兩個詞</div>
  <div class="sub" style="top:312px;">工具明年會換、紅的 repo 會過氣，<b style="color:var(--teal);">這兩條鐵律不會</b></div>
  <div class="steps" style="top:452px;">
    {step("01","寫審分離","師傅不能當試吃員，連 Anthropic 都用獨立模型當裁判",I_SPLIT,"fix")}
    {arr()}
    {step("02","硬訊號門控","驗收用量尺不用感覺：測試、編譯、字數能客觀判定",I_SCALE,"fix")}
  </div>
"""},
    # 6 · CTA
    {"name":"w6_cta","tag":"Loop Engineering · 白話導讀","page":"06",
     "deco":'<div class="circle-tl"></div><div class="circle-br"></div>',
     "content":f"""
  <div class="kicker on-terra">完整 51 張白話簡報 · 免費領</div>
  <div class="bar" style="top:206px;height:150px;"></div>
  <div class="title" style="top:194px;font-size:80px;">想要完整<br>懶人包？</div>
  <div class="ctatext" style="top:470px;">收藏這篇 + 留言「迴圈」<br>我把 51 張簡報 + LINE 讀書會傳給你</div>
  <div class="bubble" style="top:680px;">「 迴圈 」</div>
"""},
]

def build(c):
    h = TEMPLATE.replace("{{DECO}}", c["deco"]).replace("{{CONTENT}}", c["content"])
    return h.replace("{{TAG}}", c["tag"]).replace("{{PAGE}}", c["page"])

def render(c):
    name=c["name"]; hp=PROJ/f"{name}.html"; pp=PROJ/f"{name}.png"
    hp.write_text(build(c), encoding="utf-8")
    print(f"  {name}.png ", end="", flush=True)
    r=subprocess.run([CHROME,"--headless=new","--disable-gpu","--no-sandbox","--hide-scrollbars",
        "--force-device-scale-factor=1",f"--window-size={CANVAS_W},{CANVAS_H}",
        f"--screenshot={pp}",f"file://{hp}"],capture_output=True,text=True,timeout=60)
    print(f"✓ {pp.stat().st_size//1024}KB" if pp.exists() else f"✗ {r.stderr[-160:]}")

if __name__=="__main__":
    import sys
    only=sys.argv[1:] if len(sys.argv)>1 else None
    print(f"=== warm-earth carousel ({CANVAS_W}x{CANVAS_H}) ===")
    for c in CARDS:
        if only and not any(k in c["name"] for k in only): continue
        render(c)
    print(f"out: {PROJ}")
