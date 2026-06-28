"""安全预哨所终端：OpenCV试纸识别模块。

识别目标：
1. 自动从图片中寻找紫红色C/T线候选；
2. 按检测项目行（HIV1/2、HCV、TP、HBsAg）分组；
3. 只判读所选项目对应的检测窗口；
4. 输出C/T线是否存在、分值和阴性/阳性提示/无效。

说明：复杂场景（截图、倾斜、多联检卡、反光、背景纹理）仍建议保留人工确认入口。
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


TEST_ITEM_ORDER = ["HIV1/2", "HCV", "TP", "HBsAg"]


@dataclass(frozen=True)
class StripAnalysisConfig:
    min_control_score: float = 0.18
    min_test_score: float = 0.16
    row_group_ratio: float = 0.028
    min_line_height_ratio: float = 0.006
    max_line_width_ratio: float = 0.055


def _load_cv2():
    try:
        import cv2  # type: ignore
        import numpy as np  # type: ignore
        return cv2, np
    except Exception as exc:
        raise RuntimeError("OpenCV/Numpy不可用，请安装 opencv-python 和 numpy") from exc


def _normalize_item(test_item: str | None) -> str:
    if not test_item:
        return "HIV1/2"
    item = str(test_item).strip()
    aliases = {
        "HIV": "HIV1/2",
        "HIV1": "HIV1/2",
        "HIV2": "HIV1/2",
        "HIV1/2": "HIV1/2",
        "HCV": "HCV",
        "TP": "TP",
        "梅毒": "TP",
        "HBsAg": "HBsAg",
        "乙肝表面抗原": "HBsAg",
    }
    return aliases.get(item, "HIV1/2")


def _line_result(c_score: float, t_score: float, config: StripAnalysisConfig) -> tuple[bool, bool, str]:
    c_line = c_score >= config.min_control_score
    t_line = t_score >= config.min_test_score
    if not c_line:
        return False, bool(t_line), "无效"
    if t_line:
        return True, True, "阳性提示"
    return True, False, "阴性"


def _candidate_mask(img, cv2, np):
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    # Most colloidal gold / rapid-test bands are red-purple or magenta.
    purple = cv2.inRange(hsv, np.array([125, 25, 35]), np.array([179, 255, 245]))
    red1 = cv2.inRange(hsv, np.array([0, 35, 35]), np.array([12, 255, 245]))
    red2 = cv2.inRange(hsv, np.array([170, 35, 35]), np.array([179, 255, 245]))
    mask = cv2.bitwise_or(purple, cv2.bitwise_or(red1, red2))

    # Emphasize vertical narrow bands; remove small noise.
    vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 9))
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, vertical_kernel)
    mask = cv2.dilate(mask, cv2.getStructuringElement(cv2.MORPH_RECT, (2, 5)), iterations=1)
    return mask


def _line_candidates(img, cv2, np):
    h, w = img.shape[:2]
    mask = _candidate_mask(img, cv2, np)
    n, labels, stats, centroids = cv2.connectedComponentsWithStats(mask, connectivity=8)

    candidates = []
    min_h = max(8, int(h * 0.006))
    max_w = max(12, int(w * 0.055))
    for idx in range(1, n):
        x, y, bw, bh, area = [int(v) for v in stats[idx]]
        cx, cy = [float(v) for v in centroids[idx]]
        if area < 12:
            continue
        if bh < min_h or bw > max_w:
            continue
        if bh < bw * 1.2:
            continue
        # Ignore phone UI/top text and left-side blood drops/sample wells.
        if cy < h * 0.25 or cx < w * 0.22:
            continue
        density = area / max(float(bw * bh), 1.0)
        score = min(1.0, 0.45 * min(bh / 45.0, 1.0) + 0.35 * min(area / 220.0, 1.0) + 0.20 * min(density * 2.0, 1.0))
        candidates.append({
            "x": x,
            "y": y,
            "w": bw,
            "h": bh,
            "area": area,
            "cx": cx,
            "cy": cy,
            "score": float(score),
        })
    return sorted(candidates, key=lambda c: (c["cy"], c["cx"]))


def _group_rows(candidates, image_height: int, np):
    if not candidates:
        return []

    threshold = max(18.0, image_height * 0.028)
    rows = []
    for cand in candidates:
        placed = False
        for row in rows:
            if abs(cand["cy"] - row["cy"]) <= threshold:
                row["items"].append(cand)
                row["cy"] = float(np.mean([x["cy"] for x in row["items"]]))
                placed = True
                break
        if not placed:
            rows.append({"cy": cand["cy"], "items": [cand]})

    out = []
    for row in rows:
        items = sorted(row["items"], key=lambda c: c["cx"])
        # Keep plausible test-window bands: at most the strongest 2 by score if noisy.
        if len(items) > 2:
            items = sorted(items, key=lambda c: c["score"], reverse=True)[:2]
            items = sorted(items, key=lambda c: c["cx"])
        out.append({
            "cy": float(np.mean([x["cy"] for x in items])),
            "items": items,
        })
    return sorted(out, key=lambda row: row["cy"])


def _select_row(rows, test_item: str):
    if not rows:
        return None, None
    item = _normalize_item(test_item)
    expected_index = TEST_ITEM_ORDER.index(item) if item in TEST_ITEM_ORDER else 0
    if len(rows) >= len(TEST_ITEM_ORDER):
        return rows[min(expected_index, len(rows) - 1)], expected_index
    # Fallback for single-strip or partially detected images.
    return rows[min(expected_index, len(rows) - 1)], min(expected_index, len(rows) - 1)


def analyze_strip_image(
    image_path: str | Path,
    config: StripAnalysisConfig | None = None,
    test_item: str | None = "HIV1/2",
) -> dict:
    """识别指定检测项目的C/T线并返回结构化结果。"""
    cv2, np = _load_cv2()
    config = config or StripAnalysisConfig()
    img = cv2.imread(str(image_path))
    if img is None:
        raise ValueError(f"无法读取图片：{image_path}")

    h, w = img.shape[:2]
    candidates = _line_candidates(img, cv2, np)
    rows = _group_rows(candidates, h, np)
    selected_row, selected_index = _select_row(rows, _normalize_item(test_item))

    if not selected_row:
        c_score = 0.0
        t_score = 0.0
        c_line, t_line, result = _line_result(c_score, t_score, config)
        return {
            "result": result,
            "c_line": c_line,
            "t_line": t_line,
            "c_line_score": c_score,
            "t_line_score": t_score,
            "test_item": _normalize_item(test_item),
            "selected_row_index": selected_index,
            "detected_rows": len(rows),
            "algorithm": "multi_row_color_band_v2",
            "warning": "未检测到可靠C/T线候选",
        }

    items = selected_row["items"]
    if len(items) >= 2:
        # On common Wondfo-style cards the T marker is left of C.
        t_score = max(float(items[0]["score"]), 0.0)
        c_score = max(float(items[-1]["score"]), 0.0)
    else:
        # One visible band in a valid rapid test is typically the control line.
        c_score = max(float(items[0]["score"]), 0.0)
        t_score = 0.0

    c_line, t_line, result = _line_result(c_score, t_score, config)
    row_box = {
        "x_min": int(min(x["x"] for x in items)),
        "x_max": int(max(x["x"] + x["w"] for x in items)),
        "y_min": int(min(x["y"] for x in items)),
        "y_max": int(max(x["y"] + x["h"] for x in items)),
    }

    return {
        "result": result,
        "c_line": bool(c_line),
        "t_line": bool(t_line),
        "c_line_score": round(float(c_score), 4),
        "t_line_score": round(float(t_score), 4),
        "test_item": _normalize_item(test_item),
        "selected_row_index": selected_index,
        "detected_rows": len(rows),
        "row_box": row_box,
        "candidate_count": len(candidates),
        "algorithm": "multi_row_color_band_v2",
    }