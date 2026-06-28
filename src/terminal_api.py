from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from threading import Lock
from typing import Literal

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
try:
    from .strip_recognition import analyze_strip_image
except ImportError:
    from strip_recognition import analyze_strip_image


class TerminalTestResult(BaseModel):
    report_id: str = Field(..., min_length=1)
    device_id: str = Field(..., min_length=1)
    c_line: int = Field(..., ge=0, le=1)
    t_line: int = Field(..., ge=0, le=1)
    test_status: Literal["valid", "invalid"]
    assist_result: Literal["negative_reference", "positive_suspected", "invalid"]
    risk_level: Literal["low", "medium", "high", "need_retest"]
    suggestion: str = Field(..., min_length=1)


DATA_DIR = Path(__file__).resolve().parent.parent / "data"
REPORTS_FILE = DATA_DIR / "terminal_reports.json"
REPORTS_LOCK = Lock()

MEDICAL_INSTITUTIONS = [
    {
        "name": "昆明市第三人民医院",
        "service": "HIV检测、感染科咨询、建议复检与医疗转介",
        "contact_hint": "请通过医院官方渠道预约咨询医生",
    },
    {
        "name": "云南省疾控中心",
        "service": "艾滋病防控咨询、检测指导、健康科普",
        "contact_hint": "请通过疾控官方渠道咨询",
    },
    {
        "name": "昆明医科大学第一附属医院",
        "service": "感染相关门诊、综合医疗服务、医疗转介辅助",
        "contact_hint": "请通过医院官方渠道预约咨询医生",
    },
    {
        "name": "滇池半岛诊所",
        "service": "基层健康咨询、建议复检与转介辅助",
        "contact_hint": "请以机构实际服务信息为准",
    },
]

ASSIST_RESULT_LABELS = {
    "negative_reference": "阴性参考",
    "positive_suspected": "阳性疑似",
    "invalid": "检测无效",
}

RISK_LEVEL_LABELS = {
    "low": "低风险",
    "medium": "中风险",
    "high": "高风险",
    "need_retest": "需复检",
}

STATUS_LABELS = {
    "valid": "有效",
    "invalid": "无效",
}

COMPLIANCE_NOTICE = (
    "本报告仅用于健康科普、风险评估与检测辅助，不构成医学判断、"
    "用药建议或医疗决策依据。如需专业医疗服务，请前往正规医疗机构咨询医生。"
)


def _load_reports() -> list[dict]:
    if not REPORTS_FILE.exists():
        return []
    try:
        with REPORTS_FILE.open("r", encoding="utf-8") as fp:
            data = json.load(fp)
    except (json.JSONDecodeError, OSError):
        return []
    if isinstance(data, list):
        return data
    return []


def _save_reports(reports: list[dict]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with REPORTS_FILE.open("w", encoding="utf-8") as fp:
        json.dump(reports, fp, ensure_ascii=False, indent=2)


def _next_anonymous_report_id(reports: list[dict]) -> str:
    year = datetime.now().year
    prefix = f"PG-{year}-"
    max_no = 0
    for report in reports:
        report_id = str(report.get("anonymous_report_id", ""))
        if report_id.startswith(prefix):
            try:
                max_no = max(max_no, int(report_id.replace(prefix, "", 1)))
            except ValueError:
                continue
    return f"{prefix}{max_no + 1:06d}"


def _line_status(value: int, line_name: str) -> str:
    if value == 1:
        return "已识别"
    if line_name == "T":
        return "未识别"
    return "未识别"


def _default_suggestion(payload: TerminalTestResult) -> str:
    if payload.test_status == "invalid" or payload.assist_result == "invalid":
        return "请重新检测或前往正规医疗机构检测，并咨询医生。"
    if payload.assist_result == "positive_suspected":
        return "请尽快前往正规医疗机构建议复检，并咨询医生。"
    return "建议按窗口期复检，如有疑虑请前往正规医疗机构咨询医生。"


def _build_report(payload: TerminalTestResult, reports: list[dict]) -> dict:
    now = datetime.now()
    suggestion = payload.suggestion.strip() or _default_suggestion(payload)
    anonymous_report_id = _next_anonymous_report_id(reports)
    return {
        "anonymous_report_id": anonymous_report_id,
        "report_id": anonymous_report_id,
        "terminal_report_id": payload.report_id,
        "detection_time": now.strftime("%Y-%m-%d %H:%M:%S"),
        "received_at": now.strftime("%Y-%m-%d %H:%M:%S"),
        "device_id": payload.device_id,
        "test_item": "HIV试纸检测辅助",
        "c_line": payload.c_line,
        "t_line": payload.t_line,
        "c_line_status": _line_status(payload.c_line, "C"),
        "t_line_status": _line_status(payload.t_line, "T"),
        "test_status": payload.test_status,
        "test_status_label": STATUS_LABELS.get(payload.test_status, payload.test_status),
        "assist_result": payload.assist_result,
        "assist_result_label": ASSIST_RESULT_LABELS.get(payload.assist_result, payload.assist_result),
        "risk_level": payload.risk_level,
        "risk_level_label": RISK_LEVEL_LABELS.get(payload.risk_level, payload.risk_level),
        "suggestion": suggestion,
        "next_steps": [
            suggestion,
            "若近期存在高风险暴露，建议按窗口期复检。",
            "如有不适或疑虑，请前往正规医疗机构咨询医生。",
        ],
        "nearby_medical_institutions": MEDICAL_INSTITUTIONS,
        "visibility": "仅用户本人可见",
        "privacy_policy": {
            "user_default_visibility": "检测记录默认只有用户自己可见",
            "platform_backend": "平台后台只显示匿名统计，不直接暴露个人身份",
            "doctor_access": "医生/机构只有在用户主动授权后才能查看报告",
        },
        "authorization": {
            "authorized": False,
            "auth_id": None,
            "valid_for": None,
            "message": "尚未授权医生或机构查看",
        },
        "compliance_notice": COMPLIANCE_NOTICE,
    }


def _build_statistics(reports: list[dict]) -> dict:
    today = datetime.now().strftime("%Y-%m-%d")
    today_reports = [item for item in reports if str(item.get("detection_time", item.get("received_at", ""))).startswith(today)]
    return {
        "today_upload_count": len(today_reports),
        "negative_reference_count": sum(1 for item in today_reports if item.get("assist_result") == "negative_reference"),
        "positive_suspected_count": sum(1 for item in today_reports if item.get("assist_result") == "positive_suspected"),
        "invalid_count": sum(1 for item in today_reports if item.get("assist_result") == "invalid" or item.get("test_status") == "invalid"),
        "high_risk_count": sum(1 for item in today_reports if item.get("risk_level") == "high"),
        "privacy_note": "仅显示匿名汇总数据，不显示个人身份信息。",
    }


app = FastAPI(title="Prep Guardian Terminal API", version="1.1")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)



def _analysis_to_payload(analysis: dict) -> TerminalTestResult:
    result = str(analysis.get("result", "无效"))
    c_line = 1 if analysis.get("c_line") else 0
    t_line = 1 if analysis.get("t_line") else 0
    if result == "阳性提示":
        test_status = "valid"
        assist_result = "positive_suspected"
        risk_level = "high"
        suggestion = "请尽快前往正规医疗机构建议复检，并咨询医生。"
    elif result == "阴性":
        test_status = "valid"
        assist_result = "negative_reference"
        risk_level = "low"
        suggestion = "建议按窗口期复检，如有疑虑请前往正规医疗机构咨询医生。"
    else:
        test_status = "invalid"
        assist_result = "invalid"
        risk_level = "need_retest"
        suggestion = "请重新检测或前往正规医疗机构检测，并咨询医生。"
    return TerminalTestResult(
        report_id="PG-2026-001",
        device_id="PREPGUARD-P4-001",
        c_line=c_line,
        t_line=t_line,
        test_status=test_status,
        assist_result=assist_result,
        risk_level=risk_level,
        suggestion=suggestion,
    )


def _rgb565_to_bgr(body: bytes, width: int, height: int, byteorder: str):
    import numpy as np  # type: ignore

    dtype = "<u2" if byteorder == "little" else ">u2"
    raw = np.frombuffer(body, dtype=dtype).reshape((height, width))
    r = (((raw >> 11) & 0x1F) * 255 // 31).astype(np.uint8)
    g = (((raw >> 5) & 0x3F) * 255 // 63).astype(np.uint8)
    b = ((raw & 0x1F) * 255 // 31).astype(np.uint8)
    return np.dstack((b, g, r))


def _terminal_fallback_analysis(bgr, cv2, np) -> dict:
    """ESP32 preview is tiny; detect horizontal C/T bands inside the test window."""
    h, w = bgr.shape[:2]

    # The terminal camera sees the rapid-test window upright, where C/T bands are
    # horizontal. First isolate the light-colored cassette/window area so dark
    # cables and the desk do not become false positives.
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    light = cv2.inRange(hsv, np.array([0, 0, 70]), np.array([179, 110, 255]))
    light = cv2.morphologyEx(light, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_RECT, (9, 7)))
    n, _labels, stats, _centroids = cv2.connectedComponentsWithStats(light, connectivity=8)

    roi = None
    best_area = 0
    for idx in range(1, n):
        x, y, bw, bh, area = [int(v) for v in stats[idx]]
        if area < max(400, int(w * h * 0.02)):
            continue
        if x > w * 0.75 or x + bw < w * 0.15:
            continue
        if area > best_area:
            best_area = area
            roi = (max(0, x), max(0, y), min(w, x + bw), min(h, y + bh))

    if roi is None:
        roi = (int(w * 0.18), int(h * 0.05), int(w * 0.65), int(h * 0.95))

    rx0, ry0, rx1, ry1 = roi
    # Result window is usually in the upper-middle of the cassette. Search a
    # slightly narrower region to avoid the sample well.
    sx0 = rx0 + int((rx1 - rx0) * 0.32)
    sx1 = rx0 + int((rx1 - rx0) * 0.76)
    sy0 = ry0 + int((ry1 - ry0) * 0.08)
    sy1 = ry0 + int((ry1 - ry0) * 0.58)
    sx0, sx1 = max(0, sx0), min(w, sx1)
    sy0, sy1 = max(0, sy0), min(h, sy1)

    crop = bgr[sy0:sy1, sx0:sx1]
    if crop.size > 0 and crop.shape[0] >= 8 and crop.shape[1] >= 8:
        crop_gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
        crop_hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
        # Lines can look red-purple, brown, or dark gray after RGB565/lighting.
        red_purple = (
            cv2.inRange(crop_hsv, np.array([0, 18, 20]), np.array([18, 255, 230]))
            | cv2.inRange(crop_hsv, np.array([120, 12, 20]), np.array([179, 255, 230]))
        )
        dark = cv2.inRange(crop_gray, 0, 118)
        band_mask = cv2.bitwise_or(red_purple, dark)
        band_mask = cv2.morphologyEx(band_mask, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT, (5, 1)))
        band_mask = cv2.morphologyEx(band_mask, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_RECT, (13, 2)))

        rows = band_mask.mean(axis=1) / 255.0
        smooth = cv2.blur(rows.reshape(-1, 1).astype("float32"), (1, 3)).ravel()
        peaks = []
        min_sep = max(4, crop.shape[0] // 8)
        for y, value in sorted(enumerate(smooth), key=lambda item: item[1], reverse=True):
            if value < 0.10:
                continue
            if all(abs(y - old_y) >= min_sep for old_y, _ in peaks):
                peaks.append((int(y), float(value)))
            if len(peaks) >= 2:
                break
        peaks = sorted(peaks, key=lambda item: item[0])

        candidates = []
        for y, value in peaks:
            y0 = max(0, y - 2)
            y1 = min(crop.shape[0], y + 3)
            band = band_mask[y0:y1, :]
            xs = np.where(band.max(axis=0) > 0)[0]
            if len(xs) > 0:
                x0 = int(xs.min())
                x1 = int(xs.max()) + 1
            else:
                x0 = 0
                x1 = crop.shape[1]
            candidates.append({
                "x": sx0 + x0,
                "y": sy0 + y0,
                "w": max(1, x1 - x0),
                "h": max(1, y1 - y0),
                "area": int(band.sum() / 255),
                "cx": round(float(sx0 + (x0 + x1) / 2), 2),
                "cy": round(float(sy0 + y), 2),
                "score": round(min(1.0, value * 2.2), 4),
            })

        if len(candidates) >= 2:
            c_score = float(candidates[0]["score"])
            t_score = float(candidates[1]["score"])
        elif len(candidates) == 1:
            # If only one band is present, the upper C line is normally the
            # reliable control line on this cassette orientation.
            c_score = float(candidates[0]["score"])
            t_score = 0.0
        else:
            c_score = 0.0
            t_score = 0.0

        c_line = c_score >= 0.16
        t_line = t_score >= 0.12
        if not c_line:
            result = "无效"
        elif t_line:
            result = "阳性提示"
        else:
            result = "阴性"

        return {
            "result": result,
            "c_line": bool(c_line),
            "t_line": bool(t_line),
            "c_line_score": round(c_score, 4),
            "t_line_score": round(t_score, 4),
            "test_item": "HIV1/2",
            "candidate_count": len(candidates),
            "candidates": candidates,
            "roi": {"x0": rx0, "y0": ry0, "x1": rx1, "y1": ry1},
            "window_roi": {"x0": sx0, "y0": sy0, "x1": sx1, "y1": sy1},
            "algorithm": "esp32_terminal_horizontal_band_v2",
        }

    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    purple = cv2.inRange(hsv, np.array([120, 18, 25]), np.array([179, 255, 255]))
    red1 = cv2.inRange(hsv, np.array([0, 28, 25]), np.array([14, 255, 255]))
    red2 = cv2.inRange(hsv, np.array([166, 28, 25]), np.array([179, 255, 255]))
    mask = cv2.bitwise_or(purple, cv2.bitwise_or(red1, red2))
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT, (1, 3)))
    mask = cv2.dilate(mask, cv2.getStructuringElement(cv2.MORPH_RECT, (2, 5)), iterations=1)

    n, _labels, stats, centroids = cv2.connectedComponentsWithStats(mask, connectivity=8)
    candidates = []
    min_h = max(5, int(h * 0.035))
    max_w = max(8, int(w * 0.08))
    for idx in range(1, n):
        x, y, bw, bh, area = [int(v) for v in stats[idx]]
        cx, cy = [float(v) for v in centroids[idx]]
        if area < 6:
            continue
        if bh < min_h or bw > max_w:
            continue
        if bh < bw * 0.9:
            continue
        density = area / max(float(bw * bh), 1.0)
        score = min(1.0, 0.45 * min(bh / max(h * 0.26, 1), 1.0) + 0.35 * min(area / 80.0, 1.0) + 0.20 * min(density * 2.0, 1.0))
        candidates.append({
            "x": x,
            "y": y,
            "w": bw,
            "h": bh,
            "area": area,
            "cx": round(cx, 2),
            "cy": round(cy, 2),
            "score": round(float(score), 4),
        })

    candidates = sorted(candidates, key=lambda item: item["score"], reverse=True)[:4]
    candidates = sorted(candidates, key=lambda item: item["cx"])
    if len(candidates) >= 2:
        t_score = float(candidates[0]["score"])
        c_score = float(candidates[-1]["score"])
    elif len(candidates) == 1:
        c_score = float(candidates[0]["score"])
        t_score = 0.0
    else:
        c_score = 0.0
        t_score = 0.0

    c_line = c_score >= 0.10
    t_line = t_score >= 0.10
    if not c_line:
        result = "无效"
    elif t_line:
        result = "阳性提示"
    else:
        result = "阴性"

    return {
        "result": result,
        "c_line": bool(c_line),
        "t_line": bool(t_line),
        "c_line_score": round(c_score, 4),
        "t_line_score": round(t_score, 4),
        "test_item": "HIV1/2",
        "candidate_count": len(candidates),
        "candidates": candidates,
        "algorithm": "esp32_terminal_color_band_v1",
    }


TERMINAL_TEST_ITEM_ORDER = ["HIV1/2", "HCV", "TP", "HBsAg"]


def _normalize_terminal_item(test_item: str | None) -> str:
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


def _terminal_multirow_geometry_analysis(bgr, cv2, np, test_item: str = "HIV1/2") -> dict | None:
    """Geometry-aware reader for the Wondfo-style 4-row cassette in terminal preview.

    The saved ESP32 frame shows rows from top to bottom:
    HIV1/2, HCV, TP, HBsAg. For HIV1/2, judge only the first row and sample
    two small vertical zones: T on the left, C on the right.
    """
    h, w = bgr.shape[:2]
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)

    light = cv2.inRange(hsv, np.array([0, 0, 65]), np.array([179, 125, 255]))
    light = cv2.morphologyEx(light, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_RECT, (15, 9)))
    n, _labels, stats, _centroids = cv2.connectedComponentsWithStats(light, connectivity=8)
    roi = None
    best_area = 0
    for idx in range(1, n):
        x, y, bw, bh, area = [int(v) for v in stats[idx]]
        if area < max(900, int(w * h * 0.05)):
            continue
        if area > best_area:
            best_area = area
            roi = (x, y, x + bw, y + bh)

    if roi is None:
        return None

    rx0, ry0, rx1, ry1 = roi
    rw = max(1, rx1 - rx0)
    rh = max(1, ry1 - ry0)
    if rw < w * 0.38 or rh < h * 0.45:
        return None

    item = _normalize_terminal_item(test_item)
    row_index = TERMINAL_TEST_ITEM_ORDER.index(item) if item in TERMINAL_TEST_ITEM_ORDER else 0
    row_centers = [0.40, 0.56, 0.72, 0.88]
    row_center_y = int(ry0 + rh * row_centers[min(row_index, len(row_centers) - 1)])

    # Measured from the current 460x124 terminal preview. T is left of C.
    t_center_x = int(rx0 + rw * 0.495)
    c_center_x = int(rx0 + rw * 0.540)
    zone_half_w = max(3, int(rw * 0.012))
    zone_half_h = max(7, int(rh * 0.070))

    def zone_score(center_x: int) -> tuple[float, dict]:
        x0 = max(0, center_x - zone_half_w)
        x1 = min(w, center_x + zone_half_w + 1)
        y0 = max(0, row_center_y - zone_half_h)
        y1 = min(h, row_center_y + zone_half_h + 1)
        zhsv = hsv[y0:y1, x0:x1]
        zgray = gray[y0:y1, x0:x1]
        if zhsv.size == 0:
            return 0.0, {"x0": x0, "y0": y0, "x1": x1, "y1": y1, "red": 0.0, "dark": 0.0}

        hue = zhsv[:, :, 0]
        sat = zhsv[:, :, 1]
        val = zhsv[:, :, 2]
        red_purple = (
            (sat > 28)
            & (val > 25)
            & ((hue <= 28) | (hue >= 145) | ((hue >= 115) & (hue <= 179)))
        )
        # Dark pixels help when the camera desaturates red lines, but cannot
        # alone trigger T/C. This prevents plastic shadows from becoming lines.
        red_frac = float(red_purple.mean())
        dark_frac = float((zgray < 90).mean())
        score = 0.75 * red_frac + 0.25 * max(0.0, (dark_frac - 0.50) / 0.50)
        return float(score), {
            "x0": x0,
            "y0": y0,
            "x1": x1,
            "y1": y1,
            "red": round(red_frac, 4),
            "dark": round(dark_frac, 4),
            "score": round(float(score), 4),
        }

    t_score, t_zone = zone_score(t_center_x)
    c_score, c_zone = zone_score(c_center_x)
    c_line = c_score >= 0.16
    t_line = t_score >= 0.16

    if not c_line:
        result = "无效"
    elif t_line:
        result = "阳性提示"
    else:
        result = "阴性"

    return {
        "result": result,
        "c_line": bool(c_line),
        "t_line": bool(t_line),
        "c_line_score": round(c_score, 4),
        "t_line_score": round(t_score, 4),
        "test_item": item,
        "selected_row_index": row_index,
        "detected_rows": 4,
        "roi": {"x0": rx0, "y0": ry0, "x1": rx1, "y1": ry1},
        "t_zone": t_zone,
        "c_zone": c_zone,
        "algorithm": "esp32_terminal_multirow_geometry_v1",
    }


def _terminal_structural_ct_analysis(bgr, cv2, np, test_item: str = "HIV1/2") -> dict:
    """Color-independent C/T reader for ESP32-P4 terminal frames.

    The OV2710/RGB565 terminal frame can have strong color distortion, so this
    reader ignores hue and detects C/T as narrow vertical dark structures inside
    the same test window row. It is conservative: T is valid only when it forms
    a plausible pair with C in the same row.
    """
    h, w = bgr.shape[:2]
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)

    # Keep the cassette/result area while dropping the far right image border
    # and most sample-well/desk noise. These are proportional limits, not fixed
    # pixel coordinates, so the frame can move a little between captures.
    x0 = int(w * 0.18)
    x1 = int(w * 0.58)
    y0 = int(h * 0.25)
    y1 = int(h * 0.90)
    crop = gray[y0:y1, x0:x1]
    if crop.size == 0 or crop.shape[0] < 40 or crop.shape[1] < 80:
        return {
            "result": "??",
            "c_line": False,
            "t_line": False,
            "c_line_score": 0.0,
            "t_line_score": 0.0,
            "test_item": _normalize_terminal_item(test_item),
            "candidate_count": 0,
            "algorithm": "esp32_terminal_structural_ct_v1",
            "warning": "frame too small",
        }

    # Normalize uneven light, then use black-hat morphology to extract dark
    # vertical bands. This works even when RGB565 colors are wrong.
    norm = cv2.equalizeHist(cv2.GaussianBlur(crop, (3, 3), 0))
    black = cv2.morphologyEx(norm, cv2.MORPH_BLACKHAT, cv2.getStructuringElement(cv2.MORPH_RECT, (5, 31)))
    _thr, mask = cv2.threshold(black, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT, (1, 7)))
    mask = cv2.dilate(mask, cv2.getStructuringElement(cv2.MORPH_RECT, (3, 7)), iterations=1)

    n, _labels, stats, centroids = cv2.connectedComponentsWithStats(mask, connectivity=8)
    candidates = []
    min_h = max(14, int(h * 0.060))
    max_h = max(90, int(h * 0.420))
    max_w = max(18, int(w * 0.080))
    for idx in range(1, n):
        lx, ly, bw, bh, area = [int(v) for v in stats[idx]]
        cx, cy = [float(v) for v in centroids[idx]]
        gx = lx + x0
        gy = ly + y0
        gcx = cx + x0
        gcy = cy + y0
        if area < 35:
            continue
        if bw < 2 or bw > max_w:
            continue
        if bh < min_h or bh > max_h:
            continue
        if bh < bw * 0.85:
            continue

        # True reagent bands should be darker than their immediate local
        # background. This drops borders, text fragments, and glare edges.
        pad_x = max(8, int(bw * 1.8))
        pad_y = max(8, int(bh * 0.30))
        lx0 = max(0, int(gcx) - pad_x)
        lx1 = min(w, int(gcx) + pad_x + 1)
        ly0 = max(0, int(gcy) - bh // 2 - pad_y)
        ly1 = min(h, int(gcy) + bh // 2 + pad_y + 1)
        local = gray[ly0:ly1, lx0:lx1]
        center = gray[max(0, gy):min(h, gy + bh), max(0, gx):min(w, gx + bw)]
        if local.size == 0 or center.size == 0:
            continue
        contrast = float(local.mean() - center.mean())
        if contrast < 3.5:
            continue

        density = area / max(float(bw * bh), 1.0)
        score = (
            0.36 * min(bh / max(h * 0.20, 1.0), 1.0)
            + 0.28 * min(area / 420.0, 1.0)
            + 0.24 * min(max(contrast, 0.0) / 42.0, 1.0)
            + 0.12 * min(density * 2.0, 1.0)
        )
        candidates.append({
            "x": int(gx),
            "y": int(gy),
            "w": int(bw),
            "h": int(bh),
            "area": int(area),
            "cx": float(gcx),
            "cy": float(gcy),
            "score": float(score),
            "contrast": float(contrast),
        })

    # Group candidates by row. C/T must be in the same row; this prevents C
    # lines from different projects from being combined into a false positive.
    rows = []
    row_threshold = max(16.0, h * 0.075)
    for cand in sorted(candidates, key=lambda item: item["cy"]):
        for row in rows:
            if abs(cand["cy"] - row["cy"]) <= row_threshold:
                row["items"].append(cand)
                row["cy"] = float(np.mean([item["cy"] for item in row["items"]]))
                break
        else:
            rows.append({"cy": cand["cy"], "items": [cand]})

    row_results = []
    x_merge_threshold = max(12.0, w * 0.020)
    for row in rows:
        clusters = []
        for cand in sorted(row["items"], key=lambda item: item["cx"]):
            for cluster in clusters:
                if abs(cand["cx"] - cluster["cx"]) <= x_merge_threshold:
                    cluster["members"].append(cand)
                    weights = [max(item["score"], 0.01) for item in cluster["members"]]
                    cluster["cx"] = float(np.average([item["cx"] for item in cluster["members"]], weights=weights))
                    cluster["cy"] = float(np.average([item["cy"] for item in cluster["members"]], weights=weights))
                    cluster["score"] = max(float(item["score"]) for item in cluster["members"])
                    cluster["h"] = max(int(item["h"]) for item in cluster["members"])
                    cluster["area"] = sum(int(item["area"]) for item in cluster["members"])
                    break
            else:
                clusters.append({
                    "cx": cand["cx"],
                    "cy": cand["cy"],
                    "score": cand["score"],
                    "h": cand["h"],
                    "area": cand["area"],
                    "members": [cand],
                })

        clusters = sorted(clusters, key=lambda item: item["cx"])
        pairs = []
        for left_index, left in enumerate(clusters):
            for right in clusters[left_index + 1:]:
                dx = float(right["cx"] - left["cx"])
                if dx < w * 0.025 or dx > w * 0.180:
                    continue
                if abs(float(left["cy"] - right["cy"])) > max(18.0, h * 0.080):
                    continue
                height_ratio = min(left["h"], right["h"]) / max(float(max(left["h"], right["h"])), 1.0)
                if height_ratio < 0.30:
                    continue
                pair_score = float(left["score"] + right["score"] + 0.10 * height_ratio)
                pairs.append((pair_score, left, right, dx))
        row_results.append({"cy": row["cy"], "clusters": clusters, "pairs": pairs})

    selected = None
    pair_rows = [row for row in row_results if row["pairs"]]
    strong_pair_rows = []
    for row in pair_rows:
        strong_pairs = [
            pair for pair in row["pairs"]
            if float(pair[2]["score"]) >= 0.45 and float(pair[1]["score"]) >= 0.30
        ]
        if strong_pairs:
            strong_pair_rows.append({"cy": row["cy"], "clusters": row["clusters"], "pairs": strong_pairs})

    if strong_pair_rows:
        # Pick the first row with a strong control-line candidate. Weak upper
        # marks are usually labels/glare and must not steal the HIV row.
        selected_row = sorted(strong_pair_rows, key=lambda row: row["cy"])[0]
        selected = max(selected_row["pairs"], key=lambda item: item[0])
        _pair_score, t_cluster, c_cluster, _dx = selected
        t_score = float(t_cluster["score"])
        c_score = float(c_cluster["score"])
        selected_cy = float(selected_row["cy"])
    elif pair_rows:
        selected_row = sorted(pair_rows, key=lambda row: row["cy"])[0]
        selected = max(selected_row["pairs"], key=lambda item: item[0])
        _pair_score, t_cluster, c_cluster, _dx = selected
        t_score = float(t_cluster["score"])
        c_score = float(c_cluster["score"])
        selected_cy = float(selected_row["cy"])
    else:
        # One visible band is treated as C only when it is strong enough. A lone
        # weak mark becomes invalid instead of being guessed as T.
        all_clusters = [cluster for row in row_results for cluster in row["clusters"]]
        if all_clusters:
            c_cluster = max(all_clusters, key=lambda item: item["score"])
            c_score = float(c_cluster["score"])
            t_score = 0.0
            selected_cy = float(c_cluster["cy"])
        else:
            c_score = 0.0
            t_score = 0.0
            selected_cy = 0.0

    c_line = c_score >= 0.30
    t_line = bool(c_line and t_score >= 0.34)
    if not c_line:
        result = "??"
    elif t_line:
        result = "????"
    else:
        result = "??"

    debug_rows = []
    for row in row_results:
        debug_rows.append({
            "cy": round(float(row["cy"]), 2),
            "clusters": [
                {"cx": round(float(cluster["cx"]), 2), "score": round(float(cluster["score"]), 4), "h": int(cluster["h"])}
                for cluster in row["clusters"][:8]
            ],
        })

    return {
        "result": result,
        "c_line": bool(c_line),
        "t_line": bool(t_line),
        "c_line_score": round(float(c_score), 4),
        "t_line_score": round(float(t_score), 4),
        "test_item": _normalize_terminal_item(test_item),
        "selected_row_y": round(float(selected_cy), 2),
        "detected_rows": len(row_results),
        "candidate_count": len(candidates),
        "rows": debug_rows[:6],
        "algorithm": "esp32_terminal_structural_ct_v1",
    }


def _choose_terminal_analysis(body: bytes, width: int, height: int, cv2, np) -> tuple[object, dict, str]:
    best_bgr = None
    best_analysis = None
    best_order = "little"
    best_score = -1.0
    for order in ("little", "big"):
        bgr = _rgb565_to_bgr(body, width, height, order)
        analysis = _terminal_structural_ct_analysis(bgr, cv2, np)
        score = (
            float(analysis.get("c_line_score", 0.0))
            + float(analysis.get("t_line_score", 0.0))
            + 0.015 * int(analysis.get("candidate_count", 0))
        )
        if score > best_score:
            best_bgr = bgr
            best_analysis = analysis
            best_order = order
            best_score = score
    return best_bgr, best_analysis or {}, best_order


@app.post("/api/v1/terminal/analyze-frame")
async def analyze_terminal_frame(request: Request) -> dict:
    width = int(request.headers.get("x-frame-width", "460"))
    height = int(request.headers.get("x-frame-height", "124"))
    pixel_format = request.headers.get("x-frame-format", "rgb565").lower()
    body = await request.body()
    expected = width * height * 2
    if pixel_format != "rgb565":
        raise HTTPException(status_code=400, detail="unsupported frame format")
    if len(body) != expected:
        raise HTTPException(status_code=400, detail=f"invalid frame size: got {len(body)}, expected {expected}")

    try:
        import cv2  # type: ignore
        import numpy as np  # type: ignore
    except Exception as exc:
        raise HTTPException(status_code=500, detail="OpenCV/Numpy unavailable") from exc

    bgr, fallback_analysis, byteorder = _choose_terminal_analysis(body, width, height, cv2, np)

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    frame_path = DATA_DIR / "terminal_last_frame.png"
    if not cv2.imwrite(str(frame_path), bgr):
        raise HTTPException(status_code=500, detail="failed to save frame")

    # Terminal frames are RGB565 camera frames and can have severe color shifts.
    # Use the terminal structural reader instead of the web photo color reader.
    analysis = fallback_analysis
    try:
        web_photo_analysis = analyze_strip_image(frame_path, test_item="HIV1/2")
    except Exception:
        web_photo_analysis = None
    analysis["terminal_rgb565_byteorder"] = byteorder
    if web_photo_analysis is not None:
        analysis["web_photo_analysis_debug"] = web_photo_analysis
    payload = _analysis_to_payload(analysis)
    with REPORTS_LOCK:
        reports = _load_reports()
        record = _build_report(payload, reports)
        record["opencv_analysis"] = analysis
        record["frame_source"] = "esp32p4_rgb565_preview"
        reports.append(record)
        _save_reports(reports)

    return {
        "success": True,
        "report_id": record["anonymous_report_id"],
        "c_line": int(payload.c_line),
        "t_line": int(payload.t_line),
        "test_status": payload.test_status,
        "assist_result": payload.assist_result,
        "risk_level": payload.risk_level,
        "suggestion": payload.suggestion,
        "analysis": analysis,
    }

@app.post("/api/v1/terminal/test-results")
def receive_terminal_test_result(payload: TerminalTestResult) -> dict:
    with REPORTS_LOCK:
        reports = _load_reports()
        record = _build_report(payload, reports)
        reports.append(record)
        _save_reports(reports)
    return {"success": True, "report_id": record["anonymous_report_id"]}


@app.get("/api/v1/terminal/test-results")
def list_terminal_test_results() -> dict:
    with REPORTS_LOCK:
        reports = list(reversed(_load_reports()))
    return {
        "success": True,
        "count": len(reports),
        "reports": reports,
        "statistics": _build_statistics(reports),
    }


@app.get("/api/v1/terminal/statistics")
def terminal_statistics() -> dict:
    with REPORTS_LOCK:
        reports = _load_reports()
    return {"success": True, "statistics": _build_statistics(reports)}


@app.post("/api/v1/terminal/reports/{anonymous_report_id}/authorize")
def authorize_report(anonymous_report_id: str) -> dict:
    with REPORTS_LOCK:
        reports = _load_reports()
        for report in reports:
            if report.get("anonymous_report_id") == anonymous_report_id or report.get("report_id") == anonymous_report_id:
                report["authorization"] = {
                    "authorized": True,
                    "auth_id": "AUTH-2026-001",
                    "valid_for": "24小时",
                    "message": "请将报告编号或二维码提供给正规医疗机构医生参考",
                }
                _save_reports(reports)
                return {
                    "success": True,
                    "report_id": anonymous_report_id,
                    "authorization": report["authorization"],
                }
    raise HTTPException(status_code=404, detail="report not found")


@app.get("/health")
def health() -> dict:
    return {"ok": True}


@app.get("/terminal/reports", response_class=HTMLResponse)
def terminal_reports_page() -> str:
    with REPORTS_LOCK:
        rows = list(reversed(_load_reports()))

    table_rows = "\n".join(
        "<tr>"
        f"<td>{item.get('detection_time', '')}</td>"
        f"<td>{item.get('anonymous_report_id', '')}</td>"
        f"<td>{item.get('device_id', '')}</td>"
        f"<td>{item.get('c_line_status', '')}</td>"
        f"<td>{item.get('t_line_status', '')}</td>"
        f"<td>{item.get('test_status_label', '')}</td>"
        f"<td>{item.get('assist_result_label', '')}</td>"
        f"<td>{item.get('risk_level_label', '')}</td>"
        f"<td>{item.get('visibility', '')}</td>"
        "</tr>"
        for item in rows
    )
    if not table_rows:
        table_rows = '<tr><td colspan="9">暂无 ESP32 上传数据</td></tr>'

    return f"""
<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <title>检测报告中心</title>
  <style>
    body {{ margin: 0; padding: 32px; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; background: #eef7fb; color: #102033; }}
    h1 {{ margin: 0 0 8px; }}
    .hint {{ color: #4d6475; margin-bottom: 24px; }}
    table {{ width: 100%; border-collapse: collapse; background: white; border-radius: 14px; overflow: hidden; box-shadow: 0 18px 50px rgba(15, 74, 105, 0.12); }}
    th, td {{ padding: 14px 16px; border-bottom: 1px solid #e4edf2; text-align: left; }}
    th {{ background: #0f9db5; color: white; }}
  </style>
</head>
<body>
  <h1>知药护身 · 检测报告中心</h1>
  <div class="hint">匿名检测辅助报告，仅展示用户授权范围内的信息。</div>
  <table>
    <thead><tr><th>检测时间</th><th>匿名报告编号</th><th>设备编号</th><th>C线</th><th>T线</th><th>试纸状态</th><th>辅助判断</th><th>风险等级</th><th>权限</th></tr></thead>
    <tbody>{table_rows}</tbody>
  </table>
</body>
</html>
"""


