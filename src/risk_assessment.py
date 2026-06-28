# 暴露风险评估：单次/累积风险、问卷打分、HIRI-MSM、PrEP 适应症、PEP 紧急度
import math
import warnings

import numpy as np


# 单次暴露基线（每次行为的传播概率，数据量级参考公开流行病学估计）
PER_ACT_BASE_RISK = {
    "receptive_anal": 0.0138,
    "insertive_anal": 0.0011,
    "receptive_vaginal": 0.0008,
    "insertive_vaginal": 0.0004,
    "oral": 0.0001,
    "needle_sharing": 0.0063,
}

CONDOM_REDUCTION = 0.20              # 安全套后保留的相对风险（≈降 80%）
PARTNER_SUPPRESSED_REDUCTION = 0.04  # U=U 后保留的相对风险
STI_MULTIPLIER = 2.5
PREP_ADHERENT_REDUCTION = 0.10

_TRUE_WORDS = {"是", "true", "yes", "y", "1"}
_FALSE_WORDS = {"否", "false", "no", "n", "0", ""}


# ---------- 校验工具 ----------

def validate_exposure_type(exposure_type):
    if exposure_type in PER_ACT_BASE_RISK:
        return exposure_type
    warnings.warn(
        f"暴露类型非法：{exposure_type}，已回退为 receptive_anal", UserWarning
    )
    return "receptive_anal"


def validate_count(value, default=0, name="计数", max_value=None):
    try:
        v = int(round(float(value)))
    except (ValueError, TypeError):
        warnings.warn(f"{name} 必须为整数，使用默认值 {default}", UserWarning)
        return default
    if v < 0:
        warnings.warn(f"{name} 不能为负，使用默认值 {default}", UserWarning)
        return default
    if max_value is not None and v > max_value:
        warnings.warn(f"{name} 超过上限 {max_value}，已裁剪", UserWarning)
        return max_value
    return v


def validate_bool(value, default=False, name="布尔项"):
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        s = value.strip().lower()
        if s in _TRUE_WORDS:
            return True
        if s in _FALSE_WORDS:
            return False
    warnings.warn(f"{name} 非法，使用默认值 {default}", UserWarning)
    return default


def validate_probability(value, default=0.0, name="概率"):
    try:
        v = float(value)
    except (ValueError, TypeError):
        warnings.warn(f"{name} 必须为数字，使用默认值 {default}", UserWarning)
        return default
    if math.isnan(v):
        warnings.warn(f"{name} 为 NaN，使用默认值 {default}", UserWarning)
        return default
    if v < 0:
        warnings.warn(f"{name} 小于 0，已裁剪为 0", UserWarning)
        return 0.0
    if v > 1:
        warnings.warn(f"{name} 大于 1，已裁剪为 1", UserWarning)
        return 1.0
    return v


# ---------- 单次 / 累积风险 ----------

def per_act_risk(exposure_type, condom_use=False, partner_suppressed=False,
                 sti_present=False, self_on_prep=False):
    et = validate_exposure_type(exposure_type)
    risk = PER_ACT_BASE_RISK[et]
    if validate_bool(condom_use, default=False, name="安全套使用"):
        risk *= CONDOM_REDUCTION
    if validate_bool(partner_suppressed, default=False, name="伴侣病毒抑制"):
        risk *= PARTNER_SUPPRESSED_REDUCTION
    if validate_bool(sti_present, default=False, name="合并STI"):
        risk *= STI_MULTIPLIER
    if validate_bool(self_on_prep, default=False, name="自身PrEP"):
        risk *= PREP_ADHERENT_REDUCTION
    return float(np.clip(risk, 0.0, 1.0))


def cumulative_risk(per_act_probs):
    """1 - ∏(1 - p_i)，空序列返回 0。"""
    try:
        arr = np.asarray(list(per_act_probs), dtype=float)
    except (TypeError, ValueError):
        warnings.warn("暴露概率序列无法解析，返回 0", UserWarning)
        return 0.0
    if arr.size == 0:
        return 0.0
    arr = np.clip(arr, 0.0, 1.0)
    return float(np.clip(1.0 - np.prod(1.0 - arr), 0.0, 1.0))


def cumulative_risk_repeated(single_prob, n_exposures):
    p = validate_probability(single_prob, default=0.0, name="单次概率")
    n = validate_count(n_exposures, default=0, name="暴露次数")
    if n == 0:
        return 0.0
    return float(np.clip(1.0 - (1.0 - p) ** n, 0.0, 1.0))


def time_window_risk(exposure_type, n_exposures, condom_use=False,
                     partner_suppressed=False, sti_present=False,
                     self_on_prep=False):
    p = per_act_risk(
        exposure_type,
        condom_use=condom_use,
        partner_suppressed=partner_suppressed,
        sti_present=sti_present,
        self_on_prep=self_on_prep,
    )
    return cumulative_risk_repeated(p, n_exposures)


# ---------- 问卷各维度子评分 ----------
# 各维度上限总和 = 100
QUESTIONNAIRE_WEIGHTS = {
    "exposure_type": 25,
    "partner_count": 15,
    "condom_use": 15,
    "partner_status": 20,
    "drug_injection": 10,
    "sti_history": 8,
    "prep_history": 7,
}

_PARTNER_STATUS_RISK = {
    "hiv_negative": 0.0,
    "hiv_positive_suppressed": 0.15,
    "unknown": 0.6,
    "hiv_positive_unsuppressed": 1.0,
}


def _score_exposure_type(exposure_type):
    et = validate_exposure_type(exposure_type)
    rel = PER_ACT_BASE_RISK[et] / PER_ACT_BASE_RISK["receptive_anal"]
    return QUESTIONNAIRE_WEIGHTS["exposure_type"] * float(np.clip(rel, 0.0, 1.0))


def _score_partner_count(n_partners):
    n = validate_count(n_partners, default=0, name="伴侣数")
    # 饱和：>=10 接近满分
    return QUESTIONNAIRE_WEIGHTS["partner_count"] * (n / (n + 5.0))


def _score_condom_use(condom_frequency):
    # condom_frequency: 1=总是，0=从不；用得少分高
    f = validate_probability(condom_frequency, default=0.0, name="安全套频率")
    return QUESTIONNAIRE_WEIGHTS["condom_use"] * (1.0 - f)


def _score_partner_status(partner_status):
    if partner_status not in _PARTNER_STATUS_RISK:
        warnings.warn(
            f"伴侣状态非法：{partner_status}，按 unknown 处理", UserWarning
        )
        partner_status = "unknown"
    return QUESTIONNAIRE_WEIGHTS["partner_status"] * _PARTNER_STATUS_RISK[partner_status]


def _score_drug_injection(inject_drugs, share_needles):
    if not validate_bool(inject_drugs, default=False, name="注射吸毒"):
        return 0.0
    if validate_bool(share_needles, default=False, name="共用针具"):
        return float(QUESTIONNAIRE_WEIGHTS["drug_injection"])
    return QUESTIONNAIRE_WEIGHTS["drug_injection"] * 0.4


def _score_sti_history(recent_sti):
    if validate_bool(recent_sti, default=False, name="既往STI"):
        return float(QUESTIONNAIRE_WEIGHTS["sti_history"])
    return 0.0


def _score_prep_history(on_prep, prep_adherent):
    on = validate_bool(on_prep, default=False, name="使用PrEP")
    if not on:
        # 高危但未用 PrEP -> 满分提示适应症
        return float(QUESTIONNAIRE_WEIGHTS["prep_history"])
    if validate_bool(prep_adherent, default=False, name="PrEP规律"):
        return 0.0
    return QUESTIONNAIRE_WEIGHTS["prep_history"] * 0.5


def _collect_scores(answers):
    return {
        "exposure_type": _score_exposure_type(answers.get("exposure_type", "oral")),
        "partner_count": _score_partner_count(answers.get("partner_count", 0)),
        "condom_use": _score_condom_use(answers.get("condom_frequency", 1.0)),
        "partner_status": _score_partner_status(
            answers.get("partner_status", "hiv_negative")
        ),
        "drug_injection": _score_drug_injection(
            answers.get("inject_drugs", False),
            answers.get("share_needles", False),
        ),
        "sti_history": _score_sti_history(answers.get("recent_sti", False)),
        "prep_history": _score_prep_history(
            answers.get("on_prep", False),
            answers.get("prep_adherent", False),
        ),
    }


def questionnaire_score(answers):
    if not isinstance(answers, dict):
        warnings.warn("问卷答案非 dict，按空问卷处理", UserWarning)
        answers = {}
    total = float(sum(_collect_scores(answers).values()))
    return float(np.clip(total, 0.0, 100.0))


def risk_factor_attribution(answers):
    if not isinstance(answers, dict):
        warnings.warn("问卷答案非 dict，按空问卷处理", UserWarning)
        answers = {}
    parts = _collect_scores(answers)
    total = float(sum(parts.values()))
    out = {
        k: {
            "score": float(v),
            "percent": float(v / total * 100.0) if total > 0 else 0.0,
        }
        for k, v in parts.items()
    }
    out["total"] = total
    return out


# ---------- HIRI-MSM ----------

def hiri_msm_score(age, n_male_partners_6m, n_receptive_anal_no_condom_6m,
                   n_insertive_anal_6m, partner_hiv_positive, stimulant_use,
                   poppers_use):
    """HIV Incidence Risk Index for MSM。>=10 通常提示评估 PrEP。"""
    age_v = validate_count(age, default=30, name="年龄")
    partners = validate_count(n_male_partners_6m, default=0, name="男性伴侣数")
    recep = validate_count(n_receptive_anal_no_condom_6m, default=0,
                           name="无套受方肛交伴侣数")
    insert = validate_count(n_insertive_anal_6m, default=0, name="插入方肛交")
    pos_partner = validate_bool(partner_hiv_positive, default=False, name="阳性伴侣")
    stim = validate_bool(stimulant_use, default=False, name="兴奋剂使用")
    pop = validate_bool(poppers_use, default=False, name="poppers使用")

    score = 0
    # 年龄：年轻得分更高
    if age_v <= 28:
        score += 8
    elif age_v <= 40:
        score += 5

    if partners > 10:
        score += 7
    elif partners >= 6:
        score += 4

    if recep >= 1:
        score += 10
    if insert >= 5:
        score += 6
    if pos_partner:
        score += 4
    if stim:
        score += 5
    if pop:
        score += 3
    return int(score)


def hiri_msm_interpretation(score):
    s = validate_count(score, default=0, name="HIRI评分")
    if s >= 10:
        return "高风险", "建议尽快咨询并评估 PrEP 适应症"
    if s >= 5:
        return "中等风险", "建议定期检测并关注高危行为"
    return "较低风险", "保持安全行为与定期检测"


# ---------- 风险分级 & PrEP 适应症 ----------

def risk_level_from_score(score):
    s = float(np.clip(
        validate_probability(score / 100.0, default=0.0, name="风险分") * 100.0,
        0.0, 100.0,
    ))
    if s >= 75:
        return "极高", "强烈建议立即咨询并启动 PrEP / 评估 PEP"
    if s >= 50:
        return "高", "建议尽快评估 PrEP 适应症并加强检测"
    if s >= 25:
        return "中", "建议加强安全措施并定期检测"
    return "低", "维持安全行为与常规检测"


def prep_indication(answers):
    if not isinstance(answers, dict):
        warnings.warn("问卷答案非 dict，按空问卷处理", UserWarning)
        answers = {}

    reasons = []
    if questionnaire_score(answers) >= 50:
        reasons.append("综合风险评分较高")

    et = answers.get("exposure_type", "oral")
    partner_status = answers.get("partner_status", "hiv_negative")
    condom_freq = validate_probability(
        answers.get("condom_frequency", 1.0), default=1.0, name="安全套频率"
    )
    if (et in ("receptive_anal", "insertive_anal")
            and condom_freq < 0.5
            and partner_status != "hiv_negative"):
        reasons.append("高风险性行为且安全套使用不足、伴侣状态非阴性")

    if validate_bool(answers.get("share_needles", False),
                     default=False, name="共用针具"):
        reasons.append("存在共用针具行为")

    n_partners = validate_count(answers.get("partner_count", 0),
                                default=0, name="伴侣数")
    if (validate_bool(answers.get("recent_sti", False),
                      default=False, name="近期STI") and n_partners >= 2):
        reasons.append("近期 STI 合并多性伴")

    if reasons:
        return True, "；".join(reasons)
    return False, "暂未达到 PrEP 推荐阈值，建议保持安全行为与定期检测"


# ---------- PEP 紧急度 ----------

def pep_urgency_score(hours_since_exposure, exposure_type, source_hiv_status,
                      condom_failure=False):
    hours = validate_count(hours_since_exposure, default=0,
                           name="暴露后小时数", max_value=100000)
    et = validate_exposure_type(exposure_type)

    status_map = {"positive": 1.0, "unknown": 0.5, "negative": 0.05}
    if source_hiv_status not in status_map:
        warnings.warn(
            f"暴露源状态非法：{source_hiv_status}，按 unknown 处理", UserWarning
        )
        source_hiv_status = "unknown"
    status_factor = status_map[source_hiv_status]

    # <=24h 最佳，72h 临界，>72h 急剧下降
    if hours <= 24:
        time_factor = 1.0
    elif hours <= 48:
        time_factor = 0.85
    elif hours <= 72:
        time_factor = 0.6
    else:
        time_factor = 0.1

    et_factor = float(np.clip(
        PER_ACT_BASE_RISK[et] / PER_ACT_BASE_RISK["receptive_anal"], 0.0, 1.0
    ))
    cf_factor = 1.15 if validate_bool(condom_failure, default=False,
                                      name="安全套失败") else 1.0

    raw = 100.0 * status_factor * time_factor * (0.4 + 0.6 * et_factor) * cf_factor
    return float(np.clip(raw, 0.0, 100.0))


def pep_recommendation(urgency_score, hours_since_exposure):
    s = validate_probability(urgency_score / 100.0, default=0.0,
                             name="紧急度") * 100.0
    hours = validate_count(hours_since_exposure, default=0,
                           name="暴露后小时数", max_value=100000)
    if hours > 72:
        return "已超过 72 小时窗口，PEP 效果有限，建议尽快检测并咨询医生"
    if s >= 60:
        return "高度紧急：请在数小时内前往医疗机构启动 PEP"
    if s >= 30:
        return "建议尽快（72 小时内）就医评估 PEP"
    return "风险相对较低，仍建议咨询专业人员并安排检测"


def full_assessment(answers):
    score = questionnaire_score(answers)
    level, advice = risk_level_from_score(score)
    indicated, reason = prep_indication(answers)
    return {
        "score": float(score),
        "risk_level": level,
        "advice": advice,
        "prep_indicated": bool(indicated),
        "prep_reason": reason,
        "attribution": risk_factor_attribution(answers),
    }
