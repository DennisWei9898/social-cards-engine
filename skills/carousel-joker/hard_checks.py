#!/usr/bin/env python3
"""
carousel-joker 硬訊號自動檢查（render 後跑）
=================================================
把 carousel-joker 判準裡「機器可判」的項目抽出來自動化，讓 LLM joker 只留主觀項。
這是真硬訊號：同一套卡不同輪跑，結果一定一致（不像主觀分會漂）。

自動檢查：
  B1 張數      6–12（教育型 8–12）        ← 數 PNG 檔
  B4 尺寸      1080×1350（4:5 直式滿版）  ← 讀每張 PNG 解析度
  C3 Hashtag   ≤5、精準                   ← 數 caption 的 #
  B5 字級/字數  headline≥36px body≥24px、每張≤30 字  ← 只在給 --html 時驗（PNG 量不到字級）

用法：
  python3 hard_checks.py --cards <資料夾或glob> [--caption caption.md] [--html <html資料夾>]
退出碼：0＝全 PASS，1＝有 FAIL（可接進 CI / 過閘腳本）。
"""
import argparse, glob, json, os, re, subprocess, sys

TARGET_W, TARGET_H = 1080, 1350
CARD_MIN, CARD_MAX = 6, 12
HASHTAG_MAX = 5
HEADLINE_MIN_PX, BODY_MIN_PX = 36, 24
TEXT_MAX_CHARS = 30  # 每張文字上限（B5）


def png_size(path):
    """回傳 (w, h)。先試 Pillow，退回 macOS sips。"""
    try:
        from PIL import Image
        with Image.open(path) as im:
            return im.size
    except Exception:
        pass
    try:
        out = subprocess.check_output(
            ["sips", "-g", "pixelWidth", "-g", "pixelHeight", path],
            stderr=subprocess.DEVNULL, text=True)
        w = int(re.search(r"pixelWidth:\s*(\d+)", out).group(1))
        h = int(re.search(r"pixelHeight:\s*(\d+)", out).group(1))
        return (w, h)
    except Exception:
        return None


def collect_pngs(cards_arg):
    if os.path.isdir(cards_arg):
        files = sorted(glob.glob(os.path.join(cards_arg, "*.png")) +
                       glob.glob(os.path.join(cards_arg, "*.PNG")))
    else:
        files = sorted(glob.glob(cards_arg))
    return files


def check_cards(pngs):
    findings, ok = [], True
    n = len(pngs)
    if CARD_MIN <= n <= CARD_MAX:
        findings.append(("B1", "PASS", f"{n} 張（{CARD_MIN}–{CARD_MAX} 內）"))
    else:
        ok = False
        findings.append(("B1", "FAIL", f"{n} 張，超出 {CARD_MIN}–{CARD_MAX}（教育型建議 8–12）"))

    bad = []
    for p in pngs:
        size = png_size(p)
        name = os.path.basename(p)
        if size is None:
            bad.append(f"{name}:讀不到尺寸")
        elif size != (TARGET_W, TARGET_H):
            bad.append(f"{name}:{size[0]}x{size[1]}")
    if not bad:
        findings.append(("B4", "PASS", f"全部 {n} 張皆 {TARGET_W}x{TARGET_H}"))
    else:
        ok = False
        findings.append(("B4", "FAIL", f"非 {TARGET_W}x{TARGET_H}：" + "、".join(bad)))
    return findings, ok


def check_hashtags(caption):
    tags = re.findall(r"#\S+", caption or "")
    if len(tags) <= HASHTAG_MAX:
        return ("C3", "PASS", f"{len(tags)} 個（≤{HASHTAG_MAX}）"), True
    return ("C3", "FAIL", f"{len(tags)} 個，超過 {HASHTAG_MAX}：{' '.join(tags)}"), False


def check_html(html_dir):
    """B5：從 HTML/CSS 抓 font-size 與可見文字長度。給了 --html 才跑。"""
    files = sorted(glob.glob(os.path.join(html_dir, "*.html")) +
                   glob.glob(os.path.join(html_dir, "*.htm")))
    if not files:
        return [("B5", "SKIP", f"{html_dir} 無 html，字級/字數改由 joker 目視")], True
    findings, ok = [], True
    px_re = re.compile(r"font-size\s*:\s*(\d+(?:\.\d+)?)px", re.I)
    tag_re = re.compile(r"<[^>]+>")
    for f in files:
        name = os.path.basename(f)
        html = open(f, encoding="utf-8", errors="ignore").read()
        sizes = [float(x) for x in px_re.findall(html)]
        text = re.sub(r"\s+", "", tag_re.sub("", html))
        problems = []
        if sizes:
            if max(sizes) < HEADLINE_MIN_PX:
                problems.append(f"最大字級 {max(sizes):.0f}px < headline {HEADLINE_MIN_PX}px")
            if min(sizes) < BODY_MIN_PX:
                problems.append(f"最小字級 {min(sizes):.0f}px < body {BODY_MIN_PX}px")
        if len(text) > TEXT_MAX_CHARS:
            problems.append(f"純文字 {len(text)} 字 > {TEXT_MAX_CHARS}")
        if problems:
            ok = False
            findings.append(("B5", "FAIL", f"{name}：" + "；".join(problems)))
    if ok:
        findings.append(("B5", "PASS", f"{len(files)} 張 HTML 字級/字數皆達標"))
    return findings, ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cards", required=True, help="PNG 資料夾或 glob")
    ap.add_argument("--caption", help="caption 檔路徑或直接文字")
    ap.add_argument("--html", help="（可選）render 用的 HTML 資料夾，給了才驗 B5 字級/字數")
    a = ap.parse_args()

    pngs = collect_pngs(a.cards)
    if not pngs:
        print(f"❌ 找不到任何 PNG：{a.cards}")
        sys.exit(1)

    caption = ""
    if a.caption:
        caption = open(a.caption, encoding="utf-8", errors="ignore").read() \
            if os.path.isfile(a.caption) else a.caption

    findings, all_ok = check_cards(pngs)
    if a.caption is not None or caption:
        f, ok = check_hashtags(caption); findings.append(f); all_ok = all_ok and ok
    if a.html:
        hf, ok = check_html(a.html); findings.extend(hf); all_ok = all_ok and ok

    print("🤖 CAROUSEL 硬訊號自動檢查（機器判，結果穩定）")
    for code, verdict, msg in findings:
        icon = {"PASS": "✅", "FAIL": "❌", "SKIP": "⏭️"}[verdict]
        print(f"  {icon} {code} {verdict}：{msg}")
    print(f"\n硬 gate：{'全 PASS ✅ → 交給 joker 審主觀項' if all_ok else '有 FAIL ❌ → 先修硬項再進 joker'}")
    print(json.dumps({"ok": all_ok,
                      "findings": [{"code": c, "verdict": v, "msg": m} for c, v, m in findings]},
                     ensure_ascii=False))
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
