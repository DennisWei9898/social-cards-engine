#!/usr/bin/env python3
"""halo_check.py — machine gate for white-halo residue + alpha padding on RGBA assets.

Engine-layer QA tool for the social-cards asset pipeline (品牌無關，所有品牌共用一支).
It is the single executable authority for BOTH:
  1. white-halo measurement  (absorbed & adapted from asset-lab/U3/halo_measure.py)
  2. alpha-padding check      (spec source: references/visual-qa-gate.md §⑤)

WHAT A "WHITE HALO" IS
----------------------
A bright fringe left when a white-background asset is keyed to transparency WITHOUT
decontaminating the RGB of the semi-transparent edge pixels. The rim keeps near-white
RGB but partial alpha, so over a dark colour it glows — belonging to neither the
background nor the character. We composite the asset over brand backgrounds and inspect
the alpha boundary band. Luminance = Rec.601 (0.299R + 0.587G + 0.114B).

We compare every rim pixel to the LOCAL adjacent character colour (windowed mean of the
opaque body it borders), NOT a global median — so a legitimately bright body edge is not
mistaken for a halo. A pixel counts as halo only if its composited luminance exceeds BOTH
the background AND its local character reference by > MARGIN. A clean anti-aliased rim is a
blend of char<->bg and mathematically cannot exceed both.

On a WHITE background halo_ratio is ~0 by construction (nothing is brighter than white) —
exactly why halos slipped through on light cards. NAVY is the most sensitive background,
RUST intermediate. Headline score = max halo_ratio over the non-white backgrounds.

THRESHOLDS (U3-calibrated, 2026-07-05; hardcoded defaults, overridable via flags)
---------------------------------------------------------------------------------
  headline score = max(navy%, rust%)
    PASS  < 15
    WARN  15 .. < 25   (auto-emit navy composite; human zoom 四點位 覆判)
    FAIL  >= 25
  fg_edge_lum > 120            -> WARN   (bg-independent contamination: rim RGB near white)
  alpha padding any side < 4px -> FAIL   (資產本身已被裁到貼邊)
Basis: current 17 assets scored 2.82-7.85%, positive control 59.92% (7.6x separation),
fg_edge_lum <=48 (clean) vs 237 (contaminated).

EXIT CODES:  0 = PASS   1 = FAIL   2 = WARN

USAGE
-----
  python3 halo_check.py --input asset.png
  python3 halo_check.py --input asset.png --bg navy white rust --out qa/
  python3 halo_check.py --input asset.png --alpha-only        # §⑤ padding only, no halo
  python3 halo_check.py --input asset.png --json               # machine-readable to stdout

Side products written to --out (default: <input_dir>/qa/):
  on-<bg>.png  composited proofs (one per background)
  report.json  full result (schema aligns with manifest qa node)
"""
import argparse
import datetime
import json
import os
import sys

import numpy as np
from PIL import Image
from scipy.ndimage import binary_dilation, uniform_filter

# ---- brand backgrounds -------------------------------------------------------
# "rust" is the brand orange (#C4400C). "orange" accepted as an alias.
BACKGROUNDS = {
    "navy":  (0x14, 0x23, 0x3B),   # (20, 35, 59)
    "white": (0xFF, 0xFF, 0xFF),
    "rust":  (0xC4, 0x40, 0x0C),   # (196, 64, 12)
}
BG_ALIASES = {"orange": "rust"}

# ---- calibrated constants ----------------------------------------------------
MARGIN = 20.0        # luminance margin (0..255) to call a pixel "brighter than"
DILATE_ITER = 2      # +-2px band used to find the adjacent solid character colour
LOCAL_WIN = 7        # window (px) for the LOCAL adjacent-character reference

# ---- default gate thresholds (overridable) -----------------------------------
PASS_MAX = 15.0      # score < 15  -> PASS band
WARN_MAX = 25.0      # 15 <= score < 25 -> WARN ; score >= 25 -> FAIL
FG_EDGE_WARN = 120.0 # fg_edge_lum above this -> WARN
MIN_ALPHA_PAD = 4    # any side < this (px) -> FAIL

# ---- opaque background-island detection (PLAN v1.1 裁決 a/修2) ---------------
# A "background-residue island" is an OPAQUE, BRIGHT, NEUTRAL blob that FLOATS in
# the (now transparent) background — vtracer leaves them in concave notches (hair
# valley, boot seam) when it traces the bg as several paths and only the first
# full-canvas one is stripped; matte/crop can leave a clipped-decoration fragment
# at a pasted edge. They read as alpha=255 light specks over a dark card — a
# structural defect, NOT a soft halo. Distinct from a legit white feature (shirt,
# cuff, eye-white) which is EMBEDDED in the character and bordered by character
# pixels, so its surrounding ring is opaque (isolation ~0.0) not transparent.
# Discriminators (validated on now6pm hero vectorize + 17 assets, 2026-07-05):
#   neutral  chroma(max-min channel) <= ISL_SAT_TOL   (excludes warm skin sat~66,
#            and coloured sparks/sweat marks — "非人物主色")
#   bright   luminance > ISL_LUM_FLOOR                 (near-white / light-gray)
#   floating isolation >= ISL_ISO_THRESH               (transparent fraction of a
#            ISL_RING-px surrounding band; embedded features 0.00-0.03, residue
#            0.37-0.78 — a >10x-margin gap, threshold sits in the middle)
#   sized    area > ISL_MIN_AREA px
# Any island with area > 10px is a FAIL (structural, no WARN grace — 修2).
ISL_SAT_TOL = 16       # max neutral chroma
ISL_LUM_FLOOR = 200.0  # brightness floor
ISL_ISO_THRESH = 0.25  # min transparent-ring fraction to count as "floating"
ISL_MIN_AREA = 10      # area strictly > this (px) counts (裁決: >10px -> FAIL)
ISL_RING = 3           # px band sampled around a component for isolation

SEVERITY_RANK = {"PASS": 0, "WARN": 1, "FAIL": 2}
EXIT_CODE = {"PASS": 0, "FAIL": 1, "WARN": 2}


def _luminance(rgb):
    return 0.299 * rgb[..., 0] + 0.587 * rgb[..., 1] + 0.114 * rgb[..., 2]


def _resolve_bg(name):
    key = BG_ALIASES.get(name, name)
    if key not in BACKGROUNDS:
        raise ValueError(f"unknown background '{name}' (choose from {list(BACKGROUNDS)} or 'orange')")
    return key, BACKGROUNDS[key]


def check_alpha_padding(path, min_pad=MIN_ALPHA_PAD):
    """§⑤ — alpha bbox 四邊距；任一邊 < min_pad => 資產已被裁 (FAIL)."""
    im = Image.open(path).convert("RGBA")
    alpha = im.getchannel("A")
    bbox = alpha.getbbox()          # bounding box of opaque pixels
    if bbox is None:
        return {"ok": False, "pads": None, "bad": None, "note": "全透明，沒有內容"}
    w, h = im.size
    left, top, right, bottom = bbox
    pads = {"left": int(left), "top": int(top),
            "right": int(w - right), "bottom": int(h - bottom)}
    bad = {k: v for k, v in pads.items() if v < min_pad}
    return {"ok": not bad, "pads": pads, "bad": bad or None,
            "note": f"四邊距 {pads}" + ("" if not bad else f" ← 貼邊: {bad}，資產已被裁")}


def find_islands(rgba_arr, sat_tol=ISL_SAT_TOL, lum_floor=ISL_LUM_FLOOR,
                 iso_thresh=ISL_ISO_THRESH, min_area=ISL_MIN_AREA, ring=ISL_RING):
    """Detect opaque background-residue islands. See module constants for theory.

    rgba_arr : HxWx4 uint8/float ndarray (RGBA).
    Returns (islands, mask) where `islands` is a list of dicts
    {area, iso, rgb, bbox=(x0,y0,x1,y1), centroid=(cx,cy)} sorted by area desc,
    and `mask` is a HxW bool array = union of all island pixels (for removal).
    """
    from scipy.ndimage import label, binary_dilation, find_objects  # local import
    arr = np.asarray(rgba_arr).astype(np.int32)
    a = arr[..., 3]
    rgb = arr[..., :3]
    lum = _luminance(rgb.astype(np.float32))
    sat = rgb.max(axis=2) - rgb.min(axis=2)
    transp = a < 250
    cand = (a >= 250) & (lum > lum_floor) & (sat <= sat_tol)

    mask = np.zeros(a.shape, dtype=bool)
    islands = []
    if not cand.any():
        return islands, mask
    lbl, n = label(cand)
    for i in range(1, n + 1):
        m = lbl == i
        area = int(m.sum())
        if area <= min_area:
            continue
        ring_mask = binary_dilation(m, iterations=ring) & (~m)
        rp = int(ring_mask.sum())
        iso = (float((ring_mask & transp).sum()) / rp) if rp else 0.0
        if iso < iso_thresh:
            continue
        ys, xs = np.where(m)
        islands.append({
            "area": area,
            "iso": round(iso, 3),
            "rgb": [int(v) for v in rgb[m].mean(axis=0).round()],
            "bbox": [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())],
            "centroid": [int(xs.mean().round()), int(ys.mean().round())],
        })
        mask |= m
    islands.sort(key=lambda d: -d["area"])
    return islands, mask


def check_islands(path, **kw):
    """§修2 wrapper — run island detection on a file path. Returns dict with
    count, total_area, verdict (FAIL if any island >10px, else PASS), details."""
    im = Image.open(path).convert("RGBA")
    islands, _ = find_islands(np.asarray(im), **kw)
    total = int(sum(d["area"] for d in islands))
    return {"ok": not islands, "count": len(islands), "total_area": total,
            "islands": islands}


def measure_halo(path, bg_names):
    """Halo measurement over the given backgrounds. Returns dict with per-bg halo_ratio,
    the headline halo_score (max over non-white bgs measured), and fg_edge_lum."""
    im = Image.open(path).convert("RGBA")
    arr = np.asarray(im).astype(np.float32)
    fg = arr[..., :3]
    a = arr[..., 3]
    a01 = a / 255.0

    edge = (a > 0) & (a < 255)                       # anti-aliased rim
    band = binary_dilation(edge, iterations=DILATE_ITER)
    solid_in_band = band & (a >= 255)
    if solid_in_band.sum() < 20:
        solid_in_band = (a >= 255)

    fg_lum = _luminance(fg)
    fg_edge_lum = float(np.median(fg_lum[edge])) if edge.any() else 0.0
    char_solid_lum = (float(np.median(fg_lum[solid_in_band]))
                      if solid_in_band.any() else 0.0)

    # LOCAL adjacent-character luminance (windowed mean of opaque fg luminance).
    opaque = (a >= 255).astype(np.float32)
    num = uniform_filter(fg_lum * opaque, LOCAL_WIN, mode="constant")
    den = uniform_filter(opaque, LOCAL_WIN, mode="constant")
    # Fallback for rim pixels with no opaque body in-window (floating pure-halo): whole-body
    # median (dark) so they are NOT excused by a bright local ref — biases toward catching halos.
    body_ref = float(np.median(fg_lum[a >= 255])) if (a >= 255).any() else char_solid_lum
    local_char = np.where(den > 1e-4, num / np.maximum(den, 1e-6), body_ref)
    lc_edge = local_char[edge]

    per_bg = {}
    for name in bg_names:
        key, rgb = _resolve_bg(name)
        bg_arr = np.array(rgb, dtype=np.float32)
        comp = a01[..., None] * fg + (1.0 - a01[..., None]) * bg_arr
        comp_lum = _luminance(comp)
        bg_lum = float(_luminance(bg_arr))
        edge_comp = comp_lum[edge]
        if edge_comp.size == 0:
            per_bg[key] = {"halo_ratio": 0.0, "dLum": 0.0, "bg_lum": round(bg_lum, 1)}
            continue
        dLum = float(np.median(edge_comp - lc_edge))
        halo_mask = (edge_comp > bg_lum + MARGIN) & (edge_comp > lc_edge + MARGIN)
        per_bg[key] = {"halo_ratio": round(100.0 * float(halo_mask.mean()), 2),
                       "dLum": round(dLum, 1), "bg_lum": round(bg_lum, 1)}

    # headline = max over measured non-white backgrounds
    non_white = [v["halo_ratio"] for k, v in per_bg.items() if k != "white"]
    halo_score = round(max(non_white), 2) if non_white else 0.0

    return {
        "size": list(im.size),
        "edge_px": int(edge.sum()),
        "fg_edge_lum": round(fg_edge_lum, 1),
        "char_solid_lum": round(char_solid_lum, 1),
        "backgrounds": per_bg,
        "halo_score": halo_score,
    }


def _save_composite(path, bg_name, out_dir):
    key, rgb = _resolve_bg(bg_name)
    im = Image.open(path).convert("RGBA")
    arr = np.asarray(im).astype(np.float32)
    a01 = (arr[..., 3] / 255.0)[..., None]
    comp = a01 * arr[..., :3] + (1.0 - a01) * np.array(rgb, dtype=np.float32)
    os.makedirs(out_dir, exist_ok=True)
    fname = f"on-{key}.png"
    Image.fromarray(comp.astype(np.uint8)).save(os.path.join(out_dir, fname))
    return fname


def check(input_path, bg_names=("navy", "white", "rust"), out_dir=None,
          alpha_only=False, save_proofs=True, skip_pad=False,
          pass_max=PASS_MAX, warn_max=WARN_MAX,
          fg_edge_warn=FG_EDGE_WARN, min_alpha_pad=MIN_ALPHA_PAD):
    """Run the gate. Returns a report dict with a top-level 'verdict' + 'exit_code'.

    Verdict = worst of: alpha-padding, halo score band, fg_edge_lum, opaque-islands.
    FAIL > WARN > PASS.

    skip_pad : PLAN v1.1 裁決 b — alpha-padding (貼邊 4px) is only meaningful for a
      MASTER. An equal-ratio DERIVATIVE cannot gain a new crop by scaling, so for
      derivatives pass skip_pad=True: only halo + opaque-islands are re-verified,
      padding is not (avoids spurious FAILs from sub-pixel bbox rounding on resize).
    """
    input_path = os.path.abspath(input_path)
    if out_dir is None:
        out_dir = os.path.join(os.path.dirname(input_path), "qa")

    reasons = []
    verdict = "PASS"

    def escalate(level, why):
        nonlocal verdict
        reasons.append(why)
        if SEVERITY_RANK[level] > SEVERITY_RANK[verdict]:
            verdict = level

    # --- alpha padding (§⑤) — master only; skipped for equal-ratio derivatives ---
    if skip_pad:
        pad = {"ok": True, "pads": None, "bad": None, "note": "skipped (derivative)"}
    else:
        pad = check_alpha_padding(input_path, min_pad=min_alpha_pad)
        if not pad["ok"]:
            escalate("FAIL", f"alpha padding: {pad['note']}")

    report = {
        "input": input_path,
        "alpha_padding": pad["pads"],
        "alpha_padding_ok": pad["ok"],
        "alpha_padding_checked": not skip_pad,
        "thresholds": {"pass_max": pass_max, "warn_max": warn_max,
                       "fg_edge_warn": fg_edge_warn, "min_alpha_pad": min_alpha_pad,
                       "island_min_area": ISL_MIN_AREA},
        "checked": datetime.date.today().isoformat(),
    }

    if not alpha_only:
        # --- opaque background-island sub-check (修2) — always FAIL, no WARN grace ---
        _im = Image.open(input_path).convert("RGBA")
        isl, _ = find_islands(np.asarray(_im))
        isl_total = int(sum(d["area"] for d in isl))
        report["opaque_islands"] = {
            "count": len(isl), "total_area": isl_total, "detail": isl,
        }
        if isl:
            escalate("FAIL", f"opaque background-islands: {len(isl)} region(s), "
                             f"total {isl_total}px >10px (structural residue/clip-fragment)")

        m = measure_halo(input_path, bg_names)
        report.update({
            "size": m["size"],
            "edge_px": m["edge_px"],
            "fg_edge_lum": m["fg_edge_lum"],
            "char_solid_lum": m["char_solid_lum"],
            "halo_ratio": {k: v["halo_ratio"] for k, v in m["backgrounds"].items()},
            "halo_detail": m["backgrounds"],
            "halo_score": m["halo_score"],
        })
        score = m["halo_score"]
        if score >= warn_max:
            escalate("FAIL", f"halo_score {score} >= {warn_max}")
        elif score >= pass_max:
            escalate("WARN", f"halo_score {score} in [{pass_max}, {warn_max})")
        if m["fg_edge_lum"] > fg_edge_warn:
            escalate("WARN", f"fg_edge_lum {m['fg_edge_lum']} > {fg_edge_warn} (rim RGB near white)")

        # proofs
        if save_proofs:
            proofs = {}
            for name in bg_names:
                key = BG_ALIASES.get(name, name)
                proofs[key] = _save_composite(input_path, name, out_dir)
            report["proofs"] = proofs
            report["proof_dir"] = out_dir

    if not reasons:
        reasons.append("clean: halo score in PASS band, alpha padding ok")
    report["verdict"] = verdict
    report["reasons"] = reasons
    report["exit_code"] = EXIT_CODE[verdict]

    # write report.json (unless caller only wants alpha and no out dir side-effects — we
    # still write it so asset_prep / verifiers have a machine artefact)
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "report.json"), "w") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    report["report_json"] = os.path.join(out_dir, "report.json")
    return report


def main():
    ap = argparse.ArgumentParser(
        description="White-halo + alpha-padding gate for RGBA assets (U3-calibrated).")
    ap.add_argument("--input", required=True, help="RGBA PNG to check")
    ap.add_argument("--bg", nargs="+", default=["navy", "white", "rust"],
                    help="backgrounds to composite over (navy white rust; 'orange'==rust)")
    ap.add_argument("--out", help="QA output dir (default <input_dir>/qa/)")
    ap.add_argument("--alpha-only", action="store_true",
                    help="only run §⑤ alpha-padding check (skip halo measurement)")
    ap.add_argument("--skip-pad", action="store_true",
                    help="skip alpha-padding check (equal-ratio DERIVATIVE: only halo "
                         "+ opaque-islands re-verified; 貼邊 4px is master-only, 裁決 b)")
    ap.add_argument("--json", action="store_true", help="print full report JSON to stdout")
    ap.add_argument("--pass-max", type=float, default=PASS_MAX)
    ap.add_argument("--warn-max", type=float, default=WARN_MAX)
    ap.add_argument("--fg-edge-warn", type=float, default=FG_EDGE_WARN)
    ap.add_argument("--min-alpha-pad", type=int, default=MIN_ALPHA_PAD)
    args = ap.parse_args()

    if not os.path.exists(args.input):
        ap.error(f"input not found: {args.input}")

    report = check(args.input, bg_names=args.bg, out_dir=args.out,
                   alpha_only=args.alpha_only, skip_pad=args.skip_pad,
                   pass_max=args.pass_max, warn_max=args.warn_max,
                   fg_edge_warn=args.fg_edge_warn, min_alpha_pad=args.min_alpha_pad)

    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        v = report["verdict"]
        print(f"[{v}] {args.input}")
        if not args.alpha_only:
            print(f"  halo_score={report['halo_score']}  "
                  f"halo_ratio={report['halo_ratio']}  fg_edge_lum={report['fg_edge_lum']}")
            isl = report.get("opaque_islands", {})
            print(f"  opaque_islands={isl.get('count', 0)} "
                  f"(total {isl.get('total_area', 0)}px)")
        print(f"  alpha_padding={report['alpha_padding']} ok={report['alpha_padding_ok']}"
              + ("" if report.get("alpha_padding_checked", True) else " (skipped: derivative)"))
        for r in report["reasons"]:
            print(f"  - {r}")
        if report.get("proof_dir"):
            print(f"  proofs -> {report['proof_dir']}")

    sys.exit(report["exit_code"])


if __name__ == "__main__":
    main()
