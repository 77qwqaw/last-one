# 模型与校验函数集合 —— PK、保护概率、行为风险、PEP/PrEP、SIR、综合评分。
# 纯 numpy/math，没有 streamlit 依赖。app 和测试都从这里拿。

import math
import warnings

import numpy as np


def pk_3comp(days, miss, dose=300, k12=0.5, k21=0.3, k23=0.2, k_elim=0.15, threshold=700):
    # 口服三室简化模型，逐日迭代。返回 (浓度数组, 当前, 剩余保护天数, 阈值)
    A1 = A2 = A3 = 0.0
    conc = []
    total = days + miss
    for d in range(total):
        if d < days:
            A1 += dose
        # 三室之间的转运 + 一室代谢
        dA1 = -k12 * A1 + k21 * A2 - k_elim * A1
        dA2 = k12 * A1 - k21 * A2 - k23 * A2
        dA3 = k23 * A2 - 0.05 * A3
        A1 += dA1
        A2 += dA2
        A3 += dA3
        conc.append(A3 if A3 > 0 else 0.0)

    current = conc[-1] if conc else 0.0
    remain = np.log(current / threshold) / k_elim if current > threshold else 0.0
    return np.array(conc), current, remain, threshold


def pk_long_acting(days_since_injection, dose=600, ka=0.2, ke=0.05, threshold=200):
    # 长效注射（CAB-LA 一类）的一室口服等价近似。
    t = np.arange(days_since_injection + 1)
    conc = dose * ka / (ka - ke) * (np.exp(-ke * t) - np.exp(-ka * t))
    current = conc[-1] if len(conc) > 0 else 0.0
    remain = np.log(current / threshold) / ke if current > threshold else 0.0
    return conc, current, remain, threshold


def tfv_dp_model(days, miss, weight=70, steady_max=950):
    # TFV-DP（替诺福韦活性代谢物）浓度，体重越大清除越快。
    k_elim = 0.15 * (70 / weight)
    conc = 0.0
    history = []
    for _ in range(days):
        conc += steady_max * 0.3
        conc *= (1 - k_elim)
        history.append(conc)
    for _ in range(miss):
        conc *= (1 - k_elim)
        history.append(conc)

    # 阈值 700 fmol/10^6 cells，估算还能撑几天
    remain = 0
    temp = conc
    while temp >= 700:
        remain += 1
        temp *= (1 - k_elim)
    return np.array(history), round(conc, 2), remain, 700


def protection_prob(conc, ec50=700, slope=100):
    conc = np.asarray(conc, dtype=float)
    z = np.clip((conc - ec50) / slope, -700, 700)  # 防 exp 溢出
    return 1 / (1 + np.exp(-z))


# ---- 输入校验 ----------
# 风格统一：能修就修并 warn，修不动才 raise。
# 大多数都是 UI 端传进来的，宽容比严格更要紧。

def validate_single_score(value, name="分数"):
    try:
        v = int(float(value))
    except Exception:
        warnings.warn(f"{name} 输入非法，已自动设为 3", UserWarning)
        return 3
    if 1 <= v <= 5:
        return v
    warnings.warn(f"{name} 必须在 1-5，已自动设为 3", UserWarning)
    return 3


def validate_social_attitude(s, m, behavior_level):
    if not (1 <= s <= 5):
        raise ValueError("s 必须在 1-5 之间")
    if not (1 <= m <= 5):
        raise ValueError("m 必须在 1-5 之间")
    valid_levels = ["频繁高风险行为", "偶尔风险行为", "无高风险行为"]
    if behavior_level not in valid_levels:
        raise ValueError(f"behavior_level 必须是 {valid_levels} 中的一个")


_VALID_BEHAVIORS = {"无高风险行为", "偶尔风险行为", "频繁高风险行为"}
_VALID_EXPOSURES = {"有，72小时以内", "有，超过72小时", "没有明确近期暴露"}


def validate_behavior_input(behavior_input):
    if behavior_input in _VALID_BEHAVIORS:
        return behavior_input
    warnings.warn(f"行为等级非法：{behavior_input}，已重置为无高风险行为", UserWarning)
    return "无高风险行为"


def validate_exposure_input(exposure):
    if exposure in _VALID_EXPOSURES:
        return exposure
    warnings.warn(f"暴露输入非法：{exposure}，已重置为没有明确近期暴露", UserWarning)
    return "没有明确近期暴露"


def validate_non_negative_numeric(value, default=0, name="数值"):
    try:
        v = float(value)
    except Exception:
        warnings.warn(f"{name} 必须为数字，使用默认值 {default}", UserWarning)
        return default
    if v < 0:
        warnings.warn(f"{name} 不能为负数，使用默认值 {default}", UserWarning)
        return default
    return v


# ---- 行为概率 ----------

def behavior_prob_original(s, m, behavior_level="偶尔风险行为"):
    # 早期的加法权重，留着对照。
    validate_social_attitude(s, m, behavior_level)
    base = {"频繁高风险行为": 1.0, "偶尔风险行为": 0.5, "无高风险行为": 0.001}[behavior_level]
    sf = (5 - s) / 4.0
    mf = (5 - m) / 4.0
    if behavior_level == "频繁高风险行为":
        prob = base * (0.8 * sf + 0.2 * mf)
    else:
        prob = base * (0.6 * sf + 0.4 * mf)
    return max(0.0, min(prob, 1.0))


def behavior_prob_multiply(s, m, behavior) -> float:
    # 当前在用的版本，乘法形式比加法跌得更快。
    s_clean = validate_single_score(s, "社交态度 s")
    m_clean = validate_single_score(m, "性态度 m")
    beh_clean = validate_behavior_input(behavior)

    base = {"频繁高风险行为": 1.0, "偶尔风险行为": 0.5, "无高风险行为": 0.1}[beh_clean]
    risk = base * ((5 - s_clean) / 4) * ((5 - m_clean) / 4)
    return max(0.0, min(risk, 1.0))


# app.py 与 combined_risk_score 都按裸名 behavior_prob 调用。
behavior_prob = behavior_prob_multiply


# ---- PEP / PrEP ----------

def pep_priority_score(exposure, behavior):
    s = 0
    if exposure == "有，72小时以内":
        s += 70
    elif exposure == "有，超过72小时":
        s += 40
    if behavior == "偶尔风险行为":
        s += 15
    elif behavior == "频繁高风险行为":
        s += 25
    return min(s, 100)


def prep_need_prob(s, m, behavior, exposure):
    # 完全没暴露 + 完全无行为时给个最低基线
    if exposure == "没有明确近期暴露" and behavior == "无高风险行为":
        return 0.12

    score = 0
    if behavior == "偶尔风险行为":
        score += 35
    elif behavior == "频繁高风险行为":
        score += 65
    if exposure == "有，72小时以内":
        score += 20
    elif exposure == "有，超过72小时":
        score += 15
    score += (s - 1) * 3 + (m - 1) * 2
    return min(score, 95) / 100


# ---- 单次暴露传播概率 ----------

# 经验值（每次行为），数量级参考公开流行病学数据
_BASE_RISK = {
    'receptive_anal': 0.0138,
    'insertive_anal': 0.0011,
    'vaginal': 0.0008,
    'oral': 0.0001,
}


def hiv_transmission_prob(viral_load, exposure_type, condom_use=True,
                          circumcision=False, sti_present=False, **kwargs):
    risk = _BASE_RISK.get(exposure_type, 0.0005)

    try:
        vl = 1000.0 if viral_load is None else float(viral_load)
        vl = max(vl, 1.0)
        risk *= vl / 1000.0
    except (ValueError, TypeError):
        pass  # vl 解析失败就按基线，不要 crash

    if condom_use:
        risk *= 0.1
    if circumcision and exposure_type == 'insertive_anal':
        risk *= 0.5
    if sti_present:
        risk *= 2.0

    return max(0.0, min(risk, 0.3))


# ---- SIR ----------

def sir_simulation(beta, gamma, N, I0, days):
    # 经典 SIR 的离散时间版本，每步归一化以避免浮点漂移。
    if days <= 0:
        return np.array([]), np.array([]), np.array([])

    S = np.zeros(days)
    I = np.zeros(days)
    R = np.zeros(days)
    S[0] = N - I0
    I[0] = I0

    for t in range(days - 1):
        new_inf = beta * S[t] * I[t] / N
        new_rec = gamma * I[t]
        S[t+1] = S[t] - new_inf
        I[t+1] = I[t] + new_inf - new_rec
        R[t+1] = R[t] + new_rec
        tot = S[t+1] + I[t+1] + R[t+1]
        S[t+1] = S[t+1] * N / tot
        I[t+1] = I[t+1] * N / tot
        R[t+1] = R[t+1] * N / tot

    return S, I, R


# ---- 综合评分 ----------

def score(prot_prob, remain_days):
    s_prob = prot_prob * 70
    s_days = min(remain_days / 7, 1) * 30
    total = max(0, min(100, int(s_prob + s_days)))
    if total > 70:
        return "保护较好", "低风险", total
    if total > 40:
        return "部分保护", "中风险", total
    return "保护不足", "高风险", total


def score_protection(p, remain):
    val = int(p * 60 + min(remain / 7, 1) * 40)
    if val > 70:
        return "保护较好", "低风险", val
    if val > 40:
        return "部分保护", "中风险", val
    return "保护不足", "高风险", val


def combined_risk_score(conc, s, m, behavior):
    protection = protection_prob(conc)
    behavior_risk = behavior_prob(s, m, behavior)
    final = protection * (1 - behavior_risk)

    if final >= 0.8:
        level = "低风险"
    elif final >= 0.5:
        level = "中风险"
    else:
        level = "高风险"

    return {
        "protection_probability": float(protection),
        "behavior_risk_probability": float(behavior_risk),
        "final_score": float(final),
        "risk_level": level,
    }


# ---- 数值稳定性 / 批量 ----------

def numerical_stability_test():
    out = []
    for v in [-1e10, -1e6, -1000, 0, 700, 1000, 1e6, 1e10]:
        p = protection_prob(v)
        out.append({"input": v, "output": p, "nan": np.isnan(p), "inf": np.isinf(p)})
    return out


def batch_risk_analysis(concentration_array):
    arr = np.asarray(concentration_array, dtype=float)
    probs = protection_prob(arr)
    result = []
    for c, p in zip(arr, probs):
        if p >= 0.9:
            level = "高度保护"
        elif p >= 0.6:
            level = "中等保护"
        elif p >= 0.3:
            level = "部分保护"
        else:
            level = "保护不足"
        result.append({"concentration": float(c), "probability": float(p), "level": level})
    return result
