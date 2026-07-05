#!/usr/bin/env python3
"""now6pm · editorial variant 渲染腳本（1080×1350 · 4:5 直式）
────────────────────────────────────────────────────────────
方向「Navy Editorial」：雜誌編輯骨架 × 深夜藍焰。
封面/CTA 走深色攝影感 + Q版人物；內容卡走冷淺藍灰編輯版面。

風格照 render_template.py 慣例：CARDS 陣列 + HTML 模板字串 + Chrome headless。

★ 這支是 editorial 風格「引擎示範」，不是通用預設。要用在自己品牌上，改三處：
  1) OUT     → 你的輸出資料夾（下方預設是相對路徑 ./out）。
  2) 角色資產自備：本 repo **不含 now6pm 人物圖**（個人肖像資產）。CARDS 引用的
     assets/character/ 三件套（hero + poses/ + expressions/）請自備，並先過「資產入庫閘」
     （scripts/asset_prep.py 入庫 + scripts/halo_check.py 判定，見 SKILL.md「🗂 資產入庫閘」
     與 references/visual-qa-gate.md）確認任何底色上零白暈、零切腳。缺圖時該卡的 <img> 會空白。
  3) FOOTER 的 handle（下方 @denniswei1310 是 now6pm 品牌示例）→ 換成你自己的。

卡型（type）：
  cover    v3b 版式：文字左 / 人物右全身 + SVG 藍焰 + 主題 props 層 + vignette/grain
  audience 淺底 + 明體標 + 螢光筆 + 白卡 ✗ 痛點清單 + 深 navy callout 金句
  step     數字圓 badge + kicker + 明體標 + 白色圓角清單卡（左藍豎線）×2–4
           （可選底部 callout；可選右下角小角色圖 expressions/ 之一）
  quote    深 navy 全底 + 細框卡 + 置中明體金句 +「」金色 + 導流句
  cta      深底 + 人物（poses/）+ 玻璃卡 + 橘紅圓角按鈕視覺 + 留言關鍵字

用法：
  python3 render_editorial.py                # 全部
  python3 render_editorial.py 01 cover        # 只跑名字含這些關鍵字的卡
"""
import subprocess
from pathlib import Path

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
W, H = 1080, 1350

# 輸出資料夾。預設輸出到本腳本旁的 ./out；要換專案改這裡即可。
OUT = Path(__file__).parent / "out"
OUT.mkdir(parents=True, exist_ok=True)

# 人物資產庫（brand pack 內；file:// 絕對路徑）
# ⚠️ 角色資產自備：本 repo 不含 now6pm 人物圖，請把自備的三件套放到 assets/character/
#    （先過資產入庫閘，見檔頭說明）。
CHAR = Path(__file__).parent / "assets" / "character"
def cf(rel): return f"file://{CHAR}/{rel}"          # character file url

# ── 色票（direction-1/palette.md 定稿，勿改）────────────────────
ROOT_VARS = """
  --navy:#14233B; --navy2:#1F3252; --milk:#EEF3F8;
  --paper:#E7EDF3; --card:#FBFDFF; --ink:#1B2636; --hl:#C9E0F7;
  --blue:#60A5FA; --blue-dot:#4A8FE7; --gold:#E9C58A; --rust:#C4400C;
  --gray:#8FA3C2;
  --serif:'Noto Serif TC','Songti TC',serif;
  --sans:'Noto Sans TC','PingFang TC',sans-serif;
"""
IMPORT = ("@import url('https://fonts.googleapis.com/css2?"
          "family=Noto+Serif+TC:wght@700;900&"
          "family=Noto+Sans+TC:wght@400;500;700&display=swap');")

FOOTER = """<div class="footer">
    <div class="brand"><span class="dot"></span><span class="wm">now<span>6pm</span></span></div>
    <div class="handle">@denniswei1310</div>
  </div>"""

# 封面「藍焰」簽名母題（固定，base 層）＋主題 props（可抽換）
FLAME_DEFS = """
    <defs>
      <linearGradient id="flame" x1="0" y1="1" x2="0" y2="0">
        <stop offset="0" stop-color="#1B57B8" stop-opacity=".58"/>
        <stop offset=".55" stop-color="#3E7FE0" stop-opacity=".36"/>
        <stop offset="1" stop-color="#7FB4FF" stop-opacity=".10"/>
      </linearGradient>
      <linearGradient id="flame2" x1="0" y1="1" x2="0" y2="0">
        <stop offset="0" stop-color="#123E86" stop-opacity=".52"/>
        <stop offset="1" stop-color="#5E9BF0" stop-opacity=".06"/>
      </linearGradient>
      <linearGradient id="tableFade" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0" stop-color="#4A8FE7" stop-opacity="0"/>
        <stop offset=".45" stop-color="#4A8FE7" stop-opacity=".34"/>
        <stop offset="1" stop-color="#4A8FE7" stop-opacity=".55"/>
      </linearGradient>
      <filter id="soft" x="-40%" y="-40%" width="180%" height="180%"><feGaussianBlur stdDeviation="14"/></filter>
      <filter id="soft2" x="-40%" y="-40%" width="180%" height="180%"><feGaussianBlur stdDeviation="4"/></filter>
    </defs>
    <g filter="url(#soft)">
      <path fill="url(#flame)" d="M888 1220 C700 1165 680 1000 740 860 C778 774 760 684 722 624 C812 664 860 744 866 812 C916 720 898 626 864 550 C972 626 1026 748 1010 866 C1058 828 1078 762 1072 704 C1124 810 1130 954 1074 1058 C1036 1132 962 1206 888 1220 Z"/>
      <path fill="url(#flame2)" d="M590 1230 C500 1152 510 1036 562 950 C592 900 588 840 568 802 C636 840 662 902 660 950 C698 890 690 828 670 780 C750 846 780 944 756 1030 C740 1108 680 1194 590 1230 Z"/>
    </g>
"""

# 主題 props：指揮官戰情桌（全息透視網格 + 3 隻扛文件小機器人）——預設主題
PROPS_COMMANDER = """
    <g stroke="url(#tableFade)" stroke-width="2" opacity=".8">
      <line x1="140" y1="1050" x2="-60" y2="1350"/><line x1="330" y1="1050" x2="210" y2="1350"/>
      <line x1="520" y1="1050" x2="480" y2="1350"/><line x1="710" y1="1050" x2="750" y2="1350"/>
      <line x1="900" y1="1050" x2="1020" y2="1350"/><line x1="1060" y1="1050" x2="1240" y2="1350"/>
      <line x1="60" y1="1090" x2="1080" y2="1090"/><line x1="20" y1="1150" x2="1080" y2="1150"/>
      <line x1="-30" y1="1230" x2="1080" y2="1230"/><line x1="-80" y1="1330" x2="1080" y2="1330"/>
    </g>
    <ellipse cx="440" cy="1120" rx="360" ry="58" fill="#4A8FE7" opacity=".12" filter="url(#soft)"/>
    <g stroke="#7FB4FF" stroke-width="3.5" fill="none" opacity=".5" stroke-linecap="round" stroke-linejoin="round" filter="url(#soft2)">
      <g transform="translate(92,952)"><rect x="0" y="30" width="66" height="58" rx="14"/><rect x="10" y="-14" width="46" height="38" rx="12"/><circle cx="24" cy="4" r="4" fill="#7FB4FF"/><circle cx="44" cy="4" r="4" fill="#7FB4FF"/><line x1="33" y1="-14" x2="33" y2="-26"/><circle cx="33" cy="-30" r="4"/><rect x="-26" y="34" width="24" height="34" rx="6"/><line x1="12" y1="88" x2="12" y2="106"/><line x1="52" y1="88" x2="52" y2="106"/></g>
      <g transform="translate(244,986)"><rect x="0" y="26" width="58" height="52" rx="13"/><rect x="8" y="-14" width="42" height="34" rx="11"/><circle cx="21" cy="2" r="3.5" fill="#7FB4FF"/><circle cx="39" cy="2" r="3.5" fill="#7FB4FF"/><line x1="29" y1="-14" x2="29" y2="-24"/><circle cx="29" cy="-28" r="3.5"/><rect x="-24" y="30" width="22" height="30" rx="5"/><line x1="11" y1="78" x2="11" y2="94"/><line x1="47" y1="78" x2="47" y2="94"/></g>
      <g transform="translate(376,1014)"><rect x="0" y="22" width="50" height="46" rx="12"/><rect x="7" y="-12" width="36" height="30" rx="10"/><circle cx="18" cy="2" r="3" fill="#7FB4FF"/><circle cx="33" cy="2" r="3" fill="#7FB4FF"/><line x1="25" y1="-12" x2="25" y2="-21"/><circle cx="25" cy="-24" r="3"/><rect x="-21" y="26" width="19" height="26" rx="5"/><line x1="9" y1="68" x2="9" y2="82"/><line x1="41" y1="68" x2="41" y2="82"/></g>
    </g>
"""

# ════════════════════════════════════════════════════════════
#  模板外殼（每型一個完整 <html>）· 用 {{TOKEN}} 佔位再 .replace()
# ════════════════════════════════════════════════════════════

COVER = """<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8"><style>
""" + IMPORT + """
:root{""" + ROOT_VARS + """}
*{margin:0;padding:0;box-sizing:border-box}
html,body{width:1080px;height:1350px}
.stage{position:relative;width:1080px;height:1350px;overflow:hidden;
  background:radial-gradient(110% 80% at 84% 76%, #1D3457 0%, rgba(29,52,87,0) 55%),
    radial-gradient(80% 55% at 8% 100%, #0F1E36 0%, rgba(15,30,54,0) 60%),
    linear-gradient(160deg,#16273F 0%,#14233B 50%,#0D1930 100%);}
.scene{position:absolute;inset:0;pointer-events:none}
.darkzone{position:absolute;inset:0;pointer-events:none;z-index:4;
  background:radial-gradient(74% 52% at 20% 22%, rgba(6,12,24,.78) 0%, rgba(6,12,24,.30) 55%, rgba(6,12,24,0) 74%)}
.vignette{position:absolute;inset:0;pointer-events:none;z-index:4;
  background:radial-gradient(120% 96% at 46% 40%, rgba(0,0,0,0) 50%, rgba(5,11,22,.72) 100%)}
.grain{position:absolute;inset:0;pointer-events:none;opacity:.05;mix-blend-mode:overlay;z-index:4;
  background-image:url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='140' height='140'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='2' stitchTiles='stitch'/></filter><rect width='100%25' height='100%25' filter='url(%23n)'/></svg>")}
.hero{position:absolute;z-index:3;{{HERO_CSS}}
  filter:drop-shadow(0 24px 48px rgba(3,8,18,.55)) drop-shadow(0 0 38px rgba(74,143,231,.30))}
.pill{position:absolute;top:60px;right:70px;z-index:6;font-family:var(--sans);font-weight:700;
  font-size:22px;letter-spacing:.16em;color:var(--milk);background:rgba(96,165,250,.16);
  border:1px solid rgba(96,165,250,.45);padding:9px 20px;border-radius:999px;backdrop-filter:blur(4px)}
.copy{position:absolute;left:76px;top:158px;max-width:730px;z-index:5}
.kicker{font-family:var(--sans);font-weight:700;font-size:29px;letter-spacing:.02em;color:var(--gold)}
.title{font-family:var(--serif);font-weight:900;font-size:124px;line-height:1.15;color:var(--milk);
  letter-spacing:.01em;margin-top:22px;text-wrap:pretty;text-shadow:0 4px 30px rgba(4,10,22,.65)}
.title .hi-gold{color:var(--gold)} .title .hi-blue{color:var(--blue)}
.divider{width:120px;height:5px;background:var(--gold);border-radius:3px;margin:36px 0 26px}
.sub{font-family:var(--sans);font-weight:500;font-size:32px;line-height:1.62;color:#C7D5E8;
  max-width:430px;text-wrap:pretty;text-shadow:0 2px 18px rgba(4,10,22,.6)}
.sub b{color:var(--blue);font-weight:700}
.footer{position:absolute;left:70px;right:70px;bottom:54px;z-index:6;display:flex;align-items:center;
  justify-content:space-between;border-top:1px solid rgba(143,163,194,.30);padding-top:24px}
.brand{display:flex;align-items:center;gap:12px;font-family:var(--sans);font-size:26px;color:var(--milk)}
.brand .dot{width:14px;height:14px;border-radius:50%;background:var(--blue-dot);box-shadow:0 0 14px rgba(74,143,231,.9)}
.brand .wm{font-weight:700} .brand .wm span{color:var(--blue-dot)}
.handle{font-family:var(--sans);font-size:24px;color:var(--gray);letter-spacing:.02em}
</style></head><body>
<div class="stage">
  <svg class="scene" width="1080" height="1350" viewBox="0 0 1080 1350" fill="none" xmlns="http://www.w3.org/2000/svg">
""" + FLAME_DEFS + """{{PROPS}}
  </svg>
  <img class="hero" src="{{HERO}}" alt="">
  <div class="darkzone"></div><div class="vignette"></div><div class="grain"></div>
  <div class="pill">{{PAGE}}</div>
  <div class="copy">
    <div class="kicker">{{KICKER}}</div>
    <div class="title">{{TITLE}}</div>
    <div class="divider"></div>
    <div class="sub">{{SUB}}</div>
  </div>
  """ + FOOTER + """
</div></body></html>"""

# ── 淺色編輯卡共用外殼（audience / step 共用 CSS，內容用 {{BODY}}）──
PAPER = """<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8"><style>
""" + IMPORT + """
:root{""" + ROOT_VARS + """}
*{margin:0;padding:0;box-sizing:border-box}
html,body{width:1080px;height:1350px}
.stage{position:relative;width:1080px;height:1350px;background:var(--paper);overflow:hidden;
  padding:88px 84px 78px;display:flex;flex-direction:column}
.pill{position:absolute;top:60px;right:84px;font-family:var(--sans);font-weight:700;font-size:22px;
  letter-spacing:.16em;color:#3C5170;background:rgba(74,143,231,.12);border:1px solid rgba(74,143,231,.35);
  padding:9px 20px;border-radius:999px}
.main{flex:1;display:flex;flex-direction:column;padding-top:22px}
.main.center{justify-content:center;padding-top:0}
.head{display:flex;align-items:center;gap:20px}
.badge{width:66px;height:66px;border-radius:50%;background:var(--navy);color:#fff;font-family:var(--serif);
  font-weight:700;font-size:34px;display:flex;align-items:center;justify-content:center;flex:0 0 66px}
.kicker{font-family:var(--sans);font-weight:700;font-size:27px;color:#3C5170;letter-spacing:.01em}
.title{font-family:var(--serif);font-weight:900;font-size:76px;line-height:1.24;color:var(--ink);
  margin-top:26px;text-wrap:pretty}
.title.sm{font-size:66px}
.title .mark{background:linear-gradient(transparent 58%, var(--hl) 58%);padding:0 6px;border-radius:2px}
/* 白卡 ✗ 痛點清單 */
.xlist{margin-top:38px;display:flex;flex-direction:column;gap:20px}
.xcard{background:var(--card);border-radius:18px;padding:28px 32px;display:flex;gap:22px;align-items:flex-start;
  box-shadow:0 8px 22px rgba(20,35,59,.08)}
.xcard .x{font-family:var(--sans);color:var(--rust);font-weight:900;font-size:38px;line-height:1.15;flex:0 0 auto}
.xcard .t{font-family:var(--sans);font-weight:500;font-size:30px;line-height:1.5;color:#2B3A50}
.xcard .t b{color:var(--rust);font-weight:700}
/* 白色圓角清單卡（左藍豎線） */
.cards{margin-top:40px;display:flex;flex-direction:column;gap:20px}
.cards.tight{gap:16px;margin-top:32px}
.item{background:var(--card);border-radius:20px;padding:28px 32px;display:flex;gap:28px;align-items:flex-start;
  box-shadow:0 10px 26px rgba(20,35,59,.09);border-left:6px solid var(--blue)}
.item .lbl{font-family:var(--serif);font-weight:700;font-size:38px;color:var(--navy);flex:0 0 150px;line-height:1.2}
.item .lbl small{display:block;font-family:var(--sans);font-weight:700;font-size:18px;color:var(--blue-dot);
  letter-spacing:.14em;margin-top:6px}
.item .desc{font-family:var(--sans);font-weight:500;font-size:28px;line-height:1.5;color:#2B3A50;padding-top:4px}
.item .desc b{color:var(--rust);font-weight:700}
.item.compact{padding:22px 30px} .item.compact .lbl{flex:0 0 120px;font-size:32px}
.item.compact .desc{font-size:26px;line-height:1.42}
/* 數字對比卡（stat row） */
.stats{margin-top:40px;display:flex;flex-direction:column;gap:20px}
.stat{background:var(--card);border-radius:20px;padding:26px 36px;display:flex;align-items:center;gap:32px;
  box-shadow:0 10px 26px rgba(20,35,59,.09);border-left:6px solid var(--rust)}
.stat .big{font-family:var(--serif);font-weight:900;font-size:72px;color:var(--rust);line-height:1;flex:0 0 300px;
  text-align:center;letter-spacing:-1px}
.stat .cap{font-family:var(--sans);font-weight:500;font-size:29px;line-height:1.45;color:#2B3A50}
.stat .cap b{color:var(--navy);font-weight:700}
/* 深色 callout 金句 */
.callout{margin-top:30px;background:radial-gradient(120% 130% at 88% 0%, #26436F 0%, rgba(38,67,111,0) 55%),var(--navy2);
  border-radius:22px;padding:40px 46px;position:relative;overflow:hidden}
.callout .q{font-family:var(--serif);font-weight:700;font-size:48px;line-height:1.42;color:#F0F5FB;text-wrap:pretty}
.callout .q .g{color:var(--gold)}
.callout .cite{font-family:var(--sans);font-weight:500;font-size:23px;color:var(--gray);margin-top:14px}
/* 右下角小角色（不搶戲） */
.mini{position:absolute;right:56px;bottom:126px;z-index:2;pointer-events:none;
  filter:drop-shadow(0 12px 24px rgba(20,35,59,.20))}
.footer{position:relative;z-index:3;display:flex;align-items:center;justify-content:space-between;
  border-top:1px solid rgba(60,81,112,.22);padding-top:22px;margin-top:26px}
.brand{display:flex;align-items:center;gap:12px;font-family:var(--sans);font-size:26px;color:var(--navy)}
.brand .dot{width:14px;height:14px;border-radius:50%;background:var(--blue-dot)}
.brand .wm{font-weight:700} .brand .wm span{color:var(--blue-dot)}
.handle{font-family:var(--sans);font-size:24px;color:#7A8CA6;letter-spacing:.02em}
</style></head><body>
<div class="stage">
  <div class="pill">{{PAGE}}</div>
  <div class="main {{CENTER}}">{{BODY}}</div>
  {{MINI}}
  """ + FOOTER + """
</div></body></html>"""

QUOTE = """<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8"><style>
""" + IMPORT + """
:root{""" + ROOT_VARS + """}
*{margin:0;padding:0;box-sizing:border-box}
html,body{width:1080px;height:1350px}
.stage{position:relative;width:1080px;height:1350px;overflow:hidden;
  background:radial-gradient(120% 80% at 50% 12%, #1E3557 0%, rgba(30,53,87,0) 58%),
    linear-gradient(165deg,#16273F 0%,#14233B 52%,#0D1930 100%)}
.grain{position:absolute;inset:0;pointer-events:none;opacity:.05;mix-blend-mode:overlay;
  background-image:url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='140' height='140'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='2' stitchTiles='stitch'/></filter><rect width='100%25' height='100%25' filter='url(%23n)'/></svg>")}
.flame{position:absolute;left:50%;bottom:-40px;transform:translateX(-50%);width:520px;height:420px;
  background:radial-gradient(ellipse at bottom,#4A8FE7 0%,rgba(74,143,231,.28) 34%,transparent 70%);opacity:.22;filter:blur(30px)}
.pill{position:absolute;top:60px;right:70px;font-family:var(--sans);font-weight:700;font-size:22px;
  letter-spacing:.16em;color:var(--milk);background:rgba(96,165,250,.16);border:1px solid rgba(96,165,250,.45);
  padding:9px 20px;border-radius:999px}
.frame{position:absolute;left:96px;right:96px;top:210px;bottom:210px;border:1px solid rgba(96,165,250,.32);
  border-radius:28px;background:linear-gradient(160deg, rgba(23,38,64,.42) 0%, rgba(15,27,48,.30) 100%);
  display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;padding:70px 66px;
  box-shadow:inset 0 1px 0 rgba(160,190,240,.12)}
.qk{font-family:var(--sans);font-weight:700;font-size:26px;letter-spacing:.16em;color:var(--gold);margin-bottom:34px}
.q{font-family:var(--serif);font-weight:700;font-size:62px;line-height:1.5;color:var(--milk);text-wrap:pretty}
.q .qm{color:var(--gold)} .q .g{color:var(--gold)}
.cite{font-family:var(--sans);font-weight:500;font-size:26px;color:var(--gray);margin-top:40px;letter-spacing:.02em}
.lead{position:absolute;left:0;right:0;bottom:-96px;font-family:var(--sans);font-weight:700;font-size:29px;
  color:#C7D5E8;text-align:center}
.lead b{color:var(--blue)}
.footer{position:absolute;left:70px;right:70px;bottom:54px;display:flex;align-items:center;
  justify-content:space-between;border-top:1px solid rgba(143,163,194,.30);padding-top:24px}
.brand{display:flex;align-items:center;gap:12px;font-family:var(--sans);font-size:26px;color:var(--milk)}
.brand .dot{width:14px;height:14px;border-radius:50%;background:var(--blue-dot);box-shadow:0 0 14px rgba(74,143,231,.9)}
.brand .wm{font-weight:700} .brand .wm span{color:var(--blue-dot)}
.handle{font-family:var(--sans);font-size:24px;color:var(--gray);letter-spacing:.02em}
</style></head><body>
<div class="stage">
  <div class="flame"></div><div class="grain"></div>
  <div class="pill">{{PAGE}}</div>
  <div class="frame">
    <div class="qk">{{QK}}</div>
    <div class="q">{{QUOTE}}</div>
    <div class="cite">{{CITE}}</div>
    <div class="lead">{{LEAD}}</div>
  </div>
  """ + FOOTER + """
</div></body></html>"""

CTA = """<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8"><style>
""" + IMPORT + """
:root{""" + ROOT_VARS + """}
*{margin:0;padding:0;box-sizing:border-box}
html,body{width:1080px;height:1350px}
.stage{position:relative;width:1080px;height:1350px;overflow:hidden;
  background:radial-gradient(110% 76% at 22% 74%, #1D3457 0%, rgba(29,52,87,0) 56%),
    linear-gradient(160deg,#16273F 0%,#14233B 52%,#0D1930 100%)}
.grain{position:absolute;inset:0;pointer-events:none;opacity:.05;mix-blend-mode:overlay;z-index:4;
  background-image:url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='140' height='140'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='2' stitchTiles='stitch'/></filter><rect width='100%25' height='100%25' filter='url(%23n)'/></svg>")}
.flame{position:absolute;right:80px;bottom:-40px;width:460px;height:420px;
  background:radial-gradient(ellipse at bottom,#4A8FE7 0%,rgba(74,143,231,.26) 34%,transparent 70%);opacity:.20;filter:blur(28px)}
/* 人物：右下站立，佔 45% 高，clip 掉素材底部小字 */
.heroWrap{position:absolute;right:44px;bottom:52px;width:{{CW}}px;height:{{CH}}px;overflow:hidden;z-index:3;
  filter:drop-shadow(0 22px 44px rgba(3,8,18,.5)) drop-shadow(0 0 32px rgba(74,143,231,.26))}
.heroWrap img{width:100%;display:block}
.pill{position:absolute;top:60px;right:70px;z-index:6;font-family:var(--sans);font-weight:700;font-size:22px;
  letter-spacing:.16em;color:var(--milk);background:rgba(96,165,250,.16);border:1px solid rgba(96,165,250,.45);
  padding:9px 20px;border-radius:999px;backdrop-filter:blur(4px)}
/* 玻璃卡 */
.glass{position:absolute;left:64px;top:190px;width:640px;z-index:5;padding:48px 50px 44px;border-radius:30px;
  background:linear-gradient(160deg, rgba(23,38,64,.80) 0%, rgba(15,27,48,.88) 100%);
  border:1px solid rgba(96,165,250,.30);box-shadow:0 24px 70px rgba(4,10,22,.55), inset 0 1px 0 rgba(160,190,240,.14);
  backdrop-filter:blur(14px) saturate(115%)}
.glass .kicker{font-family:var(--sans);font-weight:700;font-size:27px;color:var(--gold);letter-spacing:.02em}
.glass .title{font-family:var(--serif);font-weight:900;font-size:70px;line-height:1.22;color:var(--milk);
  margin-top:16px;text-wrap:pretty}
.glass .title .hi-blue{color:var(--blue)}
.glass .sub{font-family:var(--sans);font-weight:500;font-size:29px;line-height:1.55;color:#C7D5E8;margin-top:20px}
.btn{display:inline-block;margin-top:34px;background:var(--rust);color:#fff;font-family:var(--sans);font-weight:700;
  font-size:38px;padding:20px 44px;border-radius:18px;box-shadow:0 14px 30px rgba(196,64,12,.42)}
.kw{position:absolute;left:64px;bottom:150px;width:600px;z-index:5;font-family:var(--sans);font-weight:500;
  font-size:26px;line-height:1.55;color:#AFC0DA}
.kw b{color:var(--blue);font-weight:700}
.footer{position:absolute;left:70px;right:70px;bottom:54px;z-index:6;display:flex;align-items:center;
  justify-content:space-between;border-top:1px solid rgba(143,163,194,.30);padding-top:24px}
.brand{display:flex;align-items:center;gap:12px;font-family:var(--sans);font-size:26px;color:var(--milk)}
.brand .dot{width:14px;height:14px;border-radius:50%;background:var(--blue-dot);box-shadow:0 0 14px rgba(74,143,231,.9)}
.brand .wm{font-weight:700} .brand .wm span{color:var(--blue-dot)}
.handle{font-family:var(--sans);font-size:24px;color:var(--gray);letter-spacing:.02em}
</style></head><body>
<div class="stage">
  <div class="flame"></div>
  <div class="heroWrap"><img src="{{HERO}}" alt=""></div>
  <div class="grain"></div>
  <div class="pill">{{PAGE}}</div>
  <div class="glass">
    <div class="kicker">{{KICKER}}</div>
    <div class="title">{{TITLE}}</div>
    <div class="sub">{{SUB}}</div>
    <div class="btn">{{BTN}}</div>
  </div>
  <div class="kw">{{KW}}</div>
  """ + FOOTER + """
</div></body></html>"""

# ── 內容 builder ─────────────────────────────────────────────
def xlist(items):
    rows = "".join(f'<div class="xcard"><div class="x">✗</div><div class="t">{t}</div></div>' for t in items)
    return f'<div class="xlist">{rows}</div>'

def steplist(items, tight=False, compact=False):
    cls = "cards tight" if tight else "cards"
    ic = "item compact" if compact else "item"
    rows = ""
    for it in items:
        small = f'<small>{it["small"]}</small>' if it.get("small") else ""
        rows += (f'<div class="{ic}"><div class="lbl">{it["lbl"]}{small}</div>'
                 f'<div class="desc">{it["desc"]}</div></div>')
    return f'<div class="{cls}">{rows}</div>'

def statlist(items):
    rows = "".join(f'<div class="stat"><div class="big">{it["big"]}</div><div class="cap">{it["cap"]}</div></div>'
                   for it in items)
    return f'<div class="stats">{rows}</div>'

def callout(q, cite=""):
    c = f'<div class="cite">{cite}</div>' if cite else ""
    return f'<div class="callout"><div class="q">{q}</div>{c}</div>'

def head(badge, kicker):
    b = f'<div class="badge">{badge}</div>' if badge else ""
    return f'<div class="head">{b}<div class="kicker">{kicker}</div></div>'

def mini(rel, w=150):
    return f'<img class="mini" src="{cf(rel)}" style="width:{w}px" alt="">'

# ════════════════════════════════════════════════════════════
#  8 張實戰樣卡（Fable Commander 介紹）· 文案已過 de-ai §1 機械層
# ════════════════════════════════════════════════════════════
CARDS = [
 {"name":"01_cover","type":"cover","page":"01 / 08",
  "kicker":"— AI 指揮官工作法",
  "title":'最貴的<span class="hi-gold">腦</span>，<br>只出一張<span class="hi-blue">嘴</span>。',
  "sub":'Fable 只負責<b>規劃 × 審查 × 決策</b>，研究和粗活全外包給便宜模型。',
  "hero":cf("hero-pointing-up-alpha.png"),
  "hero_css":"right:-100px;bottom:112px;height:890px;",
  "props":PROPS_COMMANDER},

 {"name":"02_audience","type":"audience","page":"02 / 08",
  "badge":"", "kicker":"— 這篇給誰",
  "title":'你的 AI 帳單，<span class="mark">正在偷偷失血</span>',
  "xlist":["一個研究專案，token 燒掉大半個月額度",
           "context 塞到爆，模型開始忘東忘西",
           "AI 寫完自己改，幫自己作業打分永遠給高分"],
  "callout_q":'把<span class="g">寫的人</span>，跟<span class="g">檢查的人</span>分開。',
  "callout_cite":"這是整套流程的第一塊骨牌"},

 {"name":"03_step1","type":"step","page":"03 / 08",
  "badge":"①", "kicker":"指揮官不下海做工",
  "title":'指揮官，只做<span class="mark">三件事</span>',
  "items":[
    {"lbl":"規劃","small":"PLAN","desc":"拆任務、定驗收標準，畫好整張作戰地圖。"},
    {"lbl":"審查","small":"REVIEW","desc":"讀 subagent 交回的東西，抓錯、要求重做。"},
    {"lbl":"拍板","small":"DECIDE","desc":"決策點停下來，由最貴的腦做最後判斷。"}],
  "callout_q":'判斷力稀缺的活，才留給<span class="g">最貴的腦</span>。',
  "callout_cite":"其餘吞吐量大的粗活，全部下放"},

 {"name":"04_step2","type":"step","page":"04 / 08",
  "badge":"②", "kicker":"省 token 的四個開關",
  "title":'帳單，<span class="mark">四層一起省</span>',
  "items":[
    {"lbl":"單價","desc":"粗活改用 Sonnet／Haiku，同樣的字便宜 3~10 倍。"},
    {"lbl":"雪球","desc":"subagent 各開小 context，讀完就丟，不重讀對話。"},
    {"lbl":"平行","desc":"研究題目同時開跑，一個晚上抵三天。"},
    {"lbl":"品質","desc":"寫審分離，錯誤在便宜迴圈裡就被抓掉。"}],
  "callout_q":'四層<span class="g">一起踩</span>，帳單才會<span class="g">真的</span>掉。',
  "callout_cite":"少踩一層，都只是省個心安"},

 {"name":"05_step3","type":"step","page":"05 / 08",
  "badge":"③", "kicker":"同一份研究，實測",
  "title":'帳單砍到 <span class="mark">1/4 ~ 1/8</span>',
  "stats":[
    {"big":"¼~⅛","cap":'<b>帳面成本</b>，跟全塞給 Fable 自己做比。'},
    {"big":"5×","cap":'研究並行，同一份專案<b>快五倍</b>跑完。'},
    {"big":"85%","cap":'token 走 <b>Sonnet 價</b>，不是旗艦價。'}],
  "callout_q":'又<span class="g">便宜</span>、又<span class="g">快</span>、驗證還更準。',
  "callout_cite":""},

 {"name":"06_quote","type":"quote","page":"06 / 08",
  "qk":"LOOP ENGINEERING",
  "quote":'<span class="qm">「</span>寫程式的模型，<br>幫自己作業打分時，<br><span class="g">太仁慈了。</span><span class="qm">」</span>',
  "cite":"—— Addy Osmani · Loop Engineering",
  "lead":'所以驗證，一定要換<b>一顆乾淨的腦</b>。'},

 {"name":"07_when_not","type":"audience","page":"07 / 08",
  "badge":"", "kicker":"— 誠實說，它不是萬用解",
  "title":'這三種情況，<span class="mark">別走這套</span>',
  "xlist":["任務很小：一個好 prompt 一次做完更快",
           "沒法客觀驗收：純主觀創作，沒有硬條件可驗",
           "token 預算很緊：這流程要先燒一波才回本"],
  "callout_q":'夠<span class="g">大</span>、可<span class="g">驗</span>、值得，才值得派兵。',
  "callout_cite":"殺雞用牛刀，也是一種浪費",
  "mini":("expressions/07_thinking-confused.png", 165)},

 {"name":"08_cta","type":"cta","page":"08 / 08",
  "kicker":"一顆腦做到底，又貴又慢",
  "title":'想學這套<br><span class="hi-blue">指揮官流程</span>？',
  "sub":"完整 SOP 加開源專案，我整理好了。",
  "btn":"留言「指揮官」",
  "kw":'我把<b>完整指南</b>私訊給你，<br>開源連結放<b>留言區</b>。',
  "hero":cf("poses/05_cheering.png"),
  "cw":392, "ch":560},   # 275×415 → 寬 392 等比放大約 1.42×，ch 560=height×0.93 clip 掉底部小字
]

# ── dispatch ─────────────────────────────────────────────────
def build(c):
    t = c["type"]
    if t == "cover":
        return (COVER.replace("{{HERO_CSS}}", c["hero_css"]).replace("{{PROPS}}", c["props"])
                .replace("{{HERO}}", c["hero"]).replace("{{PAGE}}", c["page"])
                .replace("{{KICKER}}", c["kicker"]).replace("{{TITLE}}", c["title"])
                .replace("{{SUB}}", c["sub"]))
    if t == "audience":
        body = head(c.get("badge",""), c["kicker"])
        body += f'<div class="title">{c["title"]}</div>'
        body += xlist(c["xlist"])
        if c.get("callout_q"):
            body += callout(c["callout_q"], c.get("callout_cite",""))
        m = mini(c["mini"][0], c["mini"][1]) if c.get("mini") else ""
        center = "" if c.get("mini") else "center"   # 有小角色→靠上讓出下方，無→垂直置中
        return (PAPER.replace("{{PAGE}}", c["page"]).replace("{{CENTER}}", center)
                .replace("{{BODY}}", body).replace("{{MINI}}", m))
    if t == "step":
        title_cls = "title sm" if c.get("tight") else "title"
        body = head(c.get("badge",""), c["kicker"])
        body += f'<div class="{title_cls}">{c["title"]}</div>'
        if c.get("stats"):
            body += statlist(c["stats"])
        else:
            body += steplist(c["items"], tight=c.get("tight",False), compact=c.get("compact",False))
        if c.get("callout_q"):
            body += callout(c["callout_q"], c.get("callout_cite",""))
        m = mini(c["mini"][0], c["mini"][1]) if c.get("mini") else ""
        center = "" if c.get("mini") else "center"
        return (PAPER.replace("{{PAGE}}", c["page"]).replace("{{CENTER}}", center)
                .replace("{{BODY}}", body).replace("{{MINI}}", m))
    if t == "quote":
        return (QUOTE.replace("{{PAGE}}", c["page"]).replace("{{QK}}", c["qk"])
                .replace("{{QUOTE}}", c["quote"]).replace("{{CITE}}", c["cite"])
                .replace("{{LEAD}}", c["lead"]))
    if t == "cta":
        return (CTA.replace("{{HERO}}", c["hero"]).replace("{{CW}}", str(c["cw"]))
                .replace("{{CH}}", str(c["ch"])).replace("{{PAGE}}", c["page"])
                .replace("{{KICKER}}", c["kicker"]).replace("{{TITLE}}", c["title"])
                .replace("{{SUB}}", c["sub"]).replace("{{BTN}}", c["btn"]).replace("{{KW}}", c["kw"]))
    raise ValueError(f"unknown card type: {t}")

def render(c):
    n = c["name"]; hp = OUT/f"{n}.html"; pp = OUT/f"{n}.png"
    hp.write_text(build(c), encoding="utf-8"); print(f"  {n} ", end="", flush=True)
    r = subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--no-sandbox", "--hide-scrollbars",
        "--allow-file-access-from-files", "--force-device-scale-factor=1",
        f"--window-size={W},{H}", f"--screenshot={pp}", f"file://{hp}"],
        capture_output=True, text=True, timeout=90)
    print(f"✓ {pp.stat().st_size//1024}KB" if pp.exists() else f"✗ {r.stderr[-160:]}")

if __name__ == "__main__":
    import sys; only = sys.argv[1:] or None
    print(f"=== now6pm editorial ({W}x{H}) → {OUT} ===")
    for c in CARDS:
        if only and not any(k in c["name"] for k in only): continue
        render(c)
    print("out:", OUT)
