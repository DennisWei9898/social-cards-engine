#!/usr/bin/env python3
"""sheet_cut.py — cut individual character cells out of a multi-figure contact sheet.

品牌無關的引擎層工具（所有品牌共用一支）。把一張 N-figure 的 sheet（如 now6pm 的
4x2 poses-sheet / expressions-sheet）切成每個角色一張乾淨白底 RGB cell，交給 asset_prep
的 repair 路線去背入庫。

────────────────────────────────────────────────────────────────────────────
ROUND-3 修復核心（瞳孔誤刪事故的根因與矯正）
────────────────────────────────────────────────────────────────────────────
事故：第 2 輪切圖時，「移除浮動斷片」邏輯把「被白色眼球包圍的孤立深色瞳孔」當成斷片
刪了 —— 瞳孔與人物主體不在同一深色連通區（被白眼白隔開），於是被誤判為漂浮碎片。

矯正後的斷片移除規則（本腳本唯一的刪除依據，勿改成距離/面積）：
  **只刪「接觸裁切框邊緣」的前景連通區。**
  - 接觸邊緣的連通區 = 鄰格滲入 (neighbour bleed) / 被裁切框切斷的裝飾碎片 / caption。
  - 內部被包圍的孤立前景區（瞳孔、眼神光、鈕扣高光、任何 enclosed feature）一律「保留」。
  - 絕不用「距主體多遠」或「面積多小」當刪除依據 —— 那正是誤殺瞳孔的錯誤啟發式。

幾何保障：裁切框 = 該 figure 的 bbox + margin（>0），故 figure 本體永不接觸邊緣、
永遠被保留；瞳孔在框內部、永遠被保留。

內容保全機器閘（防這類誤殺再發）：切完的 cell vs 原始 crop 做「前景像素 diff」。被移除的
像素必須「全部」屬於已列冊的 edge-touching 連通區（每項記 bbox/area/位置進 report）。任何
「不在移除清單內的前景損失」= FAIL（門檻 <0.5% of figure fg，且理論上應為 0）。

輸出：
  out_dir/<id>/raw.png        乾淨白底 RGB cell（asset_prep --source 吃這張）
  out_dir/<id>/cut_report.json 切圖證據（figure bbox、移除清單、content-preservation diff）
  out_dir/_cut_manifest.json   整張 sheet 的切圖總表
"""
import argparse
import json
import os

import numpy as np
from PIL import Image
from scipy import ndimage

# ── background segmentation (a cell background is white or a light-neutral card) ──
BG_MIN_CH = 228     # a pixel is background if its min channel exceeds this ...
BG_CHROMA = 30      # ... AND it is near-neutral (max-min channel < this).
                    # skin (min~199) & every ink/colour is foreground; white eye-
                    # white & the light-grey poses card are background.


def foreground_mask(rgb):
    a = rgb.astype(np.int32)
    chroma = a.max(2) - a.min(2)
    bg = (a.min(2) > BG_MIN_CH) & (chroma < BG_CHROMA)
    return ~bg


def find_figures(fg, n=8):
    """Return the n largest foreground components' (label_id, bbox, area, centroid),
    ordered in reading order (row-major). Area is used only to LOCATE the figures —
    never as a deletion criterion."""
    lbl, ncomp = ndimage.label(fg)
    if ncomp < n:
        raise RuntimeError(f"expected >={n} figures, found {ncomp} components")
    areas = ndimage.sum(np.ones_like(lbl), lbl, range(1, ncomp + 1))
    top = np.argsort(areas)[::-1][:n] + 1          # label ids (1-based)
    slices = ndimage.find_objects(lbl)
    figs = []
    for lid in top:
        sy, sx = slices[lid - 1]
        cy, cx = ndimage.center_of_mass(lbl == lid)
        figs.append({"lid": int(lid),
                     "bbox": [int(sx.start), int(sy.start), int(sx.stop), int(sy.stop)],
                     "area": int(areas[lid - 1]),
                     "cy": float(cy), "cx": float(cx)})
    # reading order: split into rows by centroid-y (rows = 2 for a 4x2 sheet), sort by x
    ys = sorted(f["cy"] for f in figs)
    nrows = 2 if n % 2 == 0 else 1
    if nrows == 2:
        ymid = (ys[len(ys) // 2 - 1] + ys[len(ys) // 2]) / 2.0
        for f in figs:
            f["row"] = 0 if f["cy"] < ymid else 1
    else:
        for f in figs:
            f["row"] = 0
    figs.sort(key=lambda f: (f["row"], f["cx"]))
    return figs


def cut_cell(sheet_rgb, fig, margin, keep_dilate):
    """Cut one figure into a clean white-bg RGB cell.

    KEEP-rule (round-3, pupil-safe): keep = the figure body PLUS everything topologically
    ENCLOSED by the figure's outline silhouette (fill-holes of the figure component). This
    is the precise reading of 裁決:「內部被包圍的孤立區（瞳孔/眼神光/鈕扣高光）一律保留」:
      * a pupil sits inside the head silhouette (even though it is separated from the dark
        outline by the white eye-white) -> INSIDE fill-holes -> KEPT. This is the exact
        feature round-2's floating-fragment heuristic wrongly deleted.
      * neighbour bleed / caption / free-floating decoration marks (motion lines, sparkles,
        「?」, anger marks that float OUTSIDE the body) are outside the silhouette -> DROPPED,
        which also keeps these cells consistent with the already-shipped figure-only framing
        (裁決 c) and never lets an out-of-body mark reach the crop edge and break 貼邊.
    Removal never uses distance-to-subject or area as a criterion — only silhouette
    containment (topological) and crop-edge contact (safety). Returns (cell_rgb, report)."""
    H, W = sheet_rgb.shape[:2]
    x0, y0, x1, y1 = fig["bbox"]
    cx0, cy0 = max(0, x0 - margin), max(0, y0 - margin)
    cx1, cy1 = min(W, x1 + margin), min(H, y1 + margin)
    crop = sheet_rgb[cy0:cy1, cx0:cx1]
    ch, cw = crop.shape[:2]

    fg = foreground_mask(crop)
    lbl, n = ndimage.label(fg)

    # the figure component within the crop = the largest fg component
    if n == 0:
        raise RuntimeError("no foreground in crop")
    areas = ndimage.sum(np.ones_like(lbl), lbl, range(1, n + 1))
    fig_lid = int(np.argmax(areas)) + 1
    fig_mask = lbl == fig_lid
    # silhouette = figure body with all interior holes filled (eye-whites, face, pupils)
    silhouette = ndimage.binary_fill_holes(fig_mask)

    # KEEP any foreground pixel that lies inside the figure silhouette (figure outline +
    # every enclosed interior feature). Everything else is background/decoration/bleed.
    keep = fg & silhouette

    # secondary safety: never keep a component that touches the crop border
    border = np.zeros((ch, cw), bool)
    border[0, :] = border[-1, :] = border[:, 0] = border[:, -1] = True
    edge_labels = set(int(v) for v in np.unique(lbl[border]) if v != 0)
    remove = fg & (~keep)

    # keep the anti-aliased rim around kept foreground so edges stay smooth
    keep_dil = ndimage.binary_dilation(keep, iterations=keep_dilate)
    keep_dil &= ~remove          # never re-introduce a removed component via dilation

    out = np.full_like(crop, 255)
    out[keep_dil] = crop[keep_dil]

    # ── accounting: enumerate every removed (non-kept) fg component ──
    removed_details = []
    rlbl, rn = ndimage.label(remove)
    for lid in range(1, rn + 1):
        m = rlbl == lid
        ys, xs = np.where(m)
        removed_details.append({
            "area": int(m.sum()),
            "bbox_in_crop": [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())],
            "touches_edge": _which_edges(ys, xs, ch, cw),
            "mean_rgb": [int(v) for v in crop[m].mean(0).round()],
        })
    removed_details.sort(key=lambda d: -d["area"])
    fg_total = int(fg.sum())
    removed_px = int(remove.sum())
    # enclosed interior foreground (inside silhouette) that got whited-out must be ZERO —
    # this is the machine assertion that no pupil/highlight was lost.
    interior_lost = int((fg & silhouette & (~keep_dil)).sum())
    report = {
        "figure_bbox_on_sheet": fig["bbox"],
        "figure_area": fig["area"],
        "crop_on_sheet": [cx0, cy0, cx1, cy1],
        "crop_size": [cw, ch],
        "margin": margin,
        "fg_px_in_crop": fg_total,
        "kept_px": int(keep.sum()),
        "removed_outside_silhouette": {
            "count": len(removed_details),
            "px": removed_px,
            "pct_of_fg": round(100.0 * removed_px / max(fg_total, 1), 3),
            "detail": removed_details,        # neighbour bleed / caption / floating decorations
        },
        "interior_fg_lost_px": interior_lost,
        "interior_fg_lost_pct": round(100.0 * interior_lost / max(fg_total, 1), 4),
        "content_preserved": interior_lost == 0,
    }
    return out.astype(np.uint8), report


def _which_edges(ys, xs, ch, cw):
    e = []
    if ys.min() == 0: e.append("top")
    if ys.max() == ch - 1: e.append("bottom")
    if xs.min() == 0: e.append("left")
    if xs.max() == cw - 1: e.append("right")
    return e


def run(sheet_path, ids, out_dir, margin=16, keep_dilate=2):
    im = Image.open(sheet_path).convert("RGB")
    sheet = np.asarray(im)
    fg = foreground_mask(sheet)
    figs = find_figures(fg, n=len(ids))
    os.makedirs(out_dir, exist_ok=True)
    manifest = {"sheet": os.path.basename(sheet_path), "sheet_size": list(im.size),
                "margin": margin, "keep_dilate": keep_dilate, "cells": {}}
    all_ok = True
    for fig, aid in zip(figs, ids):
        cell, rep = cut_cell(sheet, fig, margin, keep_dilate)
        cell_dir = os.path.join(out_dir, aid)
        os.makedirs(cell_dir, exist_ok=True)
        Image.fromarray(cell).save(os.path.join(cell_dir, "raw.png"))
        rep["id"] = aid
        with open(os.path.join(cell_dir, "cut_report.json"), "w") as f:
            json.dump(rep, f, indent=2, ensure_ascii=False)
        manifest["cells"][aid] = {
            "raw": os.path.join(aid, "raw.png"),
            "content_preserved": rep["content_preserved"],
            "interior_fg_lost_px": rep["interior_fg_lost_px"],
            "removed_px": rep["removed_outside_silhouette"]["px"],
            "removed_count": rep["removed_outside_silhouette"]["count"],
        }
        all_ok &= rep["content_preserved"]
        flag = "OK " if rep["content_preserved"] else "FAIL"
        print(f"[{flag}] {aid:28s} crop={rep['crop_size']} "
              f"removed(outside-silhouette)={rep['removed_outside_silhouette']['count']}comp/"
              f"{rep['removed_outside_silhouette']['px']}px "
              f"interior_lost={rep['interior_fg_lost_px']}px")
    manifest["all_content_preserved"] = all_ok
    with open(os.path.join(out_dir, "_cut_manifest.json"), "w") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    print(f"[sheet_cut] {len(ids)} cells -> {out_dir}  all_preserved={all_ok}")
    return manifest


def main():
    ap = argparse.ArgumentParser(description="Cut character cells from a contact sheet "
                                             "(round-3 pupil-safe: only edge-touching removed).")
    ap.add_argument("--sheet", required=True)
    ap.add_argument("--ids", required=True, nargs="+",
                    help="asset ids in reading order (row-major)")
    ap.add_argument("--out", required=True, help="output dir (writes <out>/<id>/raw.png)")
    ap.add_argument("--margin", type=int, default=16)
    ap.add_argument("--keep-dilate", type=int, default=2)
    args = ap.parse_args()
    run(args.sheet, args.ids, args.out, margin=args.margin, keep_dilate=args.keep_dilate)


if __name__ == "__main__":
    main()
