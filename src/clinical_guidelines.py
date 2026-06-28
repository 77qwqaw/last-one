# HIV 预防临床指南规则引擎：PrEP/PEP 启动判定、方案推荐、随访时间表等。
# 非法输入按项目约定：返回带默认值的结构化结果并 warnings.warn（除非显式标注）。
import warnings

import numpy as np


# ---- 常量与阈值 ----
# 肾功能（eGFR，mL/min/1.73m^2）阈值
EGFR_TDF_MIN = 60.0          # TDF/FTC 启动最低 eGFR
EGFR_TAF_MIN = 30.0          # TAF/FTC 启动最低 eGFR
EGFR_CONTRAINDICATED = 30.0  # 低于此值禁用含 TDF 方案

# PEP 暴露时间窗（小时）
PEP_WINDOW_HOURS = 72.0

# HIV 检测窗口期（天），不同方法的可靠检出时间
HIV_WINDOW_DAYS = {
    "抗原抗体联合检测": 18,
    "抗体检测": 23,
    "核酸检测": 10,
}

# 暴露源风险等级 -> 单次暴露相对权重
EXPOSURE_SOURCE_RISK = {
    "已知HIV阳性未治疗": 1.0,
    "已知HIV阳性病毒抑制": 0.05,
    "HIV状态未知高风险人群": 0.5,
    "HIV状态未知低风险人群": 0.1,
    "已知HIV阴性": 0.0,
}

# 暴露途径相对风险（与传播概率模型方向一致）
EXPOSURE_ROUTE_RISK = {
    "receptive_anal": 1.0,
    "insertive_anal": 0.3,
    "vaginal": 0.25,
    "needle_sharing": 0.6,
    "oral": 0.02,
    "skin_intact": 0.0,
}

# PrEP 方案标识
REGIMEN_DAILY_TDF = "每日口服 TDF/FTC"
REGIMEN_DAILY_TAF = "每日口服 TAF/FTC"
REGIMEN_ON_DEMAND = "按需 2-1-1（事件驱动）"
REGIMEN_CAB_LA = "长效注射 CAB-LA"


# ---- 输入校验工具 ----
def validate_egfr(value, name="eGFR"):
    try:
        v = float(value)
    except (ValueError, TypeError):
        warnings.warn(f"{name} 输入非法，已重置为 90", UserWarning)
        return 90.0
    if v < 0 or v > 250:
        warnings.warn(f"{name} 超出合理范围 (0-250)，已重置为 90", UserWarning)
        return 90.0
    return v


def validate_hours_since_exposure(value, name="暴露后小时数"):
    try:
        v = float(value)
    except (ValueError, TypeError):
        warnings.warn(f"{name} 输入非法，已重置为 0", UserWarning)
        return 0.0
    if v < 0:
        warnings.warn(f"{name} 不能为负数，已重置为 0", UserWarning)
        return 0.0
    return v


def validate_bool(value, name="布尔标志", default=False):
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        s = value.strip().lower()
        if s in {"true", "yes", "y", "1", "是", "有"}:
            return True
        if s in {"false", "no", "n", "0", "否", "无"}:
            return False
    warnings.warn(f"{name} 输入非法，已重置为 {default}", UserWarning)
    return default


def validate_exposure_route(route, name="暴露途径"):
    # 校验暴露途径，非法返回最保守的 receptive_anal 并警告。
    if route in EXPOSURE_ROUTE_RISK:
        return route
    warnings.warn(f"{name} 非法：{route}，已重置为 receptive_anal", UserWarning)
    return "receptive_anal"


def validate_exposure_source(source, name="暴露源风险"):
    # 校验暴露源风险等级，非法返回未知高风险并警告。
    if source in EXPOSURE_SOURCE_RISK:
        return source
    warnings.warn(f"{name} 非法：{source}，已重置为 HIV状态未知高风险人群", UserWarning)
    return "HIV状态未知高风险人群"


# ---- 风险因素评估 ----
def assess_risk_factors(risk_factors):
    """
    汇总 PrEP 相关风险因素，返回 dict。

    risk_factors: dict，可能键：
        condomless_sex(bool), multiple_partners(bool),
        partner_hiv_positive(bool), partner_not_suppressed(bool),
        recent_sti(bool), injection_drug_use(bool),
        commercial_sex(bool), pep_repeat_use(bool)
    返回 {risk_score:int, high_risk:bool, matched:list, recommend_prep:bool}
    """
    if not isinstance(risk_factors, dict):
        warnings.warn("risk_factors 必须为 dict，已视为空", UserWarning)
        risk_factors = {}

    weights = {
        "condomless_sex": 2,
        "multiple_partners": 2,
        "partner_hiv_positive": 3,
        "partner_not_suppressed": 2,
        "recent_sti": 2,
        "injection_drug_use": 3,
        "commercial_sex": 2,
        "pep_repeat_use": 2,
    }
    score = 0
    matched = []
    for key, w in weights.items():
        if validate_bool(risk_factors.get(key, False), key):
            score += w
            matched.append(key)

    high_risk = score >= 3
    # 单独的强适应症：伴侣阳性未抑制 或 注射吸毒 即视为强烈推荐
    strong = (
        validate_bool(risk_factors.get("partner_not_suppressed", False), "partner_not_suppressed")
        or validate_bool(risk_factors.get("injection_drug_use", False), "injection_drug_use")
    )
    recommend = high_risk or strong
    return {
        "risk_score": score,
        "high_risk": high_risk,
        "strong_indication": strong,
        "matched": matched,
        "recommend_prep": recommend,
    }


# ---- PrEP 启动适应症判定 ----
def evaluate_prep_eligibility(
    hiv_negative_confirmed,
    egfr,
    hbv_status,
    risk_factors,
    acute_hiv_symptoms=False,
):
    """
    判定是否适合启动 PrEP，返回结构化 dict。

    参数：
        hiv_negative_confirmed: bool，是否已确认 HIV 阴性（启动前提）
        egfr: float，肾功能
        hbv_status: str，"阴性" / "慢性感染" / "未知"
        risk_factors: dict，见 assess_risk_factors
        acute_hiv_symptoms: bool，是否存在急性 HIV 感染症状

    返回 dict: eligible / blockers / warnings / risk / details
    """
    hiv_neg = validate_bool(hiv_negative_confirmed, "hiv_negative_confirmed")
    egfr_v = validate_egfr(egfr)
    acute = validate_bool(acute_hiv_symptoms, "acute_hiv_symptoms")
    risk = assess_risk_factors(risk_factors)

    if hbv_status not in {"阴性", "慢性感染", "未知"}:
        warnings.warn(f"hbv_status 非法：{hbv_status}，已重置为 未知", UserWarning)
        hbv_status = "未知"

    blockers = []
    advisories = []

    if not hiv_neg:
        blockers.append("启动前必须确认 HIV 阴性，否则可能诱导耐药")
    if acute:
        blockers.append("存在急性 HIV 感染症状，需先排除急性感染")
    if egfr_v < EGFR_TAF_MIN:
        blockers.append(f"eGFR {egfr_v:.0f} < {EGFR_TAF_MIN:.0f}，所有含替诺福韦方案禁用")

    if hbv_status == "慢性感染":
        advisories.append("合并慢性 HBV：停用 PrEP 可能致 HBV 反弹，需肝病科共管")
    if hbv_status == "未知":
        advisories.append("HBV 状态未知，建议启动前完成 HBsAg 检测")
    if not risk["recommend_prep"]:
        advisories.append("当前风险因素不足以构成强适应症，可与受检者共同决策")

    eligible = len(blockers) == 0 and risk["recommend_prep"]

    return {
        "eligible": eligible,
        "blockers": blockers,
        "advisories": advisories,
        "egfr": egfr_v,
        "hbv_status": hbv_status,
        "risk": risk,
        "decision": "建议启动 PrEP" if eligible else "暂不启动 / 需先处理阻断项",
    }


# ---- PrEP 方案选择 ----
def recommend_prep_regimen(
    egfr,
    sex_assigned_at_birth="male",
    exposure_route="receptive_anal",
    hbv_status="阴性",
    prefers_injectable=False,
    adherence_concern=False,
    pregnancy=False,
):
    # 在已判定适合 PrEP 的前提下，推荐具体方案，返回结构化 dict。
    egfr_v = validate_egfr(egfr)
    route = validate_exposure_route(exposure_route)
    injectable = validate_bool(prefers_injectable, "prefers_injectable")
    adherence = validate_bool(adherence_concern, "adherence_concern")
    preg = validate_bool(pregnancy, "pregnancy")

    if sex_assigned_at_birth not in {"male", "female"}:
        warnings.warn("sex_assigned_at_birth 非法，已重置为 male", UserWarning)
        sex_assigned_at_birth = "male"
    if hbv_status not in {"阴性", "慢性感染", "未知"}:
        warnings.warn("hbv_status 非法，已重置为 阴性", UserWarning)
        hbv_status = "阴性"

    candidates = []
    excluded = []
    rationale = []

    # 含替诺福韦方案的肾功能门槛
    if egfr_v >= EGFR_TDF_MIN:
        candidates.append(REGIMEN_DAILY_TDF)
    else:
        excluded.append((REGIMEN_DAILY_TDF, f"eGFR {egfr_v:.0f} < {EGFR_TDF_MIN:.0f}"))

    if egfr_v >= EGFR_TAF_MIN:
        candidates.append(REGIMEN_DAILY_TAF)
    else:
        excluded.append((REGIMEN_DAILY_TAF, f"eGFR {egfr_v:.0f} < {EGFR_TAF_MIN:.0f}"))

    # 按需 2-1-1 仅推荐用于 MSM 经肛交暴露，且不依从顾虑不应作为首选；女性阴道暴露不适用
    on_demand_ok = (
        sex_assigned_at_birth == "male"
        and route in {"receptive_anal", "insertive_anal"}
        and egfr_v >= EGFR_TDF_MIN
        and not preg
    )
    if on_demand_ok:
        candidates.append(REGIMEN_ON_DEMAND)
    else:
        excluded.append((REGIMEN_ON_DEMAND, "仅适用于 MSM 肛交暴露且 eGFR≥60、非孕期"))

    # 长效注射不依赖肾功能门槛，是依从困难者的优选
    candidates.append(REGIMEN_CAB_LA)

    # 选首选
    primary = None
    if injectable or adherence:
        primary = REGIMEN_CAB_LA
        rationale.append("依从性顾虑或偏好注射，优先长效 CAB-LA")
    elif egfr_v < EGFR_TDF_MIN and egfr_v >= EGFR_TAF_MIN:
        primary = REGIMEN_DAILY_TAF
        rationale.append("eGFR 介于 30-60，TAF 肾脏安全性更优")
    elif hbv_status == "慢性感染":
        primary = REGIMEN_DAILY_TDF
        rationale.append("合并慢性 HBV，含 TDF 方案兼顾 HBV 抑制")
    else:
        primary = REGIMEN_DAILY_TDF
        rationale.append("无特殊因素，每日 TDF/FTC 为标准首选")

    alternatives = [c for c in candidates if c != primary]

    return {
        "primary": primary,
        "alternatives": alternatives,
        "candidates": candidates,
        "excluded": excluded,
        "rationale": rationale,
    }


# ---- PEP 启动判定 ----
def compute_pep_exposure_risk(exposure_route, exposure_source):
    # 计算暴露的相对风险权重 = 途径权重 * 源权重，返回 0-1。
    route = validate_exposure_route(exposure_route)
    source = validate_exposure_source(exposure_source)
    return EXPOSURE_ROUTE_RISK[route] * EXPOSURE_SOURCE_RISK[source]


def evaluate_pep_eligibility(
    hours_since_exposure,
    exposure_route,
    exposure_source,
    source_unknown_high_prevalence=False,
):
    """
    判定是否启动 PEP，返回结构化 dict。

    规则：
    - >72h 超窗，原则上不再启动；
    - 暴露源已知阴性 或 风险权重为 0（如完整皮肤），不推荐；
    - 风险权重 >0 且在 72h 内：推荐尽早启动；
    - 越早越好（用 time_factor 反映紧迫度）。
    """
    hours = validate_hours_since_exposure(hours_since_exposure)
    route = validate_exposure_route(exposure_route)
    source = validate_exposure_source(exposure_source)
    risk_weight = compute_pep_exposure_risk(route, source)

    in_window = hours <= PEP_WINDOW_HOURS
    reasons = []
    recommend = True

    if not in_window:
        recommend = False
        reasons.append(f"暴露已超过 {PEP_WINDOW_HOURS:.0f}h（实际 {hours:.0f}h），超出有效窗口")
    if risk_weight <= 0.0 and not validate_bool(
        source_unknown_high_prevalence, "source_unknown_high_prevalence"
    ):
        recommend = False
        reasons.append("暴露源风险或途径风险为 0，无 HIV 暴露可能，不推荐 PEP")

    # 紧迫度评分：越早分数越高（0-100）
    if in_window:
        time_factor = max(0.0, (PEP_WINDOW_HOURS - hours) / PEP_WINDOW_HOURS)
    else:
        time_factor = 0.0
    urgency = int(round(100 * time_factor * (0.5 + 0.5 * min(risk_weight, 1.0))))
    urgency = max(0, min(100, urgency))

    if recommend:
        decision = "建议立即启动 PEP"
    else:
        decision = "不推荐 PEP"

    return {
        "recommend": recommend,
        "in_window": in_window,
        "hours_since_exposure": hours,
        "exposure_route": route,
        "exposure_source": source,
        "risk_weight": float(risk_weight),
        "urgency_score": urgency,
        "reasons": reasons,
        "decision": decision,
    }


def recommend_pep_regimen(egfr, age_years=30, pregnancy=False):
    # 推荐 28 天 PEP 三联方案，返回结构化 dict。
    egfr_v = validate_egfr(egfr)
    preg = validate_bool(pregnancy, "pregnancy")
    try:
        age = float(age_years)
    except (ValueError, TypeError):
        warnings.warn("age_years 非法，已重置为 30", UserWarning)
        age = 30.0

    notes = []
    if egfr_v >= EGFR_TDF_MIN:
        backbone = "TDF/FTC"
    elif egfr_v >= EGFR_TAF_MIN:
        backbone = "TAF/FTC"
        notes.append("eGFR 30-60，backbone 选用 TAF")
    else:
        backbone = "AZT/3TC（避免替诺福韦）"
        notes.append(f"eGFR {egfr_v:.0f} < {EGFR_TAF_MIN:.0f}，避免替诺福韦")

    third_agent = "DTG"
    if preg:
        third_agent = "RAL"
        notes.append("孕期优先 RAL，需结合最新妊娠用药证据")
    if age < 18:
        notes.append("未成年人需按体重调整剂量并由专科评估")

    return {
        "backbone": backbone,
        "third_agent": third_agent,
        "regimen": f"{backbone} + {third_agent}",
        "duration_days": 28,
        "notes": notes,
    }


# ---- 随访时间表 / 检测窗口期 ----
def generate_followup_schedule(start_day=0, mode="prep", months=12):
    # 生成随访时间表 list[dict]。
    if mode not in {"prep", "pep"}:
        warnings.warn(f"mode 非法：{mode}，已重置为 prep", UserWarning)
        mode = "prep"
    try:
        base = int(start_day)
    except (ValueError, TypeError):
        warnings.warn("start_day 非法，已重置为 0", UserWarning)
        base = 0

    schedule = []
    if mode == "prep":
        try:
            m = int(months)
        except (ValueError, TypeError):
            m = 12
        m = max(1, m)
        schedule.append({"day": base, "label": "基线", "tests": ["HIV", "肾功能", "HBV/HCV", "STI"]})
        if m >= 1:
            schedule.append({"day": base + 30, "label": "第1个月", "tests": ["HIV", "依从性评估"]})
        # 之后每 3 个月一次直到 months
        month_mark = 3
        while month_mark <= m:
            schedule.append({
                "day": base + month_mark * 30,
                "label": f"第{month_mark}个月",
                "tests": ["HIV", "肾功能", "STI", "依从性评估"],
            })
            month_mark += 3
    else:  # pep
        schedule.append({"day": base, "label": "基线", "tests": ["HIV", "肾功能", "HBV", "STI", "妊娠检测"]})
        schedule.append({"day": base + 14, "label": "第2周", "tests": ["不良反应评估", "依从性评估"]})
        schedule.append({"day": base + 28, "label": "疗程结束(第28天)", "tests": ["肾功能", "依从性评估"]})
        schedule.append({"day": base + 42, "label": "第6周", "tests": ["HIV"]})
        schedule.append({"day": base + 84, "label": "第12周", "tests": ["HIV"]})
    return schedule


def hiv_window_status(days_since_exposure, method="抗原抗体联合检测"):
    """
    判定某检测方法在暴露后 N 天是否已过窗口期，返回 dict。
    """
    try:
        d = float(days_since_exposure)
        if d < 0:
            warnings.warn("days_since_exposure 不能为负，已重置为 0", UserWarning)
            d = 0.0
    except (ValueError, TypeError):
        warnings.warn("days_since_exposure 非法，已重置为 0", UserWarning)
        d = 0.0

    if method not in HIV_WINDOW_DAYS:
        warnings.warn(f"method 非法：{method}，已重置为 抗原抗体联合检测", UserWarning)
        method = "抗原抗体联合检测"

    window = HIV_WINDOW_DAYS[method]
    passed = d >= window
    return {
        "method": method,
        "window_days": window,
        "days_since_exposure": d,
        "window_passed": passed,
        "reliable": passed,
        "advice": "结果可靠" if passed else f"未过窗口期，需在第 {window} 天后复测",
    }


# ---- 禁忌症 / 转诊 ----
def check_contraindications(regimen, egfr, hbv_status="阴性", known_allergy=False):
    """
    检查给定方案的禁忌症，返回 dict: contraindicated(bool)/issues(list)。
    """
    egfr_v = validate_egfr(egfr)
    allergy = validate_bool(known_allergy, "known_allergy")
    issues = []

    contains_tdf = "TDF" in str(regimen)
    contains_taf = "TAF" in str(regimen)

    if (contains_tdf or contains_taf) and egfr_v < EGFR_TAF_MIN:
        issues.append(f"eGFR {egfr_v:.0f} < {EGFR_TAF_MIN:.0f}，禁用替诺福韦类")
    elif contains_tdf and egfr_v < EGFR_TDF_MIN:
        issues.append(f"eGFR {egfr_v:.0f} < {EGFR_TDF_MIN:.0f}，TDF 不推荐，宜改 TAF")

    if allergy:
        issues.append("既往药物过敏史，需核对成分后再用")

    return {
        "regimen": regimen,
        "contraindicated": len(issues) > 0,
        "issues": issues,
    }


def referral_rules(eligibility_result, special_population=None):
    # 基于适应症结果与特殊人群标记，给出转诊建议 list[str]。
    referrals = []
    if not isinstance(eligibility_result, dict):
        warnings.warn("eligibility_result 必须为 dict", UserWarning)
        eligibility_result = {}

    blockers = eligibility_result.get("blockers", [])
    for b in blockers:
        if "急性 HIV" in b:
            referrals.append("感染科：急性 HIV 排查")
        if "替诺福韦" in b or "eGFR" in b:
            referrals.append("肾内科：肾功能评估")

    pop = set(special_population or [])
    if "pregnant" in pop:
        referrals.append("产科 / MTCT 母婴阻断门诊")
    if "adolescent" in pop:
        referrals.append("青少年友善门诊")
    if "hbv_chronic" in pop or eligibility_result.get("hbv_status") == "慢性感染":
        referrals.append("肝病科：HBV 共管")
    if "renal_impairment" in pop:
        referrals.append("肾内科：肾功能评估")
    if "acute_hiv_suspect" in pop:
        referrals.append("感染科：急性 HIV 排查")

    # 去重并保持顺序
    seen = set()
    unique = []
    for r in referrals:
        if r not in seen:
            seen.add(r)
            unique.append(r)
    return unique


# ---- 决策封装（顶层入口） ----
def build_prep_decision(
    hiv_negative_confirmed,
    egfr,
    hbv_status,
    risk_factors,
    sex_assigned_at_birth="male",
    exposure_route="receptive_anal",
    prefers_injectable=False,
    adherence_concern=False,
    pregnancy=False,
    acute_hiv_symptoms=False,
):
    """
    PrEP 端到端决策封装，组合适应症 + 方案 + 随访 + 禁忌 + 转诊。
    返回结构化 dict，供报告层直接消费。
    """
    eligibility = evaluate_prep_eligibility(
        hiv_negative_confirmed, egfr, hbv_status, risk_factors, acute_hiv_symptoms
    )
    result = {
        "type": "PrEP",
        "eligibility": eligibility,
    }
    if not eligibility["eligible"]:
        result["regimen"] = None
        result["followup"] = []
        result["referrals"] = referral_rules(
            eligibility,
            special_population=(["pregnant"] if validate_bool(pregnancy, "pregnancy") else None),
        )
        return result

    regimen = recommend_prep_regimen(
        egfr=eligibility["egfr"],
        sex_assigned_at_birth=sex_assigned_at_birth,
        exposure_route=exposure_route,
        hbv_status=eligibility["hbv_status"],
        prefers_injectable=prefers_injectable,
        adherence_concern=adherence_concern,
        pregnancy=pregnancy,
    )
    contraindication = check_contraindications(
        regimen["primary"], eligibility["egfr"], eligibility["hbv_status"]
    )
    followup = generate_followup_schedule(mode="prep", months=12)
    special = []
    if validate_bool(pregnancy, "pregnancy"):
        special.append("pregnant")
    if eligibility["hbv_status"] == "慢性感染":
        special.append("hbv_chronic")
    referrals = referral_rules(eligibility, special_population=special)

    result["regimen"] = regimen
    result["contraindication"] = contraindication
    result["followup"] = followup
    result["referrals"] = referrals
    return result


def build_pep_decision(
    hours_since_exposure,
    exposure_route,
    exposure_source,
    egfr,
    age_years=30,
    pregnancy=False,
):
    """
    PEP 端到端决策封装，组合启动判定 + 方案 + 随访。
    返回结构化 dict。
    """
    eligibility = evaluate_pep_eligibility(
        hours_since_exposure, exposure_route, exposure_source
    )
    result = {
        "type": "PEP",
        "eligibility": eligibility,
    }
    if not eligibility["recommend"]:
        result["regimen"] = None
        result["followup"] = []
        return result

    regimen = recommend_pep_regimen(egfr, age_years=age_years, pregnancy=pregnancy)
    followup = generate_followup_schedule(mode="pep")
    result["regimen"] = regimen
    result["followup"] = followup
    return result
