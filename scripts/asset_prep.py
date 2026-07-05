#!/usr/bin/env python3
"""asset_prep.py — brand asset intake pipeline for the social-cards engine layer.

品牌無關的引擎層工具（所有品牌共用一支）。把一個來源資產經「判型 → 走層 → 出 master
+ derived → 跑 halo_check → 寫 manifest」標準化入庫，對齊 asset-pipeline PLAN v1 決策樹
與 U5 目錄/manifest 規範。

DIRECTORY LAYOUT (per brand, U5)
--------------------------------
  brands/<brand>/assets/
    source/<id>/raw.<ext>     原檔・唯讀證據層（永不覆寫；--source 會 ingest 到這）
    master/<id>/master.svg    向量母檔（vectorize 路線）
                master.png    或 ≥1500px 透明底高解析點陣（native-alpha / repair 路線）
    derived/<id>/<name>.png   末端可重生產物
                qa/           halo_check 的合成證明圖 + report.json
    manifest.json             全品牌單一機器可讀事實源

ROUTES (--route)
----------------
  native-alpha : 來源已是帶透明的 RGBA → 直接當 master（跳過去背，PLAN 源頭層）。
  vectorize    : 乾淨白底 flat 卡通/logo → vtracer 向量化成 master.svg，rsvg-convert 出 PNG。
                 ⚠️ U2 陷阱（寫死進本腳本，勿改）：
                   * 一律 vtracer **預設參數**。禁高 color_precision — 高精度會把「白底↔黑
                     描邊」的抗鋸齒過渡保留成獨立淺色薄 path，反而在深底製造白 fringe；預設
                     precision 6 會把 fringe 併入描邊 → 乾淨。
                   * 禁餵壞 alpha 圖進向量化：vtracer 會把半透明淺色邊二值化成不透明白 path，
                     垃圾進→更糟出。只餵乾淨白底 RGB 源。
                   * 移除首個全畫布背景 path（vtracer 把背景畫成 SVG 第一個 <path>），移除後
                     rsvg 以透明底渲染 → 數學級零 halo。
                   * python-pptx 不吃 SVG，故必留「SVG master → rsvg 出 PNG」這步。
  repair       : 白底/雜背景點陣（不得已）→ 白 matte 反解去背（背景連通區→alpha ramp→
                 unpremultiply 去污染→erode 1px + gaussian 0.8px）→ master.png（PLAN 修補層）。
  auto         : 判型 — 已帶原生透明 → native-alpha；乾淨白底 flat → 印「建議 vectorize」提示但
                 **預設走 repair（保守）**；其他 → repair。

Every derived PNG is auto-run through halo_check; its verdict is written into the manifest
qa node. checked_by defaults to "asset_prep-auto" and the node is flagged
needs_independent_verify=true — 這是產圖者自評，待獨立 verifier (fresh context) 覆判（寫審分離，
見 visual-qa-gate §⑥）。

IDEMPOTENCY: same source + same params => bit-identical outputs (vtracer / rsvg->PIL-renorm
/ PIL are deterministic; manifest only rewrites that asset's node).

USAGE
-----
  python3 asset_prep.py --brand now6pm --asset-id hero-pointing-up \
      --route vectorize --source /path/to/hero-pointing-up.png \
      --derive hero=1254 mini=165
  # --source is optional: if omitted, reads existing source/<id>/raw.*
"""
import argparse
import datetime
import glob
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

import numpy as np
from PIL import Image
from scipy import ndimage

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)
import halo_check  # noqa: E402  (co-located engine module)

SKILL_ROOT = os.path.dirname(SCRIPT_DIR)            # .../social-cards
BRANDS_DIR = os.path.join(SKILL_ROOT, "brands")
VTRACER = os.path.expanduser("~/.cargo/bin/vtracer")
RSVG = "/opt/homebrew/bin/rsvg-convert"

# island-rim removal (修1) — extend removal from the opaque core to its bright-neutral
# anti-aliased rim, while sparing the character's dark outline stroke it may abut.
ISL_RIM_DILATE = 3     # px grown around the island core to reach its AA rim
ISL_RIM_LUM = 110.0    # rim pixel rgb-luminance must exceed this (below = black stroke)

# vectorize white-bg hardening (修1) — the white→black-outline anti-aliasing in a
# flat-art cell is a smooth light-gray ramp; vtracer clusters its 200-254 band into a
# separate LIGHT PATH that renders as a glowing fringe outside the outline on a dark
# card (halo 15-24% on limbs). Snapping every NEUTRAL, near-white pixel to pure white
# before tracing removes that feed → fringe gone (pose03 19.36→0.35). Safe on flat art:
# only near-white neutrals move (bg / white shirt / eye-whites all belong at pure white);
# the dark outline (lum<threshold) and coloured skin/suit (sat>tol) are untouched.
HARDEN_LUM = 205.0     # neutral pixels brighter than this -> pure white
HARDEN_SAT = 28        # only pixels this neutral (max-min channel) are hardened


# content-preservation gate (修R3) — 防「切圖/去背誤刪內部特徵（瞳孔/鈕扣高光/眼神光）」再發。
# 比對「源 cell 的非背景前景」與「master 的不透明覆蓋」：源 cell 每一塊 enclosed 深色特徵
# （如被白眼白包圍的孤立瞳孔）都必須在 master 保留。抗 1px 邊緣 erosion：先把源前景 erode
# 2px 只留「內部實心」，薄邊收縮不算損失。
# ⚠️ 關鍵：不能只用「總前景 % 損失」當門檻 —— 一顆瞳孔只佔全身前景 0.2~0.4%，用 0.5% 全域
# 門檻會漏掉（實測 pose01 瞳孔 0.42% < 0.5%）。故主判據是「連通塊」：把損失像素 label 成
# 連通分量，只要「最大一塊」> MAX_FEATURE_PX（整顆瞳孔≥~40px），即判 FAIL —— 這是尺度無關、
# 直接對應「一個特徵被整塊抹掉」的定義。全域 % 損失僅作輔助紀錄。
CONTENT_MAX_FEATURE_PX = 30  # largest lost connected component above this -> FAIL (a whole feature)
CONTENT_LOSS_MAX_PCT = 0.5   # secondary global cap (informational + gross-loss backstop)
CONTENT_FG_MIN_CH = 228      # cell background = min-channel > this AND near-neutral
CONTENT_FG_CHROMA = 30
CONTENT_EROSION = 2          # px eroded off source fg before diff (ignore edge shrink)


def _cell_foreground(rgb):
    a = rgb.astype(np.int32)
    chroma = a.max(2) - a.min(2)
    bg = (a.min(2) > CONTENT_FG_MIN_CH) & (chroma < CONTENT_FG_CHROMA)
    return ~bg


def content_preservation(cell_rgb_path, master_png_path,
                         max_feature_px=CONTENT_MAX_FEATURE_PX,
                         loss_max_pct=CONTENT_LOSS_MAX_PCT, erosion=CONTENT_EROSION):
    """Compare source-cell non-bg foreground against the master's opaque coverage.

    A missing interior feature (a whole pupil / highlight) shows up as ONE solid lost
    connected component. `ok` is False when the largest lost component exceeds
    max_feature_px (a real feature was erased) OR gross loss exceeds loss_max_pct — but
    NOT for a scatter of 1px anti-alias-shrink pixels. cell & master must be the SAME cut
    (aligned) for the diff to be clean.
    """
    cell = np.asarray(Image.open(cell_rgb_path).convert("RGB")).astype(np.int32)
    fg = _cell_foreground(cell)
    fg_interior = ndimage.binary_erosion(fg, iterations=erosion)
    m = Image.open(master_png_path).convert("RGBA")
    if m.size != (cell.shape[1], cell.shape[0]):
        m = m.resize((cell.shape[1], cell.shape[0]), Image.NEAREST)
    opaque = np.asarray(m)[..., 3] > 128
    lost = fg_interior & (~opaque)
    fi = int(fg_interior.sum())
    lp = int(lost.sum())
    pct = round(100.0 * lp / max(fi, 1), 4)

    lbl, n = ndimage.label(lost)
    if n:
        comp_areas = ndimage.sum(np.ones_like(lbl), lbl, range(1, n + 1))
        biggest = int(comp_areas.max())
        bi = int(np.argmax(comp_areas)) + 1
        ys, xs = np.where(lbl == bi)
        big_bbox = [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())]
    else:
        biggest, big_bbox = 0, None

    ok = (biggest <= max_feature_px) and (pct <= loss_max_pct)
    return {"interior_fg_px": fi, "lost_px": lp, "loss_pct": pct,
            "largest_lost_component_px": biggest,
            "largest_lost_component_bbox": big_bbox,
            "max_feature_px": max_feature_px, "loss_max_pct": loss_max_pct, "ok": ok}


# ============================================================ helpers
def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def png_save_normalized(im, path):
    """Deterministic PNG save (no timestamp/metadata chunks) for bit-identical reruns."""
    im.save(path, format="PNG", optimize=False)


def detect_kind(src_path):
    """Return (has_native_alpha, is_white_flat)."""
    im = Image.open(src_path)
    has_native_alpha = False
    if im.mode in ("RGBA", "LA") or (im.mode == "P" and "transparency" in im.info):
        a = np.asarray(im.convert("RGBA"))[..., 3]
        has_native_alpha = bool((a < 255).any())
    rgb = np.asarray(im.convert("RGB")).astype(np.float32)
    H, W = rgb.shape[:2]
    corners = np.concatenate([
        rgb[:8, :8].reshape(-1, 3), rgb[:8, -8:].reshape(-1, 3),
        rgb[-8:, :8].reshape(-1, 3), rgb[-8:, -8:].reshape(-1, 3)])
    corner_min = float(np.median(corners.min(axis=1)))
    is_white_flat = corner_min > 240.0
    return has_native_alpha, is_white_flat


# ============================================================ repair (matte_a, absorbed)
def matte_repair(src_rgb_path, out_path, T_white=212, Solid=60, band_px=3,
                 erode_px=1, blur=0.8, bg_override=None):
    """白 matte 反解去背：背景連通區→alpha ramp→unpremultiply 去污染→erode+gaussian。"""
    im = Image.open(src_rgb_path).convert("RGB")
    rgb = np.asarray(im).astype(np.float64)
    H, W = rgb.shape[:2]
    mn = rgb.min(axis=2)

    # 1. bg 估計（四角中位）
    if bg_override is not None:
        bg = np.array(bg_override, float)
    else:
        c = np.concatenate([
            rgb[:8, :8].reshape(-1, 3), rgb[:8, -8:].reshape(-1, 3),
            rgb[-8:, :8].reshape(-1, 3), rgb[-8:, -8:].reshape(-1, 3)])
        bg = np.median(c, axis=0)
    BGmin = float(bg.min())

    # 2. 背景連通區（四角 flood-fill 的 whiteish 連通分量）
    whiteish = mn > T_white
    lbl, _ = ndimage.label(whiteish)
    corner_labels = set(int(lbl[y, x]) for y, x in
                        [(0, 0), (0, W - 1), (H - 1, 0), (H - 1, W - 1)]) - {0}
    BG = np.isin(lbl, list(corner_labels)) if corner_labels else np.zeros_like(whiteish)

    # 3. 邊界帶（往主體內擴 band_px）
    dil = ndimage.binary_dilation(BG, iterations=band_px)
    band = dil & (~BG)

    # 4. alpha ramp（near-white→0, 黑描邊→1）
    denom = max(BGmin - Solid, 1.0)
    ramp = np.clip((BGmin - mn) / denom, 0.0, 1.0)
    alpha = np.ones((H, W), np.float64)
    alpha[BG] = 0.0
    alpha[band] = ramp[band]

    # 5. 顏色去污染（unpremultiply band 內 0<a<1）
    out_rgb = rgb.copy()
    m = band & (alpha > 0.003) & (alpha < 0.997)
    a = alpha[m][:, None]
    obs = rgb[m]
    true = (obs - (1.0 - a) * bg[None, :]) / a
    out_rgb[m] = np.clip(true, 0, 255)

    # 6. alpha erode 1px + gaussian 柔化
    a255 = alpha
    if erode_px > 0:
        solid_mask = a255 >= 0.5
        eroded = ndimage.binary_erosion(solid_mask, iterations=erode_px)
        peel = solid_mask & (~eroded)
        a255 = np.where(peel, np.minimum(a255, 0.35), a255)
    if blur > 0:
        a255 = ndimage.gaussian_filter(a255, sigma=blur)
    alpha_u8 = np.clip(a255 * 255.0, 0, 255).astype(np.uint8)

    out = np.dstack([np.clip(out_rgb, 0, 255).astype(np.uint8), alpha_u8])
    png_save_normalized(Image.fromarray(out), out_path)
    return {"tool": "matte_a (白matte反解去污染)",
            "params": {"T_white": T_white, "Solid": Solid, "band_px": band_px,
                       "erode_px": erode_px, "blur": blur},
            "bg_estimate": [round(float(x)) for x in bg]}


# ============================================================ vectorize (vtracer + rsvg)
def vtracer_to_svg(src_path, out_svg):
    """vtracer 預設參數 → SVG，移除首個全畫布背景 path（U2 配方）。

    NOTE (修1): stripping only the first path leaves residual bg islands in concave
    notches (vtracer emits several bg paths). Those are removed downstream at render
    time by clean_islands() inside svg_to_png() — geometric, size-independent, and
    shared with the halo_check gate. So every rendered PNG is island-free even though
    this SVG still carries the residual paths.
    """
    if not os.path.exists(VTRACER):
        raise RuntimeError(f"vtracer not found at {VTRACER} (cargo install vtracer)")
    with tempfile.NamedTemporaryFile(suffix=".svg", delete=False) as tf:
        raw_svg = tf.name
    # harden white bg (snap near-white neutrals to pure white) to kill the AA fringe
    im = Image.open(src_path).convert("RGB")
    a = np.asarray(im).astype(np.int32)
    lum = 0.299 * a[..., 0] + 0.587 * a[..., 1] + 0.114 * a[..., 2]
    sat = a.max(2) - a.min(2)
    a[(sat <= HARDEN_SAT) & (lum > HARDEN_LUM)] = (255, 255, 255)
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tf2:
        hardened = tf2.name
    png_save_normalized(Image.fromarray(a.astype(np.uint8)), hardened)
    try:
        # DEFAULT params only — see U2 traps in module docstring. Do NOT add color_precision.
        subprocess.run([VTRACER, "--input", hardened, "--output", raw_svg],
                       check=True, capture_output=True)
        svg = open(raw_svg, "r", encoding="utf-8").read()
    finally:
        os.unlink(raw_svg)
        os.unlink(hardened)

    # Remove the first <path .../> element = vtracer's full-canvas background rectangle.
    m = re.search(r"<path\b.*?/>", svg, flags=re.DOTALL)
    removed = None
    if m:
        removed = svg[m.start():m.end()][:80]
        svg = svg[:m.start()] + svg[m.end():]
    with open(out_svg, "w", encoding="utf-8") as f:
        f.write(svg)

    # svg dims from width/height attrs
    wm = re.search(r'width="(\d+)"', svg)
    hm = re.search(r'height="(\d+)"', svg)
    w = int(wm.group(1)) if wm else None
    h = int(hm.group(1)) if hm else None
    return {"tool": "vtracer default + bg-path-strip", "removed_bg_path": removed,
            "svg_w": w, "svg_h": h}


def clean_islands(im):
    """修1 (PLAN v1.1 裁決 a) — geometric post-render removal of opaque background
    islands. vtracer traces a concave background region (hair valley, boot seam) as
    SEVERAL paths; stripping only the first full-canvas one leaves the rest as
    alpha=255 light-gray specks that glow on a dark card. Fill-colour matching can't
    catch them (they quantize to a distinct gray ≈220-229, ≠ bg-white 255 ≠ shirt
    240) without also eating the white shirt/eye-whites; SVG path-coords are relative
    so cheap path-stripping is unreliable. So we clean AFTER render, geometrically:
    island = opaque + bright + neutral + FLOATING (see halo_check.find_islands — the
    single shared authority; identical definition to the QA gate). Every render — the
    master preview and every derived size — passes through here, so all outputs are
    island-free even though master.svg keeps the raw paths.

    Self-verifying diff guard: every removed pixel is asserted neutral+bright (a bg
    residue), never a saturated character pixel — so the diff can only erase
    background, never the shirt/skin/decoration.
    """
    arr = np.asarray(im.convert("RGBA")).astype(np.uint8).copy()
    islands, core = halo_check.find_islands(arr)
    if not islands:
        return Image.fromarray(arr), {"islands_removed": 0, "px_removed": 0, "detail": []}

    rgb = arr[..., :3].astype(np.int32)
    a = arr[..., 3]
    lum = 0.299 * rgb[..., 0] + 0.587 * rgb[..., 1] + 0.114 * rgb[..., 2]
    sat = rgb.max(2) - rgb.min(2)

    # The opaque core is only half the artefact: an island's ANTI-ALIASED RIM
    # (bright-neutral RGB with partial alpha) fades into the transparent bg and, over
    # a dark card, leaves a faint gray ghost. Extend removal to that rim — but the
    # island often abuts the character's BLACK OUTLINE stroke (dark, low-lum, partial
    # alpha), which must be preserved. So within a small dilation of the core, clear
    # only pixels that are BRIGHT (rgb lum > ISL_RIM_LUM) AND NEUTRAL — the island's
    # own white rim — never the dark stroke, never a saturated character pixel.
    zone = ndimage.binary_dilation(core, iterations=ISL_RIM_DILATE)
    rim = zone & (a > 0) & (sat <= halo_check.ISL_SAT_TOL) & (lum > ISL_RIM_LUM)
    remove = core | rim

    # diff guard: removal may only touch neutral pixels — never a saturated
    # character colour (shirt is neutral too but floats far from any island).
    assert not bool((remove & (sat > halo_check.ISL_SAT_TOL)).any()), \
        "island-removal guard tripped: a saturated character pixel was selected"
    removed = int(remove.sum())
    arr[remove, 3] = 0
    return Image.fromarray(arr), {
        "islands_removed": len(islands), "px_removed": removed,
        "detail": [{"area": d["area"], "bbox": d["bbox"], "rgb": d["rgb"]} for d in islands],
    }


def svg_to_png(svg_path, out_png, width, height):
    """rsvg-convert → temp PNG → clean_islands (修1) → PIL renormalize
    (deterministic, guaranteed RGBA). Returns island-removal stats dict."""
    if not os.path.exists(RSVG):
        raise RuntimeError(f"rsvg-convert not found at {RSVG} (brew install librsvg)")
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tf:
        tmp = tf.name
    try:
        subprocess.run([RSVG, "-w", str(width), "-h", str(height),
                        svg_path, "-o", tmp], check=True, capture_output=True)
        im = Image.open(tmp).convert("RGBA")
        im, isl_stat = clean_islands(im)
        png_save_normalized(im, out_png)
        return isl_stat
    finally:
        os.unlink(tmp)


def raster_derive(master_png, out_png, width):
    """Derive a sized PNG from a raster master (preserve aspect, LANCZOS, deterministic)."""
    im = Image.open(master_png).convert("RGBA")
    w, h = im.size
    height = max(1, round(width * h / w))
    im2 = im.resize((width, height), Image.LANCZOS)
    png_save_normalized(im2, out_png)
    return width, height


# ============================================================ manifest
def load_manifest(path, brand):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"brand": brand, "assets": {}}


def write_manifest(path, data):
    # deterministic: sort asset keys
    data["assets"] = {k: data["assets"][k] for k in sorted(data["assets"])}
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False, sort_keys=False)
        f.write("\n")


# ============================================================ main pipeline
def run(brand, asset_id, route, derives, source=None, kind="unspecified",
        origin="unspecified", checked_by="asset_prep-auto",
        provenance_source=None, cell_bbox=None):
    brand_dir = os.path.join(BRANDS_DIR, brand)
    assets_dir = os.path.join(brand_dir, "assets")
    src_dir = os.path.join(assets_dir, "source", asset_id)
    master_dir = os.path.join(assets_dir, "master", asset_id)
    derived_dir = os.path.join(assets_dir, "derived", asset_id)
    qa_dir = os.path.join(derived_dir, "qa")
    manifest_path = os.path.join(assets_dir, "manifest.json")
    for d in (src_dir, master_dir, derived_dir, qa_dir):
        os.makedirs(d, exist_ok=True)

    # --- ingest source (唯讀證據層) ---
    if source:
        ext = os.path.splitext(source)[1].lower() or ".png"
        raw_path = os.path.join(src_dir, "raw" + ext)
        # copy only if changed (keep source/ stable & idempotent)
        if not (os.path.exists(raw_path) and sha256(source) == sha256(raw_path)):
            shutil.copy2(source, raw_path)
    else:
        found = sorted(glob.glob(os.path.join(src_dir, "raw.*")))
        if not found:
            raise FileNotFoundError(
                f"no source at {src_dir}/raw.* — pass --source to ingest one")
        raw_path = found[0]

    has_alpha, is_white_flat = detect_kind(raw_path)

    # --- auto route resolution ---
    resolved = route
    hints = []
    if route == "auto":
        if has_alpha:
            resolved = "native-alpha"
        elif is_white_flat:
            resolved = "repair"
            hints.append("來源為乾淨白底 flat：**建議改用 --route vectorize** 建 SVG 母檔"
                         "（任意尺寸零 halo）；auto 保守預設走 repair。")
        else:
            resolved = "repair"

    # --- process → master ---
    processing = {"route": resolved}
    if resolved == "native-alpha":
        if not has_alpha:
            raise ValueError("route native-alpha but source has no transparency")
        master = os.path.join(master_dir, "master.png")
        png_save_normalized(Image.open(raw_path).convert("RGBA"), master)
        processing.update(tool="native-alpha passthrough", params={})
        master_kind = "png"
    elif resolved == "repair":
        master = os.path.join(master_dir, "master.png")
        info = matte_repair(raw_path, master)
        processing.update(tool=info["tool"], params=info["params"],
                          bg_estimate=info["bg_estimate"])
        master_kind = "png"
    elif resolved == "vectorize":
        if has_alpha:
            hints.append("⚠️ 來源帶 alpha，向量化會放大壞邊（U2 陷阱）；建議改 native-alpha 或 repair。")
        master = os.path.join(master_dir, "master.svg")
        info = vtracer_to_svg(raw_path, master)
        processing.update(tool=info["tool"], params={"vtracer": "default"},
                          removed_bg_path=info["removed_bg_path"])
        svg_w, svg_h = info["svg_w"], info["svg_h"]
        master_kind = "svg"
    else:
        raise ValueError(f"unknown route {resolved}")

    # master_px
    if master_kind == "svg":
        master_px = svg_w
    else:
        master_px = Image.open(master).size[0]
    processing["master"] = os.path.relpath(master, assets_dir)
    processing["master_px"] = master_px

    # --- master QA (裁決 b): the MASTER is where 貼邊 4px is enforced (absolute pad).
    #     Render an island-cleaned master-resolution PNG proof and gate it WITH pad. ---
    master_qa_dir = os.path.join(master_dir, "qa")
    if master_kind == "svg":
        master_preview = os.path.join(master_dir, "master-preview.png")
        master_isl = svg_to_png(master, master_preview, svg_w, svg_h)
        processing["islands_removed"] = master_isl
        master_check_target = master_preview
    else:
        master_check_target = master
    mrep = halo_check.check(master_check_target, bg_names=("navy", "white", "rust"),
                            out_dir=master_qa_dir, skip_pad=False)

    # --- content-preservation gate (修R3): source cell vs master opaque coverage ---
    # Guards against silently erasing an enclosed interior feature (pupil / catch-light /
    # button highlight) during repair/vectorize. FAIL escalates the master verdict.
    content = content_preservation(raw_path, master_check_target)
    content_verdict = "PASS" if content["ok"] else "FAIL"
    # combined master verdict = worst of halo/pad/islands and content-preservation
    combined_verdict = mrep["verdict"]
    if not content["ok"]:
        combined_verdict = "FAIL"
    master_qa = {
        "target": os.path.relpath(master_check_target, assets_dir),
        "verdict": combined_verdict,
        "halo_verdict": mrep["verdict"],
        "halo_score": mrep.get("halo_score"),
        "alpha_padding": mrep.get("alpha_padding"),
        "alpha_padding_ok": mrep.get("alpha_padding_ok"),
        "opaque_islands": mrep.get("opaque_islands", {}).get("count"),
        "content_preservation": {
            "verdict": content_verdict,
            "interior_fg_px": content["interior_fg_px"],
            "lost_px": content["lost_px"],
            "loss_pct": content["loss_pct"],
            "largest_lost_component_px": content["largest_lost_component_px"],
            "largest_lost_component_bbox": content["largest_lost_component_bbox"],
            "max_feature_px": content["max_feature_px"],
            "loss_max_pct": content["loss_max_pct"],
            "note": ("源 cell 內部前景 vs master 不透明覆蓋；最大損失連通塊 > max_feature_px "
                     "= 有內部特徵（瞳孔/高光）被整塊誤刪 => FAIL。抗 1px 邊緣 erosion。"),
        },
        "proof_dir": os.path.relpath(master_qa_dir, assets_dir),
    }

    # --- derive PNGs + halo_check (裁決 b): DERIVATIVES are equal-ratio scalings —
    #     verify halo + opaque-islands only, skip 貼邊 pad (--skip-pad). ---
    qa_derives = {}
    for name, px in derives.items():
        out_png = os.path.join(derived_dir, f"{name}.png")
        if master_kind == "svg":
            height = max(1, round(px * (svg_h / svg_w))) if svg_w else px
            isl_stat = svg_to_png(master, out_png, px, height)
        else:
            raster_derive(master, out_png, px)
            isl_stat = None
        # per-derive qa dir
        d_qa = os.path.join(qa_dir, name)
        rep = halo_check.check(out_png, bg_names=("navy", "white", "rust"),
                               out_dir=d_qa, skip_pad=True)
        qa_derives[name] = {
            "px": px,
            "file": os.path.relpath(out_png, assets_dir),
            "verdict": rep["verdict"],
            "halo_score": rep.get("halo_score"),
            "halo_ratio": rep.get("halo_ratio"),
            "fg_edge_lum": rep.get("fg_edge_lum"),
            "opaque_islands": rep.get("opaque_islands", {}).get("count"),
            "alpha_padding": rep.get("alpha_padding"),
            "alpha_padding_checked": rep.get("alpha_padding_checked"),
            "islands_removed_at_render": isl_stat,
            "proof_dir": os.path.relpath(d_qa, assets_dir),
        }

    # --- manifest ---
    manifest = load_manifest(manifest_path, brand)
    manifest["brand"] = brand
    # provenance.source_file points to the TRUE origin (裁決 R3: must trace to _origin,
    # never the intermediate cut cell — that mis-trace is exactly how round-2's verifier
    # was fooled). When --provenance-source/--cell are given, record the origin sheet +
    # the cell bbox, and keep the intermediate cut cell path under `cut_cell`.
    if provenance_source is not None:
        prov = {
            "origin": origin,
            "acquired": datetime.date.today().isoformat(),
            "source_file": provenance_source,
            "source_sha256": sha256(os.path.join(assets_dir, provenance_source))
            if os.path.exists(os.path.join(assets_dir, provenance_source)) else None,
            "cut_cell": os.path.relpath(raw_path, assets_dir),
            "cut_cell_sha256": sha256(raw_path),
            "cell_bbox_on_sheet": cell_bbox,
            "native_alpha": has_alpha,
        }
    else:
        prov = {
            "origin": origin,
            "acquired": datetime.date.today().isoformat(),
            "source_file": os.path.relpath(raw_path, assets_dir),
            "source_sha256": sha256(raw_path),
            "native_alpha": has_alpha,
        }
    manifest.setdefault("assets", {})[asset_id] = {
        "kind": kind,
        "provenance": prov,
        "processing": processing,
        "qa": {
            "master": master_qa,
            "derives": qa_derives,
            "checked_by": checked_by,
            "needs_independent_verify": True,
            "note": ("checked_by 為自動化產圖者自評；待獨立 verifier（fresh context / 不同 pass）"
                     "覆判——寫審分離，見 visual-qa-gate §⑥。"),
            "checked": datetime.date.today().isoformat(),
        },
    }
    write_manifest(manifest_path, manifest)

    return {"route": resolved, "master": master, "master_px": master_px,
            "master_qa": master_qa, "derives": qa_derives, "hints": hints,
            "manifest": manifest_path, "source": raw_path}


def main():
    ap = argparse.ArgumentParser(
        description="Brand asset intake pipeline (route→master→derive→halo_check→manifest).")
    ap.add_argument("--brand", required=True)
    ap.add_argument("--asset-id", required=True)
    ap.add_argument("--route", required=True,
                    choices=["auto", "native-alpha", "vectorize", "repair"])
    ap.add_argument("--derive", nargs="*", default=[],
                    metavar="name=px", help="derived sizes e.g. hero=1254 mini=165")
    ap.add_argument("--source", help="ingest this file into source/<id>/raw.* (optional; "
                                     "if omitted, reads existing source/<id>/raw.*)")
    ap.add_argument("--kind", default="unspecified",
                    help="character | logo | product | prop | unspecified")
    ap.add_argument("--origin", default="unspecified",
                    help="chatgpt | client-supplied | website-scrape | ... (provenance)")
    ap.add_argument("--checked-by", default="asset_prep-auto",
                    help="QA attributor written to manifest (default flags auto self-check)")
    ap.add_argument("--provenance-source",
                    help="relpath (from assets/) of the TRUE origin (e.g. source/_origin/"
                         "poses-sheet.png). Sets provenance.source_file to it; the cut cell "
                         "is recorded under provenance.cut_cell. 修R3: 追溯必到 _origin。")
    ap.add_argument("--cell", help="cell bbox on the origin sheet 'x0,y0,x1,y1' (provenance)")
    args = ap.parse_args()

    derives = {}
    for d in args.derive:
        if "=" not in d:
            ap.error(f"bad --derive '{d}', expected name=px")
        name, px = d.split("=", 1)
        derives[name] = int(px)

    if args.source and not os.path.exists(args.source):
        ap.error(f"--source not found: {args.source}")

    cell_bbox = None
    if args.cell:
        cell_bbox = [int(v) for v in args.cell.split(",")]

    res = run(args.brand, args.asset_id, args.route, derives,
              source=args.source, kind=args.kind, origin=args.origin,
              checked_by=args.checked_by,
              provenance_source=args.provenance_source, cell_bbox=cell_bbox)

    print(f"[asset_prep] brand={args.brand} asset={args.asset_id} route={res['route']}")
    print(f"  source : {res['source']}")
    print(f"  master : {res['master']} (px={res['master_px']})")
    mq = res["master_qa"]
    cp = mq["content_preservation"]
    print(f"  master QA (4px pad): [{mq['verdict']}] halo={mq['halo_score']} "
          f"islands={mq['opaque_islands']} pad={mq['alpha_padding']} ok={mq['alpha_padding_ok']}")
    print(f"  content-preservation: [{cp['verdict']}] lost={cp['lost_px']}px "
          f"largest_blob={cp['largest_lost_component_px']}px (max {cp['max_feature_px']}px) "
          f"gross={cp['loss_pct']}%")
    for name, info in res["derives"].items():
        print(f"  derive {name}={info['px']} -> {info['file']}  "
              f"halo_check=[{info['verdict']}] score={info['halo_score']} "
              f"islands={info['opaque_islands']} (skip-pad)")
    for h in res["hints"]:
        print(f"  hint: {h}")
    print(f"  manifest: {res['manifest']}  (needs_independent_verify=true)")


if __name__ == "__main__":
    main()
