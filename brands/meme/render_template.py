#!/usr/bin/env python3
"""Claude Code 最佳實踐 · 迷因版知識輪播 v2（4:5 1080x1350）.
huashu-design 修版：梗圖用原始比例不變形、置中、文字放進梗圖原生空白區；IG 乾淨排版。
真梗圖(imgflip 個人非商用)：drake 717² / brain 857x1202 / pikachu 1893² / thisisfine 580x282
"""
import subprocess
from pathlib import Path

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
PROJ = Path(__file__).resolve().parent
W, H = 1080, 1350
M = f"file://{PROJ}/memes"

TPL = """<!doctype html><html lang="zh-Hant"><head><meta charset="UTF-8"><style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@700;900&display=swap');
*{margin:0;padding:0;box-sizing:border-box;-webkit-font-smoothing:antialiased;}
html,body{width:1080px;height:1350px;background:#FBF7EF;position:relative;overflow:hidden;
 font-family:'Noto Sans TC','Arial Black',sans-serif;color:#1A1A1A;}
/* 頂部標題帶 */
.hd{position:absolute;top:0;left:0;width:1080px;padding:40px 54px 28px;font-weight:900;font-size:47px;
 line-height:1.22;letter-spacing:-1px;color:#1A1A1A;}
.hd .y{background:#FFD400;padding:2px 12px;border-radius:4px;box-decoration-break:clone;-webkit-box-decoration-break:clone;}
.hd .r{color:#E4002B;}
.hd .idx{color:#E4002B;font-size:52px;}
/* 白底大字（IG 乾淨排版，置中） */
.big{position:absolute;font-weight:900;color:#1A1A1A;line-height:1.28;text-align:center;letter-spacing:-.5px;}
.big .r{color:#E4002B;} .big .y{background:#FFD400;padding:1px 10px;border-radius:4px;}
.big .g{color:#0A7A2F;}
.sub{position:absolute;font-weight:700;color:#5a5348;line-height:1.5;text-align:center;}
/* 疊在梗圖原生空白區（黃/白）的黑字，不用描邊 */
.ov{position:absolute;font-weight:900;color:#1A1A1A;line-height:1.22;}
.ov .r{color:#E4002B;} .ov .g{color:#0A7A2F;} .ov small{font-weight:700;font-size:.72em;color:#555;}
/* 疊在複雜圖上的白字黑邊（僅必要時） */
.onimg{position:absolute;font-weight:900;color:#fff;-webkit-text-stroke:5px #000;paint-order:stroke fill;
 line-height:1.14;text-shadow:0 4px 12px rgba(0,0,0,.5);text-align:center;}
img{display:block;}
.frame{border:5px solid #1A1A1A;border-radius:10px;box-shadow:7px 7px 0 rgba(26,26,26,.12);}
/* emoji 大圖 */
.emo{position:absolute;left:0;width:1080px;text-align:center;line-height:1;}
/* 速查表 */
.trow{position:absolute;left:60px;width:960px;display:flex;align-items:center;gap:26px;
 border-bottom:3px solid #E3D9C6;padding:26px 6px;}
.trow .a{font-weight:900;font-size:40px;color:#E4002B;width:290px;flex-shrink:0;}
.trow .b{font-weight:700;font-size:34px;color:#1A1A1A;}
/* 收尾 */
.foot{position:absolute;bottom:34px;left:0;width:1080px;text-align:center;font-weight:700;
 font-size:24px;color:#b3a894;letter-spacing:1px;}
.pagen{position:absolute;top:40px;right:50px;font-weight:900;font-size:30px;color:#d8cbb2;}
.bubble{position:absolute;left:50%;transform:translateX(-50%);background:#E4002B;color:#fff;
 font-weight:900;font-size:82px;padding:28px 70px;border-radius:22px;border:6px solid #1A1A1A;
 box-shadow:9px 9px 0 #1A1A1A;}
.swipe{position:absolute;bottom:44px;right:54px;font-weight:900;font-size:32px;color:#E4002B;}
</style></head><body>{{BODY}}
<div class="foot">◆ Claude Code 最佳實踐 · 白話迷因版 · @yourhandle</div>
<div class="pagen">{{PG}}</div>{{SWIPE}}</body></html>"""

def card(name, body, pg, swipe=True):
    html = TPL.replace("{{BODY}}", body).replace("{{PG}}", pg)
    html = html.replace("{{SWIPE}}", '<div class="swipe">滑 →</div>' if swipe else '')
    hp = PROJ/f"{name}.html"; pp = PROJ/f"{name}.png"
    hp.write_text(html, encoding="utf-8"); print(f"  {name} ", end="", flush=True)
    r = subprocess.run([CHROME,"--headless=new","--disable-gpu","--no-sandbox","--hide-scrollbars",
        "--allow-file-access-from-files","--force-device-scale-factor=2",
        f"--window-size={W},{H}",f"--screenshot={pp}",f"file://{hp}"],
        capture_output=True,text=True,timeout=60)
    print(f"✓ {pp.stat().st_size//1024}KB" if pp.exists() else f"✗ {r.stderr[-160:]}")

CARDS = [
 # 1 cover — This Is Fine（580x282 原比例放大，不變形）
 ("m1_cover", f"""
  <div class="hd" style="font-size:50px;">當你點開 <span class="y">Claude Code</span> 中文神文…</div>
  <img class="frame" src="{M}/thisisfine.jpg" style="position:absolute;top:250px;left:40px;width:1000px;height:486px;">
  <div class="big" style="top:800px;left:50px;width:980px;font-size:54px;">「CLAUDE.md？MCP？Hooks？<br>…<span class="r">這三小</span>」</div>
  <div class="sub" style="top:1010px;left:60px;width:960px;font-size:38px;">😅 看不懂，不是你笨。<br>5 個生活比喻，3 分鐘看懂 👉</div>
""", "1/8"),
 # 2 CLAUDE.md — Drake（717²，黑字疊右側黃區）
 ("m2_claudemd", f"""
  <div class="hd"><span class="idx">①</span> <span class="y">CLAUDE.md</span> = 給 AI 的員工手冊</div>
  <img class="frame" src="{M}/drake.jpg" style="position:absolute;top:220px;left:150px;width:780px;height:780px;">
  <div class="ov" style="top:322px;left:545px;width:360px;font-size:47px;text-align:center;">寫 <span class="r">200 行</span><br>落落長家規<br><small>遵從率剩 52% 📉</small></div>
  <div class="ov" style="top:715px;left:545px;width:360px;font-size:47px;text-align:center;">寫 <span class="g">60 行</span><br>剛剛好<br><small>遵從率 76% ✅</small></div>
  <div class="big" style="top:1055px;left:50px;width:980px;font-size:48px;">你規定寫<span class="y">越多</span>，AI 反而<span class="y">越不鳥你</span> 🤡</div>
""", "2/8"),
 # 3 Skills — 當你…時（純字，乾淨置中）
 ("m3_skills", f"""
  <div class="hd"><span class="idx">②</span> <span class="y">Skills</span> = 抽屜裡的專業手冊</div>
  <div class="big" style="top:270px;left:60px;width:960px;font-size:52px;">當你 skill 的<br><span class="r">description 寫太模糊</span>…</div>
  <div class="emo" style="top:500px;font-size:230px;">🗄️🙅</div>
  <div class="big" style="top:820px;left:60px;width:960px;font-size:50px;">AI：「那我一本<br>都懶得翻」</div>
  <div class="sub" style="top:1085px;left:60px;width:960px;font-size:38px;">📚 書背標籤寫得夠準，AI 才知道<br>該翻哪一本</div>
""", "3/8"),
 # 4 Subagents — POV（純字＋emoji）
 ("m4_subagents", f"""
  <div class="hd"><span class="idx">③</span> <span class="y">Subagents</span> = 派助理出去查</div>
  <div class="big" style="top:250px;left:120px;width:840px;font-size:44px;background:#1A1A1A;color:#FFD400;padding:20px;border-radius:12px;">POV：你是經理</div>
  <div class="big" style="top:400px;left:60px;width:960px;font-size:50px;">卻自己跑去翻<br>整個 codebase 😵‍💫</div>
  <div class="emo" style="top:660px;font-size:64px;font-weight:900;color:#E4002B;">⬇ 改成 ⬇</div>
  <div class="emo" style="top:760px;font-size:104px;">🧑‍💼🧑‍💼🧑‍💼🧑‍💼</div>
  <div class="big" style="top:915px;left:60px;width:960px;font-size:46px;">一次派 <span class="r">4 個助理並行</span></div>
  <div class="sub" style="top:1080px;left:60px;width:960px;font-size:37px;">小助理(Haiku)查＋顧問(Opus)決策<br>= <b style="color:#1A1A1A;background:#FFD400;padding:1px 8px">省 85% 成本</b> 💰</div>
""", "4/8"),
 # 5 Hooks — Surprised Pikachu（1893² 正方，object-fit cover 不留白、置中）
 ("m5_hooks", f"""
  <div class="hd"><span class="idx">④</span> <span class="y">Hooks</span> = 出菜口的品管員</div>
  <div class="big" style="top:245px;left:60px;width:960px;font-size:48px;">以為 <span class="r">exit 1</span> 就擋下危險指令…</div>
  <div class="frame" style="position:absolute;top:430px;left:250px;width:580px;height:365px;overflow:hidden;background:#fff;"><img src="{M}/pikachu.jpg" style="width:580px;height:auto;margin-top:-215px;"></div>
  <div class="big" style="top:895px;left:60px;width:960px;font-size:54px;">結果它<span class="r">默默放行</span> 😲</div>
  <div class="sub" style="top:1060px;left:60px;width:960px;font-size:40px;">擋動作要用 <b style="color:#1A1A1A;background:#FFD400;padding:1px 8px">exit 2</b>，不是 exit 1<br>——超多人在這踩雷</div>
""", "5/8"),
 # 6 Caching — Expanding Brain（857x1202 原比例，文字放左側白區）
 ("m6_caching", f"""
  <div class="hd" style="font-size:44px;"><span class="idx">⑤</span> <span class="y">Prompt Caching</span> = 水電費分時段</div>
  <img src="{M}/brain.jpg" class="frame" style="position:absolute;top:205px;left:640px;width:388px;height:1090px;object-fit:cover;object-position:right center;">
  <div class="ov" style="top:300px;left:75px;width:520px;font-size:42px;">每次都重付<br>全額 token 💸</div>
  <div class="ov" style="top:560px;left:75px;width:520px;font-size:42px;">開快取：<br><span class="r">$3 → $0.30</span></div>
  <div class="ov" style="top:820px;left:75px;width:520px;font-size:42px;">10 杯咖啡<br>只付 1 杯 ☕</div>
  <div class="ov" style="top:1080px;left:75px;width:520px;font-size:38px;">繁中別壓縮<br>(LLMLingua 會壞) 🌌</div>
""", "6/8"),
 # 7 速查表
 ("m7_table", f"""
  <div class="hd">5 個比喻，<span class="y">一張帶走</span> 📌</div>
  <div class="trow" style="top:220px;"><div class="a">CLAUDE.md</div><div class="b">員工手冊（60 行剛好）</div></div>
  <div class="trow" style="top:352px;"><div class="a">Skills</div><div class="b">抽屜手冊（標籤要準）</div></div>
  <div class="trow" style="top:484px;"><div class="a">Subagents</div><div class="b">派助理（最多 4 個並行）</div></div>
  <div class="trow" style="top:616px;"><div class="a">Hooks</div><div class="b">品管員（exit 2 才擋得住）</div></div>
  <div class="trow" style="top:748px;"><div class="a">Caching</div><div class="b">水電費分時段（省 ~90%）</div></div>
  <div class="big" style="top:940px;left:60px;width:960px;font-size:46px;"><span class="y">存這張</span>，週末照著設定就好</div>
  <div class="emo" style="top:1070px;font-size:150px;">🗂️</div>
""", "7/8"),
 # 8 CTA
 ("m8_cta", f"""
  <div class="hd" style="font-size:54px;">看懂了？<span class="r">換你了</span> 👇</div>
  <div class="big" style="top:230px;left:70px;width:940px;font-size:44px;line-height:1.5;text-align:left;">🏷️ 傳給那個「想學 AI 卻<br>&nbsp;&nbsp;&nbsp;&nbsp;卡在英文術語」的朋友<br><br>📌 收藏這篇，週末花 13 分鐘<br>&nbsp;&nbsp;&nbsp;&nbsp;把 Claude Code 裝好</div>
  <div class="big" style="top:640px;left:60px;width:960px;font-size:42px;">💬 留言「<span class="r">比喻</span>」，我把<br>完整 61 張簡報傳給你</div>
  <div class="bubble" style="top:840px;">「比喻」</div>
  <div class="sub" style="top:1090px;left:60px;width:960px;font-size:30px;">🐿️ 範例：把公開技術文章整理成白話迷因</div>
""", "8/8", False),
]

if __name__=="__main__":
    import sys; only=sys.argv[1:] or None
    print(f"=== claude-code-bp 迷因輪播 v2 ({W}x{H}) ===")
    for c in CARDS:
        if only and not any(k in c[0] for k in only): continue
        card(*c)
    print("out:",PROJ)
