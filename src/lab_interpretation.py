# 实验室指标解读：CD4 / VL / eGFR / ALT / 血常规等分级与临床建议。
# 非法输入按项目约定：返回安全默认值并 warnings.warn。
import warnings

import numpy as np


# ---- 通用数值校验 ----
def _to_float(value, name="数值", default=None):
    """转 float，失败时 warn 并返回 default。"""
    try:
        v = float(value)
        if np.isnan(v):
            raise ValueError("nan")
        return v
    except (ValueError, TypeError):
        warnings.warn(f"{name} 输入非法，使用默认值 {default}", UserWarning)
        return default


def _norm_sex(sex):
    """规范化性别为 'male' / 'female'，未知按 male 处理并 warn。"""
    if sex is None:
        return "male"
    s = str(sex).strip().lower()
    if s in ("male", "m", "男", "男性"):
        return "male"
    if s in ("female", "f", "女", "女性"):
        return "female"
    warnings.warn(f"未识别的性别：{sex}，按 male 处理", UserWarning)
    return "male"


# ---- CD4 计数分级 ----
def interpret_cd4(cd4):
    """CD4+ T 淋巴细胞计数（cells/µL）分级与临床意义。

    返回 dict：{value, stage, level, meaning, action}
    分级：>=500 正常；350-499 轻度抑制；200-349 中度抑制；
    <200 重度抑制（AIDS 定义阈值，机会性感染高风险）。
    """
    v = _to_float(cd4, "CD4 计数", default=None)
    if v is None or v < 0:
        if v is not None and v < 0:
            warnings.warn("CD4 计数不能为负，按非法处理", UserWarning)
        return {
            "value": None, "stage": "unknown", "level": "无法判定",
            "meaning": "输入无效", "action": "请复测",
        }
    if v >= 500:
        stage, level = "normal", "正常"
        meaning = "免疫功能基本正常"
        action = "常规随访"
    elif v >= 350:
        stage, level = "mild", "轻度免疫抑制"
        meaning = "免疫功能轻度下降"
        action = "加强随访，评估抗病毒治疗"
    elif v >= 200:
        stage, level = "moderate", "中度免疫抑制"
        meaning = "机会性感染风险上升"
        action = "尽快启动/强化抗病毒治疗"
    else:
        stage, level = "severe", "重度免疫抑制"
        meaning = "达 AIDS 定义阈值，机会性感染高风险"
        action = "立即转诊感染科，启动 ART 与机会性感染预防"
    return {
        "value": v, "stage": stage, "level": level,
        "meaning": meaning, "action": action,
    }


# ---- HIV 病毒载量 ----
def viral_load_log10(copies):
    """病毒载量（copies/mL）转 log10；<=0 返回 0.0 并 warn。"""
    v = _to_float(copies, "病毒载量", default=None)
    if v is None:
        return 0.0
    if v <= 0:
        warnings.warn("病毒载量需为正数，log10 计为 0", UserWarning)
        return 0.0
    return round(float(np.log10(v)), 2)


def interpret_viral_load(copies, lod=50):
    """HIV RNA 病毒载量解读。

    lod: 检测下限（默认 50 copies/mL）。
    返回 dict：{value, log10, category, level, suppressed, meaning}
    分级：< lod 检测不到（病毒学抑制）；lod-1000 低水平病毒血症；
    1000-100000 中等；>100000 高病毒血症。
    """
    v = _to_float(copies, "病毒载量", default=None)
    if v is None or v < 0:
        if v is not None and v < 0:
            warnings.warn("病毒载量不能为负", UserWarning)
        return {
            "value": None, "log10": None, "category": "unknown",
            "level": "无法判定", "suppressed": False, "meaning": "输入无效",
        }
    log10 = viral_load_log10(v) if v > 0 else 0.0
    if v < lod:
        category, level, suppressed = "undetectable", "检测不到", True
        meaning = "达病毒学抑制（U=U，不可传染水平）"
    elif v < 1000:
        category, level, suppressed = "low", "低水平病毒血症", False
        meaning = "需复查并评估依从性/耐药"
    elif v < 100000:
        category, level, suppressed = "moderate", "中等病毒血症", False
        meaning = "病毒控制不佳，评估治疗方案"
    else:
        category, level, suppressed = "high", "高病毒血症", False
        meaning = "病毒复制活跃，传播与进展风险高"
    return {
        "value": v, "log10": log10, "category": category,
        "level": level, "suppressed": suppressed, "meaning": meaning,
    }


# ---- 肾功能：eGFR 与肌酐清除率 ----
def egfr_ckd_epi(creatinine_mg_dl, age, sex):
    """CKD-EPI（2009）公式估算 eGFR（mL/min/1.73m²）。

    creatinine_mg_dl: 血肌酐 mg/dL。返回 float（保留 1 位），非法返回 None。
    """
    scr = _to_float(creatinine_mg_dl, "血肌酐", default=None)
    a = _to_float(age, "年龄", default=None)
    if scr is None or a is None or scr <= 0 or a <= 0:
        warnings.warn("eGFR 计算输入非法", UserWarning)
        return None
    s = _norm_sex(sex)
    if s == "female":
        kappa, alpha, sex_factor = 0.7, -0.329, 1.018
    else:
        kappa, alpha, sex_factor = 0.9, -0.411, 1.0
    ratio = scr / kappa
    egfr = (141.0
            * (min(ratio, 1.0) ** alpha)
            * (max(ratio, 1.0) ** -1.209)
            * (0.993 ** a)
            * sex_factor)
    return round(egfr, 1)


def creatinine_clearance_cg(creatinine_mg_dl, age, weight_kg, sex):
    # Cockcroft-Gault 公式估算肌酐清除率（mL/min）。
    scr = _to_float(creatinine_mg_dl, "血肌酐", default=None)
    a = _to_float(age, "年龄", default=None)
    w = _to_float(weight_kg, "体重", default=None)
    if scr is None or a is None or w is None or scr <= 0 or a <= 0 or w <= 0:
        warnings.warn("Cockcroft-Gault 计算输入非法", UserWarning)
        return None
    crcl = (140.0 - a) * w / (72.0 * scr)
    if _norm_sex(sex) == "female":
        crcl *= 0.85
    return round(crcl, 1)


def stage_egfr(egfr):
    """按 KDIGO 对 eGFR 做 CKD 分期。

    返回 dict：{value, stage, level, action}
    G1 >=90；G2 60-89；G3a 45-59；G3b 30-44；G4 15-29；G5 <15。
    """
    v = _to_float(egfr, "eGFR", default=None)
    if v is None or v < 0:
        return {"value": None, "stage": "unknown", "level": "无法判定", "action": "请复测"}
    if v >= 90:
        stage, level, action = "G1", "正常或偏高", "常规随访"
    elif v >= 60:
        stage, level, action = "G2", "轻度下降", "常规随访，留意趋势"
    elif v >= 45:
        stage, level, action = "G3a", "轻-中度下降", "评估含 TDF 方案，加强监测"
    elif v >= 30:
        stage, level, action = "G3b", "中-重度下降", "避免/停用 TDF，肾内科评估"
    elif v >= 15:
        stage, level, action = "G4", "重度下降", "停用肾毒性药，转诊肾内科"
    else:
        stage, level, action = "G5", "肾衰竭", "立即转诊，评估替代治疗"
    return {"value": v, "stage": stage, "level": level, "action": action}


def interpret_creatinine(creatinine_mg_dl, sex):
    """血肌酐异常判定（按性别参考上限）。

    参考上限：男 1.3 mg/dL，女 1.1 mg/dL。
    返回 dict：{value, abnormal, level}
    """
    v = _to_float(creatinine_mg_dl, "血肌酐", default=None)
    if v is None or v < 0:
        return {"value": None, "abnormal": False, "level": "无法判定"}
    upper = 1.3 if _norm_sex(sex) == "male" else 1.1
    if v < 0.5:
        return {"value": v, "abnormal": True, "level": "偏低"}
    if v <= upper:
        return {"value": v, "abnormal": False, "level": "正常"}
    if v <= upper * 1.5:
        return {"value": v, "abnormal": True, "level": "轻度升高"}
    if v <= upper * 3.0:
        return {"value": v, "abnormal": True, "level": "中度升高"}
    return {"value": v, "abnormal": True, "level": "重度升高"}


# ---- 肝功能：ALT/AST 与胆红素（CTCAE 简化） ----
def grade_alt(alt, uln=40):
    """ALT/AST 按 CTCAE 简化分级（基于 ULN 倍数）。

    uln: 正常值上限（默认 40 U/L）。
    返回 dict：{value, grade, level, ratio}
    G0 <=ULN；G1 1-3×；G2 3-5×；G3 5-20×；G4 >20×。
    """
    v = _to_float(alt, "转氨酶", default=None)
    if v is None or v < 0:
        return {"value": None, "grade": None, "level": "无法判定", "ratio": None}
    ratio = round(v / uln, 2)
    if v <= uln:
        grade, level = 0, "正常"
    elif v <= 3 * uln:
        grade, level = 1, "轻度升高"
    elif v <= 5 * uln:
        grade, level = 2, "中度升高"
    elif v <= 20 * uln:
        grade, level = 3, "重度升高"
    else:
        grade, level = 4, "极重度升高"
    return {"value": v, "grade": grade, "level": level, "ratio": ratio}


def grade_bilirubin(bilirubin, uln=1.2):
    """总胆红素按 CTCAE 简化分级（mg/dL，基于 ULN 倍数）。

    G0 <=ULN；G1 1-1.5×；G2 1.5-3×；G3 3-10×；G4 >10×。
    """
    v = _to_float(bilirubin, "胆红素", default=None)
    if v is None or v < 0:
        return {"value": None, "grade": None, "level": "无法判定", "ratio": None}
    ratio = round(v / uln, 2)
    if v <= uln:
        grade, level = 0, "正常"
    elif v <= 1.5 * uln:
        grade, level = 1, "轻度升高"
    elif v <= 3 * uln:
        grade, level = 2, "中度升高"
    elif v <= 10 * uln:
        grade, level = 3, "重度升高"
    else:
        grade, level = 4, "极重度升高"
    return {"value": v, "grade": grade, "level": level, "ratio": ratio}


# ---- 血液学：血红蛋白与血小板 ----
def grade_hemoglobin(hb, sex):
    """血红蛋白贫血分级（g/dL，按性别参考下限）。

    分级阈值（WHO/CTCAE 简化）：>=下限 正常；
    轻度 >=10；中度 8-10；重度 <8。
    """
    v = _to_float(hb, "血红蛋白", default=None)
    if v is None or v < 0:
        return {"value": None, "grade": None, "level": "无法判定"}
    lower = 13.0 if _norm_sex(sex) == "male" else 12.0
    if v >= lower:
        return {"value": v, "grade": 0, "level": "正常"}
    if v >= 10.0:
        return {"value": v, "grade": 1, "level": "轻度贫血"}
    if v >= 8.0:
        return {"value": v, "grade": 2, "level": "中度贫血"}
    return {"value": v, "grade": 3, "level": "重度贫血"}


def grade_platelets(plt):
    """血小板减少分级（×10⁹/L，CTCAE 简化）。

    >=150 正常；75-149 G1；50-74 G2；25-49 G3；<25 G4。
    """
    v = _to_float(plt, "血小板", default=None)
    if v is None or v < 0:
        return {"value": None, "grade": None, "level": "无法判定"}
    if v >= 150:
        return {"value": v, "grade": 0, "level": "正常"}
    if v >= 75:
        return {"value": v, "grade": 1, "level": "轻度减少"}
    if v >= 50:
        return {"value": v, "grade": 2, "level": "中度减少"}
    if v >= 25:
        return {"value": v, "grade": 3, "level": "重度减少"}
    return {"value": v, "grade": 4, "level": "极重度减少"}


# ---- HBV 共感染标志物 ----
def interpret_hbv(hbsag, anti_hbs=None, anti_hbc=None):
    # 根据乙肝两对半核心标志物解读 HBV 状态。
    def b(x):
        return bool(x) if x is not None else None

    sag, shab, chab = b(hbsag), b(anti_hbs), b(anti_hbc)

    if sag is None:
        warnings.warn("HBsAg 未提供，无法判定 HBV 状态", UserWarning)
        return {"status": "unknown", "level": "信息不足", "note": "需补充 HBsAg"}

    if sag is True:
        return {
            "status": "chronic_or_acute",
            "level": "HBV 感染",
            "note": "HBsAg 阳性，提示现症感染；PrEP 选含替诺福韦方案并监测肝功能，避免突然停药",
        }
    # HBsAg 阴性
    if shab is True and chab is True:
        return {"status": "recovered", "level": "既往感染已恢复", "note": "具免疫力"}
    if shab is True and (chab is False or chab is None):
        return {"status": "vaccinated", "level": "疫苗接种免疫", "note": "具免疫力"}
    if chab is True and (shab is False or shab is None):
        return {
            "status": "isolated_anti_hbc",
            "level": "单独核心抗体阳性",
            "note": "可能既往感染或隐匿感染，建议 HBV DNA 复查",
        }
    return {
        "status": "susceptible",
        "level": "易感（无免疫）",
        "note": "建议接种乙肝疫苗",
    }


# ---- 参考区间按性别 / 年龄调整 ----
def reference_range(analyte, sex=None, age=None):
    # 返回指定指标的参考区间 (low, high)，按性别/年龄调整。 支持 analyte: 'creatinine'(mg/dL), 'hemoglobin…
    key = str(analyte).strip().lower()
    s = _norm_sex(sex) if sex is not None else None
    a = _to_float(age, "年龄", default=None) if age is not None else None

    if key == "creatinine":
        if s == "female":
            return (0.5, 1.1)
        return (0.7, 1.3)
    if key == "hemoglobin":
        if s == "female":
            return (12.0, 16.0)
        return (13.0, 17.0)
    if key == "alt":
        # 老年人上限略放宽
        high = 40.0
        if a is not None and a >= 65:
            high = 45.0
        return (7.0, high)
    if key == "platelets":
        return (150.0, 400.0)

    warnings.warn(f"未知指标：{analyte}，无参考区间", UserWarning)
    return (None, None)


# ---- 随访检验时间表 ----
def followup_schedule(regimen_type="prep_oral"):
    # 生成随访检验时间表（相对基线的周/月）。
    rt = str(regimen_type).strip().lower()
    if rt == "pep":
        return [
            {"visit": "基线(0周)", "hiv_test": True, "renal": True,
             "other": "肝功能、HBV/HCV、肌酐"},
            {"visit": "4-6周", "hiv_test": True, "renal": False, "other": "评估依从性"},
            {"visit": "12周", "hiv_test": True, "renal": False, "other": "最终 HIV 排查"},
        ]
    if rt == "prep_injectable":
        return [
            {"visit": "基线(0周)", "hiv_test": True, "renal": True,
             "other": "HBV、肝肾功能"},
            {"visit": "首次注射后4周", "hiv_test": True, "renal": False, "other": "第2针"},
            {"visit": "每8周", "hiv_test": True, "renal": False,
             "other": "后续每次注射前 HIV 检测"},
        ]
    if rt != "prep_oral":
        warnings.warn(f"未知方案类型：{regimen_type}，按口服 PrEP 处理", UserWarning)
    return [
        {"visit": "基线(0周)", "hiv_test": True, "renal": True,
         "other": "HBV、肝肾功能、STI 筛查"},
        {"visit": "1个月", "hiv_test": True, "renal": True, "other": "依从性评估"},
        {"visit": "每3个月", "hiv_test": True, "renal": True,
         "other": "HIV、肾功能、STI 复查"},
    ]


# ---- 停药 / 转诊规则判定 ----
def needs_action(*, egfr=None, alt_grade=None, hb_grade=None,
                 plt_grade=None, viral_load_category=None):
    """综合多项指标判定是否需要停药 / 转诊 / 加强监测。

    返回 dict：{action, reasons}
    action ∈ {"continue", "monitor", "refer", "stop"}（严重度递增）。
    """
    reasons = []
    severity = 0  # 0 continue,1 monitor,2 refer,3 stop

    def escalate(level, reason):
        nonlocal severity
        severity = max(severity, level)
        reasons.append(reason)

    if egfr is not None:
        e = _to_float(egfr, "eGFR", default=None)
        if e is not None:
            if e < 30:
                escalate(3, "eGFR<30，需停用 TDF 并转诊肾内科")
            elif e < 50:
                escalate(2, "eGFR<50，含 TDF 方案需评估转诊")
            elif e < 60:
                escalate(1, "eGFR 偏低，加强肾功能监测")

    if alt_grade is not None:
        g = _to_float(alt_grade, "ALT 分级", default=None)
        if g is not None:
            if g >= 3:
                escalate(3, "转氨酶 ≥G3，建议停药并评估肝损伤")
            elif g == 2:
                escalate(2, "转氨酶 G2，需复查与评估")
            elif g == 1:
                escalate(1, "转氨酶轻度升高，监测")

    if hb_grade is not None and _to_float(hb_grade, "Hb 分级", default=0) >= 3:
        escalate(2, "重度贫血，需评估病因并转诊")

    if plt_grade is not None and _to_float(plt_grade, "PLT 分级", default=0) >= 3:
        escalate(2, "重度血小板减少，需评估出血风险")

    if viral_load_category in ("high", "moderate"):
        escalate(2, "病毒血症未受控，需评估治疗方案与耐药")
    elif viral_load_category == "low":
        escalate(1, "低水平病毒血症，复查并评估依从性")

    action = {0: "continue", 1: "monitor", 2: "refer", 3: "stop"}[severity]
    if not reasons:
        reasons.append("各项指标无异常，继续当前方案")
    return {"action": action, "reasons": reasons}


# ---- 趋势判断（连续多次） ----
def trend_direction(values, higher_is_worse=True, rel_tol=0.05):
    # 根据一连串数值判断趋势：恶化 / 改善 / 稳定。
    clean = []
    for x in (values or []):
        fx = _to_float(x, "趋势数值", default=None)
        if fx is not None:
            clean.append(fx)
    if len(clean) < 2:
        warnings.warn("趋势判断至少需要两个有效数值", UserWarning)
        return {"direction": "unknown", "change": None, "change_pct": None}

    arr = np.asarray(clean, dtype=float)
    first, last = arr[0], arr[-1]
    change = round(float(last - first), 4)
    denom = abs(first) if first != 0 else 1.0
    change_pct = round(float((last - first) / denom * 100.0), 2)

    if abs(last - first) <= rel_tol * denom:
        return {"direction": "stable", "change": change, "change_pct": change_pct}

    increasing = last > first
    if higher_is_worse:
        direction = "worsening" if increasing else "improving"
    else:
        direction = "improving" if increasing else "worsening"
    return {"direction": direction, "change": change, "change_pct": change_pct}
