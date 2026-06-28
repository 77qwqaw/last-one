"""检测筛查中心：HIV尿液/血液/核酸检测推荐规则。"""

from dataclasses import dataclass


@dataclass(frozen=True)
class ScreeningInput:
    risk_level: str
    hours_since_exposure: int | None = None
    has_symptoms: bool = False
    on_prep: bool = False
    on_pep: bool = False


def normalize_risk_level(risk_level: str) -> str:
    mapping = {
        "低": "low",
        "较低": "low",
        "中": "medium",
        "中等": "medium",
        "高": "high",
        "极高": "very_high",
        "low": "low",
        "medium": "medium",
        "high": "high",
        "very_high": "very_high",
    }
    return mapping.get(str(risk_level).strip(), "medium")


def recommend_hiv_testing(data: ScreeningInput | dict) -> dict:
    """根据风险等级、暴露时间、症状和PrEP/PEP状态推荐检测方式。"""
    if isinstance(data, dict):
        data = ScreeningInput(**data)

    risk = normalize_risk_level(data.risk_level)
    days = None if data.hours_since_exposure is None else max(data.hours_since_exposure / 24.0, 0)

    if risk in {"high", "very_high"} and days is not None and days <= 14:
        method = "HIV核酸检测"
        scenario = "高风险暴露、窗口期早期检测"
        timing = "建议尽快到医疗机构咨询核酸检测，并按医嘱在4-6周、12周复查抗原抗体。"
        window = "核酸检测可更早发现病毒核酸，但阴性结果仍需结合暴露时间和后续复查确认。"
    elif days is not None and days >= 21 and risk in {"low", "medium"}:
        method = "HIV尿液检测"
        scenario = "窗口期后筛查、低侵入性自检"
        timing = "建议窗口期后筛查；若结果异常或仍有担忧，应前往机构做血液检测确认。"
        window = "尿液检测适合作为窗口期后筛查，不能替代医疗机构确证检测。"
    else:
        method = "HIV血液检测"
        scenario = "常规检测、PrEP/PEP前后随访"
        timing = "建议到医院、疾控或社区检测点完成抗原抗体检测，并按风险情况复查。"
        window = "第四代抗原抗体检测通常比单纯抗体检测更早发现感染，具体窗口期以机构说明为准。"

    if data.on_pep:
        timing += " PEP使用者需完成基线、疗程结束后及后续随访检测。"
    if data.on_prep:
        timing += " PrEP使用者建议保持定期HIV检测，避免在感染未排除时继续单药预防。"
    if data.has_symptoms:
        timing += " 如出现急性感染样症状，请优先线下就医。"

    return {
        "risk_level": risk,
        "recommended_method": method,
        "scenario": scenario,
        "timing_advice": timing,
        "window_period_note": window,
    }
