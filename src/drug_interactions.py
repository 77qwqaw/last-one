# 药物相互作用：知识库 + 成对/方案查询、肾毒性叠加、严重度汇总、监测建议。
# 非法输入按项目约定：返回安全默认值并 warnings.warn。
import warnings

import numpy as np


# 数字越大越严重；用于排序与汇总
SEVERITY_RANK = {
    "contraindicated": 4,
    "major": 3,
    "moderate": 2,
    "minor": 1,
    "none": 0,
}

SEVERITY_LABEL_ZH = {
    "contraindicated": "禁忌合用",
    "major": "重度相互作用",
    "moderate": "中度相互作用",
    "minor": "轻度相互作用",
    "none": "无已知相互作用",
}


# --- 药物名规范化 ---
# 键统一小写比对，值是标准通用名
_DRUG_ALIASES = {
    # TDF
    "tdf": "tenofovir_df",
    "tenofovir df": "tenofovir_df",
    "tenofovir disoproxil": "tenofovir_df",
    "tenofovir disoproxil fumarate": "tenofovir_df",
    "viread": "tenofovir_df",
    "替诺福韦": "tenofovir_df",
    "替诺福韦二吡呋酯": "tenofovir_df",
    # TAF
    "taf": "tenofovir_af",
    "tenofovir af": "tenofovir_af",
    "tenofovir alafenamide": "tenofovir_af",
    "vemlidy": "tenofovir_af",
    "替诺福韦艾拉酚胺": "tenofovir_af",
    # FTC
    "ftc": "emtricitabine",
    "emtricitabine": "emtricitabine",
    "emtriva": "emtricitabine",
    "恩曲他滨": "emtricitabine",
    # DTG
    "dtg": "dolutegravir",
    "dolutegravir": "dolutegravir",
    "tivicay": "dolutegravir",
    "多替拉韦": "dolutegravir",
    # CAB（长效注射 PrEP）
    "cab": "cabotegravir",
    "cabotegravir": "cabotegravir",
    "cab-la": "cabotegravir",
    "apretude": "cabotegravir",
    "卡博特韦": "cabotegravir",
    # 增强剂
    "ritonavir": "ritonavir",
    "rtv": "ritonavir",
    "利托那韦": "ritonavir",
    "cobicistat": "cobicistat",
    "cobi": "cobicistat",
    # 相互作用对象
    "rifampin": "rifampicin",
    "rifampicin": "rifampicin",
    "利福平": "rifampicin",
    "nsaid": "nsaids",
    "nsaids": "nsaids",
    "ibuprofen": "nsaids",
    "naproxen": "nsaids",
    "diclofenac": "nsaids",
    "非甾体抗炎药": "nsaids",
    "布洛芬": "nsaids",
    "gentamicin": "aminoglycosides",
    "amikacin": "aminoglycosides",
    "aminoglycoside": "aminoglycosides",
    "aminoglycosides": "aminoglycosides",
    "氨基糖苷类": "aminoglycosides",
    "庆大霉素": "aminoglycosides",
    "antacid": "polyvalent_cations",
    "antacids": "polyvalent_cations",
    "calcium": "polyvalent_cations",
    "magnesium": "polyvalent_cations",
    "iron": "polyvalent_cations",
    "iron supplement": "polyvalent_cations",
    "multivitamin": "polyvalent_cations",
    "polyvalent cation": "polyvalent_cations",
    "polyvalent cations": "polyvalent_cations",
    "含二价阳离子制剂": "polyvalent_cations",
    "钙剂": "polyvalent_cations",
    "铁剂": "polyvalent_cations",
    "carbamazepine": "carbamazepine",
    "phenytoin": "phenytoin",
    "oxcarbazepine": "carbamazepine",
    "卡马西平": "carbamazepine",
    "苯妥英": "phenytoin",
    "metformin": "metformin",
    "二甲双胍": "metformin",
    "dofetilide": "dofetilide",
    "多非利特": "dofetilide",
    "st johns wort": "st_johns_wort",
    "st john's wort": "st_johns_wort",
    "贯叶连翘": "st_johns_wort",
    "圣约翰草": "st_johns_wort",
    "acyclovir": "acyclovir",
    "valacyclovir": "acyclovir",
    "阿昔洛韦": "acyclovir",
    "cisplatin": "cisplatin",
    "顺铂": "cisplatin",
    "vancomycin": "vancomycin",
    "万古霉素": "vancomycin",
    "ledipasvir": "ledipasvir",
    "雷迪帕韦": "ledipasvir",
}

DRUG_DISPLAY = {
    "tenofovir_df": "替诺福韦二吡呋酯 (TDF)",
    "tenofovir_af": "替诺福韦艾拉酚胺 (TAF)",
    "emtricitabine": "恩曲他滨 (FTC)",
    "dolutegravir": "多替拉韦 (DTG)",
    "cabotegravir": "卡博特韦 (CAB)",
    "ritonavir": "利托那韦",
    "cobicistat": "考比司他",
    "rifampicin": "利福平",
    "nsaids": "非甾体抗炎药 (NSAIDs)",
    "aminoglycosides": "氨基糖苷类抗生素",
    "polyvalent_cations": "含二价阳离子制剂",
    "carbamazepine": "卡马西平",
    "phenytoin": "苯妥英",
    "metformin": "二甲双胍",
    "dofetilide": "多非利特",
    "st_johns_wort": "贯叶连翘 (St John's Wort)",
    "acyclovir": "阿昔洛韦",
    "cisplatin": "顺铂",
    "vancomycin": "万古霉素",
    "ledipasvir": "雷迪帕韦",
}


def normalize_drug(name):
    if name is None:
        warnings.warn("药物名称为空，已忽略", UserWarning)
        return ""
    key = str(name).strip().lower()
    if not key:
        warnings.warn("药物名称为空，已忽略", UserWarning)
        return ""

    if key in _DRUG_ALIASES:
        return _DRUG_ALIASES[key]
    # 容忍多空格输入
    collapsed = " ".join(key.split())
    if collapsed in _DRUG_ALIASES:
        return _DRUG_ALIASES[collapsed]

    warnings.warn(f"未识别的药物名称：{name}，按原样处理", UserWarning)
    return collapsed


def drug_display_name(canonical):
    return DRUG_DISPLAY.get(canonical, canonical)


# --- 知识库（以 frozenset 为键，无序对） ---

def _pair_key(a, b):
    return frozenset((a, b))


_INTERACTIONS = {
    # TDF —— 肾毒性叠加 ----------------------------------------
    _pair_key("tenofovir_df", "nsaids"): {
        "severity": "moderate",
        "mechanism": "NSAIDs 与 TDF 均可损伤近端肾小管，肾毒性叠加",
        "management": "尽量避免长期合用，监测血肌酐与 eGFR，优先选择对乙酰氨基酚",
        "nephro": True,
    },
    _pair_key("tenofovir_df", "aminoglycosides"): {
        "severity": "major",
        "mechanism": "氨基糖苷类直接肾小管毒性，与 TDF 叠加显著增加急性肾损伤风险",
        "management": "避免合用；必须使用时密切监测肾功能并考虑改用 TAF",
        "nephro": True,
    },
    _pair_key("tenofovir_df", "cisplatin"): {
        "severity": "major",
        "mechanism": "顺铂具明确肾毒性，与 TDF 叠加增加肾小管损伤",
        "management": "化疗期间优先改用 TAF 或非替诺福韦方案，密切监测肾功能",
        "nephro": True,
    },
    _pair_key("tenofovir_df", "vancomycin"): {
        "severity": "moderate",
        "mechanism": "万古霉素肾毒性与 TDF 叠加",
        "management": "监测肾功能与万古霉素血药浓度，必要时换用 TAF",
        "nephro": True,
    },
    _pair_key("tenofovir_df", "acyclovir"): {
        "severity": "moderate",
        "mechanism": "高剂量静脉阿昔洛韦肾毒性，与 TDF 叠加",
        "management": "充分水化，监测肾功能",
        "nephro": True,
    },
    _pair_key("tenofovir_df", "rifampicin"): {
        "severity": "minor",
        "mechanism": "利福平轻度降低替诺福韦暴露，临床意义有限",
        "management": "通常无需调整，留意疗效",
        "nephro": False,
    },
    # DTG ------------------------------------------------------
    _pair_key("dolutegravir", "polyvalent_cations"): {
        "severity": "major",
        "mechanism": "二价/三价阳离子（钙、镁、铁、铝）与 DTG 螯合，显著降低吸收",
        "management": "DTG 应在含阳离子制剂前 2 小时或后 6 小时服用，或与餐同服",
        "nephro": False,
    },
    _pair_key("dolutegravir", "rifampicin"): {
        "severity": "major",
        "mechanism": "利福平强效诱导 UGT1A1/CYP3A，大幅降低 DTG 暴露",
        "management": "合用时 DTG 需加倍为每日两次；停利福平后 2 周恢复常规剂量",
        "nephro": False,
    },
    _pair_key("dolutegravir", "carbamazepine"): {
        "severity": "major",
        "mechanism": "卡马西平诱导代谢酶，降低 DTG 暴露",
        "management": "DTG 加量为每日两次，或改用非诱导剂抗癫痫药",
        "nephro": False,
    },
    _pair_key("dolutegravir", "phenytoin"): {
        "severity": "major",
        "mechanism": "苯妥英诱导代谢酶，降低 DTG 暴露",
        "management": "DTG 加量为每日两次，或改用左乙拉西坦等替代",
        "nephro": False,
    },
    _pair_key("dolutegravir", "metformin"): {
        "severity": "moderate",
        "mechanism": "DTG 抑制 OCT2/MATE，升高二甲双胍血药浓度",
        "management": "二甲双胍每日总量建议不超过 1000mg，监测血糖与乳酸",
        "nephro": False,
    },
    _pair_key("dolutegravir", "dofetilide"): {
        "severity": "contraindicated",
        "mechanism": "DTG 抑制肾脏分泌，升高多非利特浓度，致命性心律失常风险",
        "management": "绝对禁忌合用",
        "nephro": False,
    },
    _pair_key("dolutegravir", "st_johns_wort"): {
        "severity": "moderate",
        "mechanism": "贯叶连翘诱导代谢酶，降低 DTG 暴露",
        "management": "避免合用",
        "nephro": False,
    },
    # CAB（长效注射）------------------------------------------
    _pair_key("cabotegravir", "rifampicin"): {
        "severity": "contraindicated",
        "mechanism": "利福平强诱导 UGT1A1，显著降低卡博特韦暴露且长效难以补救",
        "management": "禁止合用长效卡博特韦；改用口服替代或调整结核治疗",
        "nephro": False,
    },
    _pair_key("cabotegravir", "carbamazepine"): {
        "severity": "contraindicated",
        "mechanism": "强酶诱导剂降低长效卡博特韦暴露，无法及时调整",
        "management": "禁止合用",
        "nephro": False,
    },
    _pair_key("cabotegravir", "phenytoin"): {
        "severity": "contraindicated",
        "mechanism": "苯妥英诱导代谢酶，降低长效卡博特韦暴露",
        "management": "禁止合用",
        "nephro": False,
    },
    # FTC
    _pair_key("emtricitabine", "aminoglycosides"): {
        "severity": "minor",
        "mechanism": "二者均经肾清除，理论上竞争性减少清除，临床意义小",
        "management": "肾功能不全者监测",
        "nephro": False,
    },
    # 增强剂
    _pair_key("ritonavir", "rifampicin"): {
        "severity": "major",
        "mechanism": "利福平大幅降低增强型蛋白酶抑制剂暴露",
        "management": "避免合用，结核治疗改用利福布汀",
        "nephro": False,
    },
    _pair_key("cobicistat", "rifampicin"): {
        "severity": "contraindicated",
        "mechanism": "利福平诱导 CYP3A，使考比司他增强作用失效",
        "management": "禁忌合用",
        "nephro": False,
    },
    _pair_key("cobicistat", "st_johns_wort"): {
        "severity": "contraindicated",
        "mechanism": "贯叶连翘强诱导 CYP3A，导致药物治疗失败",
        "management": "禁忌合用",
        "nephro": False,
    },
    # TAF —— 肾毒性更低，主要是吸收影响
    _pair_key("tenofovir_af", "rifampicin"): {
        "severity": "major",
        "mechanism": "利福平诱导 P-gp，显著降低 TAF 暴露",
        "management": "避免合用",
        "nephro": False,
    },
}


# 单药肾毒性权重（用于叠加评分）
_NEPHROTOXIC_WEIGHTS = {
    "tenofovir_df": 2.0,
    "aminoglycosides": 3.0,
    "cisplatin": 3.0,
    "vancomycin": 2.0,
    "nsaids": 1.5,
    "acyclovir": 1.0,
    "tenofovir_af": 0.5,
}


# --- 成对查询 / 方案查询 ---

def _make_pair_result(a, b, severity, mechanism, management, nephro,
                      has_interaction):
    return {
        "drug_a": a,
        "drug_b": b,
        "drug_a_display": drug_display_name(a),
        "drug_b_display": drug_display_name(b),
        "severity": severity,
        "severity_label": SEVERITY_LABEL_ZH[severity],
        "mechanism": mechanism,
        "management": management,
        "nephro": nephro,
        "has_interaction": has_interaction,
    }


def check_pair(drug_a, drug_b):
    a = normalize_drug(drug_a)
    b = normalize_drug(drug_b)
    if not a or not b or a == b:
        return _make_pair_result(a, b, "none", "", "", False, False)

    record = _INTERACTIONS.get(_pair_key(a, b))
    if record is None:
        return _make_pair_result(
            a, b, "none", "",
            "未检索到已知相互作用，仍建议遵医嘱", False, False,
        )
    return _make_pair_result(
        a, b,
        record["severity"], record["mechanism"], record["management"],
        record["nephro"], True,
    )


def _dedup_normalize(drug_list):
    out, seen = [], set()
    for d in drug_list:
        nd = normalize_drug(d)
        if nd and nd not in seen:
            seen.add(nd)
            out.append(nd)
    return out


def check_regimen(drug_list):
    if not drug_list:
        return []
    normalized = _dedup_normalize(drug_list)

    findings = []
    for i, a in enumerate(normalized):
        for b in normalized[i + 1:]:
            res = check_pair(a, b)
            if res["has_interaction"]:
                findings.append(res)
    return sort_by_severity(findings)


def sort_by_severity(findings):
    return sorted(
        findings,
        key=lambda r: SEVERITY_RANK.get(r.get("severity", "none"), 0),
        reverse=True,
    )


def summarize_severity(findings):
    counts = {k: 0 for k in SEVERITY_RANK if k != "none"}
    for r in findings:
        sev = r.get("severity", "none")
        if sev in counts:
            counts[sev] += 1

    highest = "none"
    for sev, n in counts.items():
        if n > 0 and SEVERITY_RANK[sev] > SEVERITY_RANK[highest]:
            highest = sev
    return {
        "counts": counts,
        "highest": highest,
        "highest_label": SEVERITY_LABEL_ZH[highest],
        "total": sum(counts.values()),
    }


# --- 肾毒性评分 ---

def nephrotoxicity_score(drug_list):
    if not drug_list:
        return {"score": 0.0, "level": "无", "nephrotoxic_drugs": [],
                "synergy": False}

    normalized = _dedup_normalize(drug_list)
    nephro_drugs = [d for d in normalized if d in _NEPHROTOXIC_WEIGHTS]
    base = float(np.sum([_NEPHROTOXIC_WEIGHTS[d] for d in nephro_drugs]))

    synergy = len(nephro_drugs) >= 2
    if synergy:
        # 每多一种肾毒性药额外 +30%
        base *= 1.0 + 0.3 * (len(nephro_drugs) - 1)

    # 权重总和约 10 视为满分量级
    raw_score = round(min(base / 10.0 * 100.0, 100.0), 1)

    if raw_score >= 60:
        level = "高"
    elif raw_score >= 30:
        level = "中"
    elif raw_score > 0:
        level = "低"
    else:
        level = "无"

    return {
        "score": raw_score,
        "level": level,
        "nephrotoxic_drugs": nephro_drugs,
        "synergy": synergy,
    }


# --- 监测建议 ---

_INDUCERS = {"rifampicin", "carbamazepine", "phenytoin", "st_johns_wort"}
_NEPHROTOXIC_SET = set(_NEPHROTOXIC_WEIGHTS)


def monitoring_recommendations(drug_list):
    if not drug_list:
        return []

    present = set()
    for d in drug_list:
        nd = normalize_drug(d)
        if nd:
            present.add(nd)

    recs = []

    def add(msg):
        if msg not in recs:
            recs.append(msg)

    if present & _NEPHROTOXIC_SET:
        add("定期监测血肌酐与 eGFR（肾功能）")
    if "tenofovir_df" in present:
        add("监测尿蛋白与血磷，警惕近端肾小管病变")
    if "dolutegravir" in present or "cabotegravir" in present:
        add("监测 HIV 病毒载量以确认整合酶抑制剂疗效")
    if "polyvalent_cations" in present and "dolutegravir" in present:
        add("严格遵守 DTG 与含阳离子制剂的服药间隔")
    if present & _INDUCERS:
        add("注意酶诱导剂可能降低抗病毒药暴露，监测疗效")
    if "metformin" in present and "dolutegravir" in present:
        add("监测血糖与血乳酸（DTG 升高二甲双胍浓度）")
    return recs


def review_regimen(drug_list):
    findings = check_regimen(drug_list)
    return {
        "interactions": findings,
        "severity_summary": summarize_severity(findings),
        "nephrotoxicity": nephrotoxicity_score(drug_list),
        "monitoring": monitoring_recommendations(drug_list),
    }
