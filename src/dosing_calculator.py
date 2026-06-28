# 给药方案计算器（科普/教学演示，不可作为临床用药指导）。
import math
import warnings

import numpy as np


# ---- 内部校验 ----
def _require_positive(value, name):
    try:
        v = float(value)
    except (TypeError, ValueError):
        raise ValueError(f"{name} 必须为数字，收到 {value!r}")
    if not math.isfinite(v) or v <= 0:
        raise ValueError(f"{name} 必须为正的有限数，收到 {value!r}")
    return v


def _require_non_negative(value, name):
    try:
        v = float(value)
    except (TypeError, ValueError):
        raise ValueError(f"{name} 必须为数字，收到 {value!r}")
    if not math.isfinite(v) or v < 0:
        raise ValueError(f"{name} 必须为非负有限数，收到 {value!r}")
    return v


# ---- 体表面积 / 体重剂量 ----
def mosteller_bsa(height_cm, weight_kg):
    # Mosteller 公式计算体表面积 BSA (m^2)：
    height_cm = _require_positive(height_cm, "height_cm")
    weight_kg = _require_positive(weight_kg, "weight_kg")
    return math.sqrt(height_cm * weight_kg / 3600.0)


def dubois_bsa(height_cm, weight_kg):
    # Du Bois 公式计算体表面积 BSA (m^2)：
    height_cm = _require_positive(height_cm, "height_cm")
    weight_kg = _require_positive(weight_kg, "weight_kg")
    return 0.007184 * (height_cm ** 0.725) * (weight_kg ** 0.425)


def dose_by_weight(weight_kg, mg_per_kg, max_dose_mg=None):
    """
    按体重线性计算剂量：dose = weight * mg_per_kg，可选封顶 max_dose_mg。
    """
    weight_kg = _require_positive(weight_kg, "weight_kg")
    mg_per_kg = _require_positive(mg_per_kg, "mg_per_kg")
    dose = weight_kg * mg_per_kg
    if max_dose_mg is not None:
        max_dose_mg = _require_positive(max_dose_mg, "max_dose_mg")
        dose = min(dose, max_dose_mg)
    return dose


def dose_by_bsa(bsa_m2, mg_per_m2, max_dose_mg=None):
    # 按体表面积计算剂量：dose = BSA * mg_per_m2，可选封顶。
    bsa_m2 = _require_positive(bsa_m2, "bsa_m2")
    mg_per_m2 = _require_positive(mg_per_m2, "mg_per_m2")
    dose = bsa_m2 * mg_per_m2
    if max_dose_mg is not None:
        max_dose_mg = _require_positive(max_dose_mg, "max_dose_mg")
        dose = min(dose, max_dose_mg)
    return dose


# ---- 肾功能评估 ----
def cockcroft_gault_crcl(age_years, weight_kg, serum_cr_mg_dl, is_female=False):
    # Cockcroft-Gault 肌酐清除率 CrCl (mL/min)：
    age_years = _require_positive(age_years, "age_years")
    weight_kg = _require_positive(weight_kg, "weight_kg")
    scr = _require_positive(serum_cr_mg_dl, "serum_cr_mg_dl")
    crcl = (140.0 - age_years) * weight_kg / (72.0 * scr)
    if is_female:
        crcl *= 0.85
    return max(crcl, 0.0)


def ckd_epi_egfr(age_years, serum_cr_mg_dl, is_female=False):
    """
    CKD-EPI 2009 公式估算 eGFR (mL/min/1.73m^2)。
    kappa/alpha 取决于性别，Scr 单位 mg/dL。
    """
    age_years = _require_positive(age_years, "age_years")
    scr = _require_positive(serum_cr_mg_dl, "serum_cr_mg_dl")
    if is_female:
        kappa, alpha, sex_factor = 0.7, -0.329, 1.018
    else:
        kappa, alpha, sex_factor = 0.9, -0.411, 1.0
    ratio = scr / kappa
    egfr = (141.0
            * (min(ratio, 1.0) ** alpha)
            * (max(ratio, 1.0) ** -1.209)
            * (0.993 ** age_years)
            * sex_factor)
    return max(egfr, 0.0)


def renal_function_stage(egfr):
    """
    按 eGFR 划分慢性肾病 (CKD) 分级 G1-G5。
    返回 (分级代码, 中文描述)。
    """
    egfr = _require_non_negative(egfr, "egfr")
    if egfr >= 90:
        return "G1", "肾功能正常或偏高"
    if egfr >= 60:
        return "G2", "轻度下降"
    if egfr >= 45:
        return "G3a", "轻中度下降"
    if egfr >= 30:
        return "G3b", "中重度下降"
    if egfr >= 15:
        return "G4", "重度下降"
    return "G5", "肾衰竭"


# ---- TDF 按肾功能调整给药间隔 ----
def tdf_renal_dose_interval(crcl):
    # 依据 CrCl (mL/min) 给出 TDF 300mg 的推荐给药间隔（科普简化版）。 返回 dict：是否可用、间隔小时数、说明。
    crcl = _require_non_negative(crcl, "crcl")
    if crcl >= 50:
        return {"recommended": True, "interval_hours": 24,
                "note": "常规每日一次 300mg"}
    if crcl >= 30:
        return {"recommended": True, "interval_hours": 48,
                "note": "每 48 小时 300mg"}
    if crcl >= 10:
        return {"recommended": True, "interval_hours": 72,
                "note": "每 72-96 小时 300mg，需监测"}
    return {"recommended": False, "interval_hours": None,
            "note": "CrCl<10 不建议常规使用，需个体化/透析方案"}


def prep_renal_eligibility(crcl, min_crcl=60.0):
    """
    口服 PrEP（TDF/FTC）肾功能准入判断：CrCl 需 >= min_crcl(默认60)。
    返回 (是否合格 bool, 说明)。
    """
    crcl = _require_non_negative(crcl, "crcl")
    min_crcl = _require_positive(min_crcl, "min_crcl")
    if crcl >= min_crcl:
        return True, f"CrCl={crcl:.0f} >= {min_crcl:.0f}，符合口服PrEP准入"
    return False, f"CrCl={crcl:.0f} < {min_crcl:.0f}，需评估替代方案"


# ---- 儿科 / 青少年体重分段剂量 ----
def pediatric_weight_band_dose(weight_kg):
    """
    按体重分段给出 TDF/FTC 固定剂量复方片的近似剂量（科普示意）。
    返回 dict：体重段、TDF(mg)、FTC(mg)。
    """
    weight_kg = _require_positive(weight_kg, "weight_kg")
    if weight_kg < 17:
        raise ValueError("体重过低（<17kg），不在本简化方案范围")
    if weight_kg < 22:
        return {"band": "17-21kg", "tdf_mg": 150, "ftc_mg": 100}
    if weight_kg < 28:
        return {"band": "22-27kg", "tdf_mg": 200, "ftc_mg": 133}
    if weight_kg < 35:
        return {"band": "28-34kg", "tdf_mg": 250, "ftc_mg": 167}
    return {"band": ">=35kg", "tdf_mg": 300, "ftc_mg": 200}


def adolescent_prep_eligibility(weight_kg, age_years, min_weight=35.0,
                                min_age=15.0):
    """
    青少年口服 PrEP 准入：体重 >= min_weight 且年龄 >= min_age。
    返回 (是否合格, 说明)。
    """
    weight_kg = _require_positive(weight_kg, "weight_kg")
    age_years = _require_positive(age_years, "age_years")
    if weight_kg >= min_weight and age_years >= min_age:
        return True, "符合青少年口服PrEP准入（体重与年龄达标）"
    reasons = []
    if weight_kg < min_weight:
        reasons.append(f"体重{weight_kg:.0f}<{min_weight:.0f}kg")
    if age_years < min_age:
        reasons.append(f"年龄{age_years:.0f}<{min_age:.0f}岁")
    return False, "不符合：" + "，".join(reasons)


# ---- 给药时间表 / 间隔 ----
def dosing_schedule(start_hour, interval_hours, n_doses):
    # 生成等间隔给药时间表（单位：小时，相对起点）。
    start_hour = _require_non_negative(start_hour, "start_hour")
    interval_hours = _require_positive(interval_hours, "interval_hours")
    if int(n_doses) < 1:
        raise ValueError("n_doses 必须 >= 1")
    n_doses = int(n_doses)
    return start_hour + interval_hours * np.arange(n_doses, dtype=float)


def doses_per_day(interval_hours):
    """每日给药次数 = 24 / interval_hours。"""
    interval_hours = _require_positive(interval_hours, "interval_hours")
    return 24.0 / interval_hours


def total_daily_dose(dose_mg, interval_hours):
    """每日总剂量 = 单次剂量 * 每日次数。"""
    dose_mg = _require_positive(dose_mg, "dose_mg")
    return dose_mg * doses_per_day(interval_hours)


# ---- 漏服补救规则 ----
def missed_dose_rule(hours_since_due, interval_hours,
                     half_window_fraction=0.5):
    # 通用漏服补救规则：
    hours_since_due = _require_non_negative(hours_since_due,
                                           "hours_since_due")
    interval_hours = _require_positive(interval_hours, "interval_hours")
    if not (0 < half_window_fraction < 1):
        raise ValueError("half_window_fraction 必须在 0-1 之间")
    window = interval_hours * half_window_fraction
    if hours_since_due <= window:
        return {"action": "take_now", "double_dose": False,
                "note": "在补服窗内，立即补服，下次按原计划"}
    return {"action": "skip", "double_dose": False,
            "note": "已超过补服窗，跳过本次，切勿双倍补服"}


# ---- PrEP 按需给药 2-1-1 方案 ----
def prep_on_demand_211_schedule(exposure_hour=0.0):
    # 生成 PrEP 按需 2-1-1 方案时间表（事件驱动 PrEP，主要用于 MSM）：
    exposure_hour = _require_non_negative(exposure_hour, "exposure_hour")
    return [
        {"time_hour": exposure_hour - 2.0, "pills": 2,
         "label": "性行为前2-24小时负荷剂量"},
        {"time_hour": exposure_hour + 24.0, "pills": 1,
         "label": "首剂后24小时"},
        {"time_hour": exposure_hour + 48.0, "pills": 1,
         "label": "首剂后48小时"},
    ]


def prep_on_demand_extended(extra_exposure_days):
    # 2-1-1 方案在持续暴露时的延展：每多一天持续暴露需多服 1 片/天，
    extra = int(_require_non_negative(extra_exposure_days,
                                     "extra_exposure_days"))
    # 标准 4 片 + 每多一天暴露多 1 片
    return 4 + extra


# ---- 长效注射给药日历 ----
def long_acting_injection_calendar(start_day, n_injections,
                                    loading_interval_days=30,
                                    maintenance_interval_days=60):
    # 生成长效卡替拉韦注射日历（相对天）：
    start_day = _require_non_negative(start_day, "start_day")
    loading_interval_days = _require_positive(loading_interval_days,
                                             "loading_interval_days")
    maintenance_interval_days = _require_positive(
        maintenance_interval_days, "maintenance_interval_days")
    if int(n_injections) < 1:
        raise ValueError("n_injections 必须 >= 1")
    n_injections = int(n_injections)
    days = [start_day]
    for i in range(1, n_injections):
        if i == 1:
            days.append(days[-1] + loading_interval_days)
        else:
            days.append(days[-1] + maintenance_interval_days)
    return np.array(days, dtype=float)


def injection_window(target_day, window_days=7):
    # 长效注射给药窗口：目标日 ± window_days（默认 ±7 天）。
    target_day = _require_non_negative(target_day, "target_day")
    window_days = _require_positive(window_days, "window_days")
    return (target_day - window_days, target_day + window_days)


def is_injection_late(actual_day, target_day, window_days=7):
    # 判断某次实际注射是否超出给药窗（迟于 target_day + window_days）。
    actual_day = _require_non_negative(actual_day, "actual_day")
    target_day = _require_non_negative(target_day, "target_day")
    window_days = _require_positive(window_days, "window_days")
    return actual_day > target_day + window_days


# ---- 单位换算 ----
def mg_to_mmol(mg, molar_mass_g_per_mol):
    """质量(mg) -> 物质的量(mmol)：mmol = mg / molar_mass。"""
    mg = _require_non_negative(mg, "mg")
    mm = _require_positive(molar_mass_g_per_mol, "molar_mass_g_per_mol")
    return mg / mm


def mmol_to_mg(mmol, molar_mass_g_per_mol):
    """物质的量(mmol) -> 质量(mg)：mg = mmol * molar_mass。"""
    mmol = _require_non_negative(mmol, "mmol")
    mm = _require_positive(molar_mass_g_per_mol, "molar_mass_g_per_mol")
    return mmol * mm


def concentration_ng_ml_to_nmol_l(ng_ml, molar_mass_g_per_mol):
    """
    浓度换算 ng/mL -> nmol/L：nmol/L = (ng/mL) * 1000 / molar_mass。
    （1 ng/mL = 1 µg/L；除以 g/mol 得 µmol/L，再 *1000 得 nmol/L）
    """
    ng_ml = _require_non_negative(ng_ml, "ng_ml")
    mm = _require_positive(molar_mass_g_per_mol, "molar_mass_g_per_mol")
    return ng_ml * 1000.0 / mm


def serum_cr_umol_to_mg_dl(scr_umol_l):
    """血肌酐单位换算 µmol/L -> mg/dL：mg/dL = µmol/L / 88.42。"""
    scr_umol_l = _require_positive(scr_umol_l, "scr_umol_l")
    return scr_umol_l / 88.42
