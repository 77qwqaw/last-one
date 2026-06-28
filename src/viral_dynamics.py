# HIV 病毒动力学：靶细胞/感染细胞/病毒 T-I-V 三元 ODE 及推导。
# 仅作科普/教学定性演示，参数为文献量级的简化值，不可用于临床判断。
import math
import warnings

import numpy as np


# ---- 输入校验工具 ----
def _validate_positive(value, default, name="数值"):
    # 校验为正数（>0），非法或非正返回 default 并警告。
    try:
        v = float(value)
    except (TypeError, ValueError):
        warnings.warn(f"{name} 必须为数字，已使用默认值 {default}", UserWarning)
        return float(default)
    if not math.isfinite(v) or v <= 0:
        warnings.warn(f"{name} 必须为正数，已使用默认值 {default}", UserWarning)
        return float(default)
    return v


def _validate_non_negative(value, default, name="数值"):
    # 校验为非负数（>=0），非法或为负返回 default 并警告。
    try:
        v = float(value)
    except (TypeError, ValueError):
        warnings.warn(f"{name} 必须为数字，已使用默认值 {default}", UserWarning)
        return float(default)
    if not math.isfinite(v) or v < 0:
        warnings.warn(f"{name} 不能为负，已使用默认值 {default}", UserWarning)
        return float(default)
    return v


def _validate_prob(value, default, name="概率"):
    # 校验为 [0,1] 概率，越界裁剪并警告。
    try:
        v = float(value)
    except (TypeError, ValueError):
        warnings.warn(f"{name} 必须为数字，已使用默认值 {default}", UserWarning)
        return float(default)
    if not math.isfinite(v):
        warnings.warn(f"{name} 非有限值，已使用默认值 {default}", UserWarning)
        return float(default)
    if v < 0 or v > 1:
        warnings.warn(f"{name} 必须在 0-1 之间，已自动裁剪", UserWarning)
        return float(min(1.0, max(0.0, v)))
    return v


def _validate_int_days(value, default, name="天数"):
    # 校验为非负整数天数。
    try:
        v = int(float(value))
    except (TypeError, ValueError):
        warnings.warn(f"{name} 必须为整数，已使用默认值 {default}", UserWarning)
        return int(default)
    if v < 0:
        warnings.warn(f"{name} 不能为负，已使用默认值 {default}", UserWarning)
        return int(default)
    return v


# ---- 靶细胞-感染细胞-病毒 (T/I/V) 三元 ODE 模型 ----
def target_cell_model(
    days,
    dt=0.1,
    T0=1e6,
    I0=0.0,
    V0=1e-3,
    lam=1e4,
    d_T=0.01,
    beta=2e-7,
    delta=0.7,
    p=1000.0,
    c=23.0,
):
    """
    标准 HIV 靶细胞模型（欧拉数值积分）。

    状态变量：
      T —— 未感染易感 CD4+ 靶细胞 (cells/mL)
      I —— 已感染并产毒细胞 (cells/mL)
      V —— 自由病毒 (copies/mL)

    微分方程：
      dT/dt = lam - d_T*T - beta*T*V
      dI/dt = beta*T*V - delta*I
      dV/dt = p*I - c*V

    参数：
      days  总模拟时长（天）
      dt    积分步长（天），越小越稳定
      lam   靶细胞生成速率，d_T 自然死亡率
      beta  感染速率常数，delta 感染细胞死亡率
      p     单个感染细胞产毒速率，c 病毒清除率

    返回：(t, T, V, I) 四个等长 numpy 数组（时间、靶细胞、病毒、感染细胞）。
    所有状态被裁剪为非负。
    """
    days = _validate_positive(days, 30, "days")
    dt = _validate_positive(dt, 0.1, "dt")
    if dt > days:
        warnings.warn("dt 大于总时长，已将 dt 调整为 days/10", UserWarning)
        dt = days / 10.0
    T0 = _validate_non_negative(T0, 1e6, "T0")
    I0 = _validate_non_negative(I0, 0.0, "I0")
    V0 = _validate_non_negative(V0, 1e-3, "V0")
    lam = _validate_non_negative(lam, 1e4, "lam")
    d_T = _validate_non_negative(d_T, 0.01, "d_T")
    beta = _validate_non_negative(beta, 2e-7, "beta")
    delta = _validate_non_negative(delta, 0.7, "delta")
    p = _validate_non_negative(p, 1000.0, "p")
    c = _validate_non_negative(c, 23.0, "c")

    n = int(math.ceil(days / dt)) + 1
    t = np.linspace(0.0, days, n)
    T = np.zeros(n)
    I = np.zeros(n)
    V = np.zeros(n)
    T[0], I[0], V[0] = T0, I0, V0

    for k in range(n - 1):
        dT = lam - d_T * T[k] - beta * T[k] * V[k]
        dI = beta * T[k] * V[k] - delta * I[k]
        dV = p * I[k] - c * V[k]
        T[k + 1] = max(T[k] + dt * dT, 0.0)
        I[k + 1] = max(I[k] + dt * dI, 0.0)
        V[k + 1] = max(V[k] + dt * dV, 0.0)

    return t, T, V, I


def basic_reproductive_number(
    beta=2e-7,
    p=1000.0,
    c=23.0,
    delta=0.7,
    lam=1e4,
    d_T=0.01,
):
    """
    病毒基本感染再生数 R0。

    对靶细胞模型，无病平衡时 T* = lam/d_T，
    R0 = beta * p * T* / (c * delta)
    R0 > 1 表示感染可建立并扩增，R0 < 1 表示感染倾向于消退。
    """
    beta = _validate_non_negative(beta, 2e-7, "beta")
    p = _validate_non_negative(p, 1000.0, "p")
    c = _validate_positive(c, 23.0, "c")
    delta = _validate_positive(delta, 0.7, "delta")
    lam = _validate_non_negative(lam, 1e4, "lam")
    d_T = _validate_positive(d_T, 0.01, "d_T")

    T_star = lam / d_T
    r0 = beta * p * T_star / (c * delta)
    return float(r0)


# ---- 急性期峰值与 set point ----
def acute_peak_and_setpoint(t, V):
    # 从病毒载量轨迹中提取急性期峰值与 set point。
    V = np.asarray(V, dtype=float)
    t = np.asarray(t, dtype=float)
    if V.size == 0 or t.size != V.size:
        warnings.warn("t 与 V 必须等长且非空，返回 0", UserWarning)
        return {"peak_value": 0.0, "peak_time": 0.0, "set_point": 0.0}

    peak_idx = int(np.argmax(V))
    peak_value = float(V[peak_idx])
    peak_time = float(t[peak_idx])

    tail_start = max(peak_idx, int(V.size * 3 / 4))
    tail = V[tail_start:]
    if tail.size == 0:
        tail = V[-1:]
    set_point = float(np.median(tail))

    return {
        "peak_value": peak_value,
        "peak_time": peak_time,
        "set_point": set_point,
    }


# ---- ART 治疗后病毒载量双相衰减 ----
def art_biphasic_decay(t_days, V0=1e5, f_fast=0.95, k_fast=0.5, k_slow=0.05):
    """
    ART 启动后病毒载量的双相指数衰减模型。

    V(t) = V0 * [ f_fast * exp(-k_fast*t) + (1-f_fast) * exp(-k_slow*t) ]

    - 第一相（快相，k_fast）：自由病毒与短寿命感染细胞快速清除。
    - 第二相（慢相，k_slow）：长寿命感染细胞缓慢清除。

    t_days 可为标量或数组（天）。返回与输入同形状的载量数组。
    """
    t_days = np.asarray(t_days, dtype=float)
    V0 = _validate_non_negative(V0, 1e5, "V0")
    f_fast = _validate_prob(f_fast, 0.95, "f_fast")
    k_fast = _validate_positive(k_fast, 0.5, "k_fast")
    k_slow = _validate_positive(k_slow, 0.05, "k_slow")

    t_clip = np.clip(t_days, 0.0, None)
    v = V0 * (f_fast * np.exp(-k_fast * t_clip) + (1.0 - f_fast) * np.exp(-k_slow * t_clip))
    return v


def viral_clearance_half_life(rate):
    # 给定一阶清除速率常数 rate（每天），返回半衰期（天）：t1/2 = ln2 / rate。
    rate = _validate_positive(rate, 0.5, "rate")
    return float(math.log(2.0) / rate)


def time_to_undetectable(V0=1e5, k_fast=0.5, f_fast=0.95, k_slow=0.05,
                         limit=50.0, max_days=365, dt=0.5):
    """
    估计 ART 后病毒载量降到检测限 limit 以下所需天数（双相衰减）。

    采用细步长扫描首次跌破 limit 的时间；若 max_days 内未达到则返回 max_days
    并警告。返回 float 天数。
    """
    V0 = _validate_non_negative(V0, 1e5, "V0")
    limit = _validate_positive(limit, 50.0, "limit")
    max_days = _validate_positive(max_days, 365, "max_days")
    dt = _validate_positive(dt, 0.5, "dt")

    if V0 <= limit:
        return 0.0

    t = 0.0
    while t <= max_days:
        v = art_biphasic_decay(t, V0=V0, f_fast=f_fast, k_fast=k_fast, k_slow=k_slow)
        if float(v) <= limit:
            return float(t)
        t += dt
    warnings.warn("在 max_days 内未降至检测限以下", UserWarning)
    return float(max_days)


# ---- 潜伏库衰减 ----
def latent_reservoir_decay(t_days, L0=1e6, half_life_days=1340.0):
    """
    潜伏感染细胞库的缓慢指数衰减。

    L(t) = L0 * exp(-ln2 / half_life * t)
    文献中潜伏库半衰期约 44 个月（~1340 天），自然清除极慢。
    t_days 可为标量或数组。返回库大小数组。
    """
    t_days = np.asarray(t_days, dtype=float)
    L0 = _validate_non_negative(L0, 1e6, "L0")
    half_life_days = _validate_positive(half_life_days, 1340.0, "half_life_days")

    k = math.log(2.0) / half_life_days
    t_clip = np.clip(t_days, 0.0, None)
    return L0 * np.exp(-k * t_clip)


def reservoir_eradication_time(L0=1e6, half_life_days=1340.0, target=1.0):
    # 在纯指数衰减假设下，潜伏库从 L0 降到 target 个细胞所需的天数。
    L0 = _validate_positive(L0, 1e6, "L0")
    half_life_days = _validate_positive(half_life_days, 1340.0, "half_life_days")
    target = _validate_positive(target, 1.0, "target")
    if target >= L0:
        return 0.0
    k = math.log(2.0) / half_life_days
    return float(math.log(L0 / target) / k)


# ---- 耐药突变出现概率 ----
def resistance_mutation_prob(viral_population, mutation_rate=3e-5, n_sites=1):
    """
    估计病毒群体中至少出现一个特定耐药突变的概率。

    设每次复制每位点突变率 mutation_rate，需要 n_sites 个独立位点同时突变
    （高耐药屏障药物 n_sites 更大）。单个病毒携带该耐药组合的概率
    p_single = mutation_rate ** n_sites。在群体规模 N 下，至少一个携带的概率：
      P = 1 - (1 - p_single) ** N
    随病毒群体 N 上升而单调上升（趋于 1）。
    """
    N = _validate_non_negative(viral_population, 0.0, "viral_population")
    mutation_rate = _validate_prob(mutation_rate, 3e-5, "mutation_rate")
    try:
        n_sites = int(n_sites)
    except (TypeError, ValueError):
        warnings.warn("n_sites 必须为整数，已使用默认值 1", UserWarning)
        n_sites = 1
    if n_sites < 1:
        warnings.warn("n_sites 至少为 1，已使用 1", UserWarning)
        n_sites = 1

    p_single = mutation_rate ** n_sites
    if N <= 0 or p_single <= 0:
        return 0.0
    # 用 expm1/log1p 提升小概率大群体下的数值精度。
    prob = -math.expm1(N * math.log1p(-p_single))
    return float(min(1.0, max(0.0, prob)))


# ---- 病毒载量 / log10 换算与检测限 ----
def viral_load_to_log10(copies):
    """
    将病毒载量（copies/mL）换算为 log10 拷贝数。
    copies <= 0 视为不可检出，返回 0.0 并警告。
    支持标量或数组。
    """
    arr = np.asarray(copies, dtype=float)
    if arr.ndim == 0:
        v = float(arr)
        if v <= 0:
            warnings.warn("载量须为正数，log10 返回 0", UserWarning)
            return 0.0
        return float(math.log10(v))
    out = np.where(arr > 0, np.log10(np.clip(arr, 1e-12, None)), 0.0)
    return out


def log10_to_viral_load(log10_copies):
    """将 log10 拷贝数换算回病毒载量（copies/mL）。支持标量或数组。"""
    arr = np.asarray(log10_copies, dtype=float)
    if arr.ndim == 0:
        return float(10.0 ** float(arr))
    return np.power(10.0, arr)


def is_below_detection(viral_load, limit=50.0):
    """
    判定病毒载量是否在检测限以下（U=U 的常用阈值约 50 copies/mL）。
    返回 bool。非法载量按 0 处理（视为检测不到）。
    """
    vl = _validate_non_negative(viral_load, 0.0, "viral_load")
    limit = _validate_positive(limit, 50.0, "limit")
    return bool(vl < limit)


# ---- 暴露后病毒建立窗口期与 eclipse phase ----
def eclipse_phase_duration(inoculum=1.0, growth_rate=1.5, detect_threshold=1.0):
    """
    暴露后病毒的 eclipse phase（隐蔽期）估计：从初始接种病毒量 inoculum
    指数扩增到可被本地检测阈值 detect_threshold 所需的天数。

    若 inoculum 已达阈值，返回 0。growth_rate 为每天的净指数增长率。
    返回天数（float）。
    """
    inoculum = _validate_positive(inoculum, 1.0, "inoculum")
    growth_rate = _validate_positive(growth_rate, 1.5, "growth_rate")
    detect_threshold = _validate_positive(detect_threshold, 1.0, "detect_threshold")
    if inoculum >= detect_threshold:
        return 0.0
    return float(math.log(detect_threshold / inoculum) / growth_rate)


def establishment_window(inoculum=1.0, growth_rate=1.5,
                         systemic_threshold=1e3, eclipse_threshold=1.0):
    """
    暴露后病毒建立窗口期估计。

    分两阶段：
      eclipse：从接种量增长到本地可检阈值 eclipse_threshold。
      systemic：进一步增长到系统性感染阈值 systemic_threshold（血浆可测）。

    返回 dict：eclipse_days / systemic_days / total_days。
    total_days 即 PrEP/PEP 干预的"机会窗口"近似上限。
    """
    inoculum = _validate_positive(inoculum, 1.0, "inoculum")
    growth_rate = _validate_positive(growth_rate, 1.5, "growth_rate")
    systemic_threshold = _validate_positive(systemic_threshold, 1e3, "systemic_threshold")
    eclipse_threshold = _validate_positive(eclipse_threshold, 1.0, "eclipse_threshold")

    if systemic_threshold < eclipse_threshold:
        warnings.warn("systemic_threshold 应大于 eclipse_threshold，已交换", UserWarning)
        systemic_threshold, eclipse_threshold = eclipse_threshold, systemic_threshold

    eclipse_days = eclipse_phase_duration(inoculum, growth_rate, eclipse_threshold)
    systemic_days = float(math.log(systemic_threshold / inoculum) / growth_rate)
    systemic_days = max(systemic_days, eclipse_days)
    return {
        "eclipse_days": eclipse_days,
        "systemic_days": systemic_days,
        "total_days": systemic_days,
    }
