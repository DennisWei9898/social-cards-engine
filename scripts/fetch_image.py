#!/usr/bin/env python3
"""版權優先的圖片抓取器 · social-cards-engine

一個「找圖 + 附出處」的 helper，給引擎在需要真實照片 / 迷因模板時呼叫。
它**不替使用者決定**——只抓一排候選、附上來源與授權，讓使用者挑或換來源。

設計原則
  1. 版權優先：預設抓 CC / 公眾領域（Openverse → Wikimedia Commons），免 API key。
  2. 永不靜默使用：每張圖都寫 provenance（來源 / 頁面 / 授權 / 作者 / 標註句）到
     `fetch_manifest.json`，並印出清單交使用者定奪。
  3. 迷因例外：走 imgflip 乾淨模板（免 key），抓完印**版權提醒**——個人非商用風險較低，
     品牌 / 客戶案請改自繪原創或買授權（meme-joker 會擋版權梗）。
  4. WebSearch 撿到的圖：用 --url 直接下載並登記使用者提供的出處。
  5. 零相依：只用 Python 標準庫（urllib）。零寫死金鑰（Unsplash / Pexels 走環境變數）。

用法
  # 版權友善（預設 Openverse，CC/PD，免 key）
  python3 scripts/fetch_image.py "morning coffee" --count 3 --out /tmp/cards_assets
  # 指定來源
  python3 scripts/fetch_image.py "taipei 101" --source wikimedia --count 2 --out ...
  python3 scripts/fetch_image.py "sunrise" --source unsplash --count 3 --out ...   # 需 key
  # 迷因模板（imgflip，附版權提醒）
  python3 scripts/fetch_image.py "drake" --meme --out brands/meme/memes
  # 直接下載 WebSearch 撿到的圖，並登記出處（--credit 一律自填來源/作者/授權）
  python3 scripts/fetch_image.py --url "https://example.com/x.jpg" \
      --credit "作者名 · 來源頁 · 授權(如 CC BY 4.0)" --out ...

選用來源需免費 API key（讀環境變數，不寫死）：
  export UNSPLASH_ACCESS_KEY=...   # https://unsplash.com/developers
  export PEXELS_API_KEY=...        # https://www.pexels.com/api/
"""
import argparse
import json
import os
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

UA = "social-cards-engine/1.0 (image fetcher; +https://github.com/DennisWei9898/social-cards-engine)"
TIMEOUT = 30

# 迷因範本用到的檔名（brands/meme/render_template.py 會引用這些）
MEME_FILES = ["thisisfine.jpg", "drake.jpg", "pikachu.jpg", "brain.jpg"]


# ---------- HTTP 小工具（純標準庫） ----------
def _get(url, headers=None):
    req = urllib.request.Request(url, headers={"User-Agent": UA, **(headers or {})})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        return r.read(), r.headers.get("Content-Type", "")


def _get_json(url, headers=None):
    body, _ = _get(url, headers)
    return json.loads(body.decode("utf-8", "replace"))


def _ext_from(url, content_type):
    m = re.search(r"\.(jpe?g|png|webp|gif)(?:$|[?#])", url, re.I)
    if m:
        return "." + m.group(1).lower().replace("jpeg", "jpg")
    ct = (content_type or "").lower()
    for key, ext in (("jpeg", ".jpg"), ("png", ".png"), ("webp", ".webp"), ("gif", ".gif")):
        if key in ct:
            return ext
    return ".jpg"


def _slug(text, maxlen=40):
    s = re.sub(r"[^a-zA-Z0-9]+", "_", (text or "img").strip()).strip("_").lower()
    return (s or "img")[:maxlen]


# ---------- 各來源：回傳統一格式的候選 dict ----------
# 每個候選：{direct_url, page_url, license, license_url, author, title, attribution, source}
def search_openverse(query, count):
    q = urllib.parse.quote(query)
    # license_type=commercial,modification → 可商用且可改作，偏「安全重用」
    url = (f"https://api.openverse.org/v1/images/?q={q}"
           f"&page_size={count}&license_type=commercial,modification&mature=false")
    data = _get_json(url)
    out = []
    for it in data.get("results", [])[:count]:
        out.append({
            "direct_url": it.get("url"),
            "page_url": it.get("foreign_landing_url") or it.get("url"),
            "license": (it.get("license", "") + " " + str(it.get("license_version", ""))).strip().upper(),
            "license_url": it.get("license_url", ""),
            "author": it.get("creator") or "unknown",
            "title": it.get("title") or query,
            "attribution": it.get("attribution") or "",
            "source": "openverse",
        })
    return out


def search_wikimedia(query, count):
    q = urllib.parse.quote(query)
    url = ("https://commons.wikimedia.org/w/api.php?action=query&format=json"
           f"&generator=search&gsrsearch={q}&gsrnamespace=6&gsrlimit={count}"
           "&prop=imageinfo&iiprop=url|extmetadata")
    data = _get_json(url)
    pages = (data.get("query", {}) or {}).get("pages", {}) or {}
    out = []
    for p in list(pages.values())[:count]:
        info = (p.get("imageinfo") or [{}])[0]
        meta = info.get("extmetadata", {}) or {}

        def mv(k):
            return (meta.get(k, {}) or {}).get("value", "")

        author = re.sub(r"<[^>]+>", "", mv("Artist")).strip() or "unknown"
        out.append({
            "direct_url": info.get("url"),
            "page_url": info.get("descriptionurl") or info.get("url"),
            "license": mv("LicenseShortName") or "see page",
            "license_url": mv("LicenseUrl"),
            "author": author,
            "title": p.get("title", query),
            "attribution": re.sub(r"<[^>]+>", "", mv("Credit")).strip(),
            "source": "wikimedia",
        })
    return out


def search_unsplash(query, count):
    key = os.environ.get("UNSPLASH_ACCESS_KEY")
    if not key:
        raise RuntimeError("缺 UNSPLASH_ACCESS_KEY 環境變數（免費申請：https://unsplash.com/developers）")
    q = urllib.parse.quote(query)
    url = f"https://api.unsplash.com/search/photos?query={q}&per_page={count}"
    data = _get_json(url, headers={"Authorization": f"Client-ID {key}"})
    out = []
    for it in data.get("results", [])[:count]:
        user = it.get("user", {}) or {}
        out.append({
            "direct_url": (it.get("urls", {}) or {}).get("regular"),
            "page_url": (it.get("links", {}) or {}).get("html", ""),
            "license": "Unsplash License (免費可商用，免標註但建議註明)",
            "license_url": "https://unsplash.com/license",
            "author": user.get("name") or "unknown",
            "title": it.get("description") or it.get("alt_description") or query,
            "attribution": f"Photo by {user.get('name','?')} on Unsplash",
            "source": "unsplash",
        })
    return out


def search_pexels(query, count):
    key = os.environ.get("PEXELS_API_KEY")
    if not key:
        raise RuntimeError("缺 PEXELS_API_KEY 環境變數（免費申請：https://www.pexels.com/api/）")
    q = urllib.parse.quote(query)
    url = f"https://api.pexels.com/v1/search?query={q}&per_page={count}"
    data = _get_json(url, headers={"Authorization": key})
    out = []
    for it in data.get("photos", [])[:count]:
        out.append({
            "direct_url": (it.get("src", {}) or {}).get("large"),
            "page_url": it.get("url", ""),
            "license": "Pexels License (免費可商用，免標註但建議註明)",
            "license_url": "https://www.pexels.com/license/",
            "author": it.get("photographer") or "unknown",
            "title": it.get("alt") or query,
            "attribution": f"Photo by {it.get('photographer','?')} on Pexels",
            "source": "pexels",
        })
    return out


def search_imgflip_meme(query, count):
    """imgflip 乾淨梗圖模板（免 key）。⚠️ 版權：個人非商用較低風險，品牌案請走原創/授權。"""
    data = _get_json("https://api.imgflip.com/get_memes")
    memes = (data.get("data", {}) or {}).get("memes", []) or []
    ql = query.lower().strip()
    hits = [m for m in memes if ql in (m.get("name", "").lower())] if ql else memes
    hits = hits[:count]
    out = []
    for m in hits:
        out.append({
            "direct_url": m.get("url"),
            "page_url": f"https://imgflip.com/memetemplate/{m.get('id','')}",
            "license": "⚠️ 梗圖模板・版權未定（個人非商用較低風險，品牌案請改原創/授權）",
            "license_url": "https://imgflip.com/",
            "author": "imgflip / 原梗作者",
            "title": m.get("name") or query,
            "attribution": f"meme template「{m.get('name','?')}」via imgflip",
            "source": "imgflip",
        })
    return out


SOURCES = {
    "openverse": search_openverse,
    "wikimedia": search_wikimedia,
    "unsplash": search_unsplash,
    "pexels": search_pexels,
}


# ---------- 下載 + 出處登記 ----------
def download(cand, out_dir, idx, name_hint=None):
    url = cand.get("direct_url")
    if not url:
        return None
    body, ct = _get(url)
    ext = _ext_from(url, ct)
    base = name_hint or f"{cand['source']}_{_slug(cand.get('title'))}_{idx}"
    fp = out_dir / f"{base}{ext}"
    fp.write_bytes(body)
    return fp


def write_manifest(out_dir, records):
    mf = out_dir / "fetch_manifest.json"
    existing = []
    if mf.exists():
        try:
            existing = json.loads(mf.read_text("utf-8"))
        except Exception:
            existing = []
    existing.extend(records)
    mf.write_text(json.dumps(existing, ensure_ascii=False, indent=2), "utf-8")
    return mf


def print_summary(records):
    if not records:
        print("  （沒有抓到任何圖，換個關鍵字或來源試試）")
        return
    print("\n===== 抓到的圖 + 出處（請自行挑選 / 決定是否採用）=====")
    for r in records:
        print(f"• {Path(r['file']).name}")
        print(f"    來源 : {r['source']}   授權 : {r['license']}")
        print(f"    作者 : {r['author']}")
        print(f"    出處 : {r['page_url']}")
        if r.get("attribution"):
            print(f"    標註 : {r['attribution']}")
    print("\n注意：以上為候選，**引擎不會自動採用**。請挑一張、或說「換來源 / 換關鍵字」。")
    if any(r["source"] == "imgflip" for r in records):
        print("⚠️ 迷因模板版權未定：個人非商用較低風險；品牌 / 客戶案請改自繪原創或買授權。")


# ---------- 主流程 ----------
def run(args):
    out_dir = Path(args.out).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    records = []

    # 模式一：直接下載一個 URL（WebSearch 撿到的圖）
    if args.url:
        cand = {
            "direct_url": args.url, "page_url": args.url,
            "license": args.credit or "使用者提供・請自行確認授權",
            "license_url": "", "author": args.credit or "unknown",
            "title": args.query or "web_pick",
            "attribution": args.credit or "", "source": "web",
        }
        fp = download(cand, out_dir, 1, name_hint=_slug(args.query or "web_pick"))
        if fp:
            records.append({**cand, "file": str(fp)})
        write_manifest(out_dir, records)
        print_summary(records)
        return 0

    if not args.query:
        print("請給關鍵字，例如：fetch_image.py \"morning coffee\" --out ./assets", file=sys.stderr)
        return 2

    # 模式二：迷因模板
    if args.meme:
        cands = search_imgflip_meme(args.query, args.count)
        for i, c in enumerate(cands, 1):
            try:
                fp = download(c, out_dir, i)
                if fp:
                    records.append({**c, "file": str(fp)})
            except Exception as e:
                print(f"  下載失敗（{c.get('title')}）：{e}", file=sys.stderr)
        write_manifest(out_dir, records)
        print_summary(records)
        return 0

    # 模式三：版權優先的照片搜尋（auto = openverse → wikimedia 補足）
    order = ["openverse", "wikimedia"] if args.source == "auto" else [args.source]
    seen = 0
    for src in order:
        if seen >= args.count:
            break
        try:
            cands = SOURCES[src](args.query, args.count - seen)
        except Exception as e:
            print(f"  來源 {src} 失敗：{e}", file=sys.stderr)
            continue
        for i, c in enumerate(cands, 1):
            try:
                fp = download(c, out_dir, seen + i)
                if fp:
                    records.append({**c, "file": str(fp)})
                    seen += 1
            except Exception as e:
                print(f"  下載失敗（{c.get('title')}）：{e}", file=sys.stderr)
    write_manifest(out_dir, records)
    print_summary(records)
    return 0


def main():
    ap = argparse.ArgumentParser(description="版權優先的圖片抓取器（附出處，交使用者決定）")
    ap.add_argument("query", nargs="?", help="搜尋關鍵字（英文命中率較高）")
    ap.add_argument("--out", required=True, help="輸出資料夾")
    ap.add_argument("--count", type=int, default=3, help="抓幾張候選（預設 3）")
    ap.add_argument("--source", default="auto",
                    choices=["auto", "openverse", "wikimedia", "unsplash", "pexels"],
                    help="來源（預設 auto＝openverse→wikimedia，版權友善免 key）")
    ap.add_argument("--meme", action="store_true", help="改抓 imgflip 迷因模板（附版權提醒）")
    ap.add_argument("--url", help="直接下載這個圖片 URL（WebSearch 撿到的圖）")
    ap.add_argument("--credit", help="搭配 --url：自填來源/作者/授權（會寫進出處）")
    args = ap.parse_args()
    try:
        return run(args)
    except Exception as e:
        print(f"錯誤：{e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
