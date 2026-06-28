"""智能干预中心：整合风险、检测、PrEP/PEP状态生成干预建议。"""

from dataclasses import dataclass
from datetime import datetime, timedelta

from screening import ScreeningInput, normalize_risk_level, recommend_hiv_testing


@dataclass(frozen=True)
class InterventionInput:
    risk_level: str
    hours_since_exposure: int | None = None
    test_result: str = "未检测"
    prep_status: str = "未使用"
    prep_adherence: str = "未知"
    pep_status: str = "未使用"
    has_symptoms: bool = False


def build_intervention_plan(data: InterventionInput | dict) -> dict:
    if isinstance(data, dict):
        data = InterventionInput(**data)

    risk = normalize_risk_level(data.risk_level)
    testing = recommend_hiv_testing(
        ScreeningInput(
            risk_level=data.risk_level,
            hours_since_exposure=data.hours_since_exposure,
            has_symptoms=data.has_symptoms,
            on_prep=data.prep_status != "未使用",
            on_pep=data.pep_status != "未使用",
        )
    )

    in_pep_window = data.hours_since_exposure is not None and data.hours_since_exposure <= 72
    if in_pep_window and risk in {"high", "very_high"} and data.pep_status == "未使用":
        pep_advice = "仍在72小时窗口内，建议立即前往PEP门诊、急诊、感染科或疾控机构评估PEP。"
    elif data.pep_status != "未使用":
        pep_advice = "按医嘱完成28天PEP疗程，并完成基线、疗程结束后及后续随访检测。"
    else:
        pep_advice = "如已超过72小时，PEP获益有限；仍建议检测并咨询专业人员。"

    if data.test_result in {"阳性提示", "初筛阳性"}:
        prep_advice = "暂缓PrEP，立即进行确证检测和感染科转诊。"
    elif risk in {"high", "very_high"}:
        prep_advice = "在确认HIV阴性、肾功能和乙肝等基线检查合适后，可咨询医生启动PrEP。"
    elif data.prep_status != "未使用":
        prep_advice = "继续按方案服药，保持定期HIV检测和肾功能随访。"
    else:
        prep_advice = "当前以安全行为、定期检测和风险变化后复评为主。"

    medication = "暂无用药提醒"
    if data.prep_status != "未使用":
        medication = "建议固定每日服药时间；漏服、呕吐或停药前后暴露请咨询医生。"
    if data.pep_status != "未使用":
        medication = "PEP需连续28天，尽量每天同一时间服用，不适反应及时咨询医生。"

    return {
        "risk_level": data.risk_level,
        "testing_advice": testing,
        "prep_advice": prep_advice,
        "pep_advice": pep_advice,
        "medication_reminder": medication,
        "pharmacy_guidance": "结合检测结果、肾功能、乙肝状态、合并用药和依从性进行个体化药学指导。",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
    }


def next_followup_dates(start: datetime | None = None) -> list[dict]:
    base = start or datetime.now()
    return [
        {"name": "基线检测", "date": base.date().isoformat()},
        {"name": "4周复查", "date": (base + timedelta(days=28)).date().isoformat()},
        {"name": "12周复查", "date": (base + timedelta(days=84)).date().isoformat()},
    ]
