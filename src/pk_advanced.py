# 高级 PK：基础参数换算、一/二/三室模型、AUC、多剂量稳态、长效尾巴等。
# 模型层都是纯函数；非法输入一律 raise ValueError（测试也这么要求）。
import math
import warnings  # noqa: F401  app 层依赖本模块时一并继承使用

import numpy as np


LN2 = math.log(2.0)
_EPS = 1e-9


# -- 校验小工具（不抛 docstring，名字已经够清楚）

def _to_float(value, name):
    try:
        v = float(value)
    except (TypeError, ValueError):
        raise ValueError(f"{name} 必须为数字，收到 {value!r}")
    if not math.isfinite(v):
        raise ValueError(f"{name} 必须为有限数，收到 {v}")
    return v


def _require_positive(value, name):
    v = _to_float(value, name)
    if v <= 0:
        raise ValueError(f"{name} 必须为正数，收到 {v}")
    return v


def _require_non_negative(value, name):
    v = _to_float(value, name)
    if v < 0:
        raise ValueError(f"{name} 不能为负数，收到 {v}")
    return v


def _require_fraction(value, name):
    v = _require_non_negative(value, name)
    if v > 1.0:
        raise ValueError(f"{name} 必须在 0-1 之间，收到 {v}")
    return v


def _as_time_array(t, name="time"):
    arr = np.asarray(t, dtype=float).reshape(-1)
    if arr.size == 0:
        raise ValueError(f"{name} 不能为空")
    if not np.all(np.isfinite(arr)):
        raise ValueError(f"{name} 含有非有限值")
    if np.any(arr < 0):
        raise ValueError(f"{name} 不能为负数")
    return arr


# -- PK 基础参数换算

def half_life_from_ke(ke):
    return LN2 / _require_positive(ke, "ke")


def ke_from_half_life(t_half):
    return LN2 / _require_positive(t_half, "t_half")


def clearance(ke, vd):
    return _require_positive(ke, "ke") * _require_positive(vd, "vd")


def volume_of_distribution(dose, c0, bioavailability=1.0):
    # 适用于 IV 或瞬时分布近似：Vd = F * Dose / C0
    dose = _require_positive(dose, "dose")
    c0 = _require_positive(c0, "c0")
    f = _require_fraction(bioavailability, "bioavailability")
    return f * dose / c0


def elimination_rate_from_cl_vd(cl, vd):
    return _require_positive(cl, "cl") / _require_positive(vd, "vd")


# -- 一室模型

def one_compartment_iv(t, dose, vd, ke):
    dose = _require_positive(dose, "dose")
    vd = _require_positive(vd, "vd")
    ke = _require_positive(ke, "ke")
    scalar = np.isscalar(t)
    tt = _as_time_array(t, "t")
    conc = (dose / vd) * np.exp(-ke * tt)
    return float(conc[0]) if scalar else conc


def one_compartment_oral(t, dose, vd, ka, ke, bioavailability=1.0):
    # Bateman 解析解；ka≈ke 时退化为 flip-flop 极限。
    dose = _require_positive(dose, "dose")
    vd = _require_positive(vd, "vd")
    ka = _require_positive(ka, "ka")
    ke = _require_positive(ke, "ke")
    f = _require_fraction(bioavailability, "bioavailability")
    scalar = np.isscalar(t)
    tt = _as_time_array(t, "t")
    coeff = f * dose / vd

    if abs(ka - ke) < _EPS:
        conc = coeff * ke * tt * np.exp(-ke * tt)
    else:
        conc = coeff * ka / (ka - ke) * (np.exp(-ke * tt) - np.exp(-ka * tt))
    conc = np.maximum(conc, 0.0)
    return float(conc[0]) if scalar else conc


def bateman_function(t, ka, ke, scale=1.0):
    ka = _require_positive(ka, "ka")
    ke = _require_positive(ke, "ke")
    scale = _require_non_negative(scale, "scale")
    scalar = np.isscalar(t)
    tt = _as_time_array(t, "t")

    if abs(ka - ke) < _EPS:
        val = scale * ke * tt * np.exp(-ke * tt)
    else:
        val = scale * ka / (ka - ke) * (np.exp(-ke * tt) - np.exp(-ka * tt))
    val = np.maximum(val, 0.0)
    return float(val[0]) if scalar else val


def tmax_oral(ka, ke):
    ka = _require_positive(ka, "ka")
    ke = _require_positive(ke, "ke")
    if abs(ka - ke) < _EPS:
        return 1.0 / ke
    return math.log(ka / ke) / (ka - ke)


def cmax_oral(dose, vd, ka, ke, bioavailability=1.0):
    return one_compartment_oral(tmax_oral(ka, ke), dose, vd, ka, ke,
                                bioavailability)


# -- 双室模型

def _two_compartment_eigen(k10, k12, k21):
    s = k10 + k12 + k21
    disc = math.sqrt(max(s * s - 4.0 * k10 * k21, 0.0))
    return (s + disc) / 2.0, (s - disc) / 2.0   # alpha, beta


def two_compartment_iv(t, dose, v1, k10, k12, k21):
    dose = _require_positive(dose, "dose")
    v1 = _require_positive(v1, "v1")
    k10 = _require_positive(k10, "k10")
    k12 = _require_non_negative(k12, "k12")
    k21 = _require_positive(k21, "k21")
    scalar = np.isscalar(t)
    tt = _as_time_array(t, "t")

    alpha, beta = _two_compartment_eigen(k10, k12, k21)
    c0 = dose / v1

    if abs(alpha - beta) < 1e-12:
        conc = c0 * np.exp(-alpha * tt)
    else:
        a_coeff = c0 * (alpha - k21) / (alpha - beta)
        b_coeff = c0 * (k21 - beta) / (alpha - beta)
        conc = a_coeff * np.exp(-alpha * tt) + b_coeff * np.exp(-beta * tt)
    conc = np.maximum(conc, 0.0)
    return float(conc[0]) if scalar else conc


def two_compartment_macro_constants(k10, k12, k21):
    k10 = _require_positive(k10, "k10")
    k12 = _require_non_negative(k12, "k12")
    k21 = _require_positive(k21, "k21")
    return _two_compartment_eigen(k10, k12, k21)


# -- 三室数值解（前向欧拉）

def three_compartment_numeric(t, dose, k12=0.5, k21=0.3, k23=0.2,
                              k32=0.1, k10=0.15, dt=None):
    dose = _require_positive(dose, "dose")
    for nm, vv in (("k12", k12), ("k21", k21), ("k23", k23),
                   ("k32", k32), ("k10", k10)):
        _require_non_negative(vv, nm)
    tt = _as_time_array(t, "t")
    t_end = float(tt[-1])

    if dt is None:
        dt = max(t_end / 2000.0, 1e-3)
    dt = _require_positive(dt, "dt")
    n = int(math.ceil(t_end / dt)) + 1
    grid = np.linspace(0.0, dt * (n - 1), n)

    A1 = np.zeros(n)
    A2 = np.zeros(n)
    A3 = np.zeros(n)
    A1[0] = dose
    for i in range(n - 1):
        a1, a2, a3 = A1[i], A2[i], A3[i]
        A1[i + 1] = max(a1 + (-k12 * a1 + k21 * a2 - k10 * a1) * dt, 0.0)
        A2[i + 1] = max(a2 + (k12 * a1 - k21 * a2 - k23 * a2 + k32 * a3) * dt, 0.0)
        A3[i + 1] = max(a3 + (k23 * a2 - k32 * a3) * dt, 0.0)

    return tt, np.interp(tt, grid, A1), np.interp(tt, grid, A2), np.interp(tt, grid, A3)


# -- AUC / 暴露量

def auc_trapezoid(times, concentrations):
    t = _as_time_array(times, "times")
    c = np.asarray(concentrations, dtype=float).reshape(-1)
    if c.size != t.size:
        raise ValueError("times 与 concentrations 长度必须一致")
    if np.any(np.diff(t) < 0):
        raise ValueError("times 必须单调非降")
    if np.any(c < -1e-9):
        raise ValueError("concentrations 不能为负")
    trap = getattr(np, "trapezoid", np.trapz)
    return float(trap(c, t))


def auc_inf_oral(dose, cl, bioavailability=1.0):
    return (_require_fraction(bioavailability, "bioavailability")
            * _require_positive(dose, "dose")
            / _require_positive(cl, "cl"))


def auc_tail(c_last, ke):
    return _require_non_negative(c_last, "c_last") / _require_positive(ke, "ke")


# -- 多剂量叠加 / 稳态

def multidose_superposition(t, dose, vd, ka, ke, tau, n_doses,
                            bioavailability=1.0):
    tau = _require_positive(tau, "tau")
    n_doses = int(n_doses)
    if n_doses < 1:
        raise ValueError("n_doses 必须 >= 1")

    scalar = np.isscalar(t)
    tt = _as_time_array(t, "t")
    total = np.zeros_like(tt)

    for i in range(n_doses):
        t0 = i * tau
        mask = tt >= t0
        if not mask.any():
            continue
        total[mask] += one_compartment_oral(
            tt[mask] - t0, dose, vd, ka, ke, bioavailability
        )
    total = np.maximum(total, 0.0)
    return float(total[0]) if scalar else total


def accumulation_factor(ke, tau):
    ke = _require_positive(ke, "ke")
    tau = _require_positive(tau, "tau")
    return 1.0 / (1.0 - math.exp(-ke * tau))


def steady_state_css_avg(dose, cl, tau, bioavailability=1.0):
    dose = _require_positive(dose, "dose")
    cl = _require_positive(cl, "cl")
    tau = _require_positive(tau, "tau")
    f = _require_fraction(bioavailability, "bioavailability")
    return f * dose / (cl * tau)


def steady_state_cmax_cmin(dose, vd, ka, ke, tau, bioavailability=1.0):
    """Cmax_ss / Cmin_ss / Tmax_ss。ka≈ke 时退化为数值叠加近似。"""
    dose = _require_positive(dose, "dose")
    vd = _require_positive(vd, "vd")
    ka = _require_positive(ka, "ka")
    ke = _require_positive(ke, "ke")
    tau = _require_positive(tau, "tau")
    f = _require_fraction(bioavailability, "bioavailability")

    degenerate = abs(ka - ke) <= _EPS
    coeff = None if degenerate else f * dose * ka / (vd * (ka - ke))

    def css(time):
        if degenerate:
            return multidose_superposition(
                np.array([time + 50 * tau]),
                dose, vd, ka, ke, tau, 51, bioavailability,
            )[0]
        e = math.exp(-ke * time) / (1.0 - math.exp(-ke * tau))
        a = math.exp(-ka * time) / (1.0 - math.exp(-ka * tau))
        return coeff * (e - a)

    if degenerate:
        tmax_ss = tmax_oral(ka, ke)
    else:
        num = ka * (1.0 - math.exp(-ke * tau))
        den = ke * (1.0 - math.exp(-ka * tau))
        tmax_ss = max(0.0, math.log(num / den) / (ka - ke))

    return float(max(css(tmax_ss), 0.0)), float(max(css(tau), 0.0)), float(tmax_ss)


def time_to_steady_state(ke, fraction=0.95):
    ke = _require_positive(ke, "ke")
    fraction = _require_fraction(fraction, "fraction")
    if fraction >= 1.0:
        raise ValueError("fraction 必须 < 1")
    return -math.log2(1.0 - fraction) * half_life_from_ke(ke)


# -- 负荷 / 维持 / 剂量等效

def loading_dose(target_css, vd, bioavailability=1.0):
    return (_require_positive(target_css, "target_css")
            * _require_positive(vd, "vd")
            / _require_fraction(bioavailability, "bioavailability"))


def maintenance_dose(target_css, cl, tau, bioavailability=1.0):
    return (_require_positive(target_css, "target_css")
            * _require_positive(cl, "cl")
            * _require_positive(tau, "tau")
            / _require_fraction(bioavailability, "bioavailability"))


def dose_adjust_for_bioavailability(oral_dose, f_old, f_new):
    oral_dose = _require_positive(oral_dose, "oral_dose")
    f_old = _require_fraction(f_old, "f_old")
    f_new = _require_fraction(f_new, "f_new")
    if f_new == 0:
        raise ValueError("f_new 不能为 0")
    return oral_dose * f_old / f_new


# -- TFV-DP 多周期累积

def tfv_dp_multicycle(n_doses, dose_effect=120.0, ke_cell=0.05,
                      tau=1.0, c_init=0.0):
    # 每周期：吸收 dose_effect，然后 exp(-ke_cell*tau) 衰减。
    # ke_cell 较小 -> 细胞内半衰期长 -> 漏服较宽容（TDF/FTC PrEP 的关键性质）。
    n_doses = int(n_doses)
    if n_doses < 1:
        raise ValueError("n_doses 必须 >= 1")
    dose_effect = _require_non_negative(dose_effect, "dose_effect")
    ke_cell = _require_positive(ke_cell, "ke_cell")
    tau = _require_positive(tau, "tau")
    c_init = _require_non_negative(c_init, "c_init")

    decay = math.exp(-ke_cell * tau)
    history = np.zeros(n_doses)
    conc = c_init
    for i in range(n_doses):
        conc = (conc + dose_effect) * decay
        history[i] = conc
    return history


def tfv_dp_steady_state(dose_effect=120.0, ke_cell=0.05, tau=1.0):
    dose_effect = _require_non_negative(dose_effect, "dose_effect")
    ke_cell = _require_positive(ke_cell, "ke_cell")
    tau = _require_positive(tau, "tau")
    decay = math.exp(-ke_cell * tau)
    return dose_effect * decay / (1.0 - decay)


# -- 长效注射尾端衰减

def long_acting_tail(days_since_last, c_at_last, ke,
                     protection_threshold=200.0):
    c_at_last = _require_positive(c_at_last, "c_at_last")
    ke = _require_positive(ke, "ke")
    protection_threshold = _require_positive(protection_threshold,
                                             "protection_threshold")
    scalar = np.isscalar(days_since_last)
    days = _as_time_array(days_since_last, "days_since_last")
    conc = c_at_last * np.exp(-ke * days)

    if c_at_last <= protection_threshold:
        cross_day = 0.0
    else:
        cross_day = math.log(c_at_last / protection_threshold) / ke
    return (float(conc[0]) if scalar else conc), cross_day


def long_acting_tail_pharmacokinetic_tail_days(c_at_last, ke, threshold=200.0):
    c_at_last = _require_positive(c_at_last, "c_at_last")
    ke = _require_positive(ke, "ke")
    threshold = _require_positive(threshold, "threshold")
    if c_at_last <= threshold:
        return 0.0
    return math.log(c_at_last / threshold) / ke


# -- 漏服恢复

def missed_dose_recovery(n_days, miss_start, miss_count,
                         dose_effect=120.0, ke_cell=0.05, tau=1.0,
                         c_init=0.0):
    n_days = int(n_days)
    if n_days < 1:
        raise ValueError("n_days 必须 >= 1")
    miss_start = int(_require_non_negative(miss_start, "miss_start"))
    miss_count = int(_require_non_negative(miss_count, "miss_count"))
    dose_effect = _require_non_negative(dose_effect, "dose_effect")
    ke_cell = _require_positive(ke_cell, "ke_cell")
    tau = _require_positive(tau, "tau")
    c_init = _require_non_negative(c_init, "c_init")

    decay = math.exp(-ke_cell * tau)
    miss_lo, miss_hi = miss_start, miss_start + miss_count
    conc = c_init
    history = np.zeros(n_days)
    for i in range(n_days):
        if not (miss_lo <= i < miss_hi):
            conc += dose_effect
        conc *= decay
        history[i] = conc
    return history


def recovery_doses_to_target(c_now, target, dose_effect=120.0,
                             ke_cell=0.05, tau=1.0, max_doses=365):
    c_now = _require_non_negative(c_now, "c_now")
    target = _require_positive(target, "target")
    dose_effect = _require_non_negative(dose_effect, "dose_effect")
    ke_cell = _require_positive(ke_cell, "ke_cell")
    tau = _require_positive(tau, "tau")
    max_doses = int(max_doses)

    if c_now >= target:
        return 0
    decay = math.exp(-ke_cell * tau)
    conc = c_now
    for i in range(1, max_doses + 1):
        conc = (conc + dose_effect) * decay
        if conc >= target:
            return i
    return None


# -- 综合估计

def protection_days_remaining(current_conc, ke, threshold=700.0):
    current_conc = _require_non_negative(current_conc, "current_conc")
    ke = _require_positive(ke, "ke")
    threshold = _require_positive(threshold, "threshold")
    if current_conc <= threshold:
        return 0.0
    return math.log(current_conc / threshold) / ke


def fraction_of_steady_state(n_doses, ke, tau):
    n_doses = int(n_doses)
    if n_doses < 0:
        raise ValueError("n_doses 不能为负")
    ke = _require_positive(ke, "ke")
    tau = _require_positive(tau, "tau")
    return 1.0 - math.exp(-n_doses * ke * tau)
