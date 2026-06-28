# 依从性相关计算。PDC/MPR、漏服模拟、forgiveness window、评分等。
import math
import warnings as warn_mod

import numpy as np


def _warn(msg):
    warn_mod.warn(msg, UserWarning)


def validate_non_negative_int(value, default=0, name="整数"):
    try:
        v = int(round(float(value)))
    except (ValueError, TypeError):
        _warn(f"{name} 必须为整数，使用默认值 {default}")
        return default
    if v < 0:
        _warn(f"{name} 不能为负，使用默认值 {default}")
        return default
    return v


def validate_probability(value, default=0.0, name="概率"):
    try:
        v = float(value)
    except (ValueError, TypeError):
        _warn(f"{name} 必须为数字，使用默认值 {default}")
        return default
    if math.isnan(v):
        _warn(f"{name} 为 NaN，使用默认值 {default}")
        return default
    if v < 0:
        _warn(f"{name} 小于 0，已裁剪为 0")
        return 0.0
    if v > 1:
        _warn(f"{name} 大于 1，已裁剪为 1")
        return 1.0
    return v


def validate_positive_numeric(value, default=1.0, name="数值"):
    try:
        v = float(value)
    except (ValueError, TypeError):
        _warn(f"{name} 必须为数字，使用默认值 {default}")
        return default
    if math.isnan(v) or v <= 0:
        _warn(f"{name} 必须为正数，使用默认值 {default}")
        return default
    return v


def validate_dose_log(log, n_days=None):
    # 把任意输入折叠成 0/1 数组，可选定长
    try:
        arr = np.asarray(list(log), dtype=float)
    except TypeError:
        _warn("服药日志无法迭代，使用空日志")
        arr = np.zeros(0, dtype=float)

    if arr.size:
        if np.any((arr != 0) & (arr != 1)):
            _warn("服药日志含非 0/1 元素，已按非零折叠为 1")
        cleaned = (arr != 0).astype(int)
    else:
        cleaned = np.zeros(0, dtype=int)

    if n_days is None:
        return cleaned

    n = validate_non_negative_int(n_days, default=0, name="天数")
    if cleaned.size >= n:
        return cleaned[:n]
    pad = np.zeros(n - cleaned.size, dtype=int)
    return np.concatenate([cleaned, pad])


# ===== 依从率 =====

def proportion_days_covered(dose_log, n_days=None):
    log = validate_dose_log(dose_log, n_days=n_days)
    if log.size == 0:
        return 0.0
    return float(log.sum() / log.size)


def medication_possession_ratio(doses_dispensed, n_days):
    """MPR 可能 > 1（提前补药），这里不裁剪上界。"""
    doses = validate_non_negative_int(doses_dispensed, default=0, name="发药天数")
    n = validate_non_negative_int(n_days, default=0, name="观察天数")
    return 0.0 if n == 0 else float(doses / n)


def adherence_rate_from_log(dose_log, n_days=None):
    return proportion_days_covered(dose_log, n_days=n_days)


def doses_taken_and_missed(dose_log, n_days=None):
    log = validate_dose_log(dose_log, n_days=n_days)
    taken = int(log.sum())
    total = int(log.size)
    return taken, total - taken, total


# ===== 漏服模式模拟 =====

def simulate_random_missing(n_days, miss_prob, seed=None):
    n = validate_non_negative_int(n_days, default=0, name="天数")
    p_miss = validate_probability(miss_prob, default=0.0, name="漏服概率")
    if n == 0:
        return np.zeros(0, dtype=int)
    rng = np.random.default_rng(seed)
    return (rng.random(n) >= p_miss).astype(int)


def simulate_periodic_missing(n_days, period, offset=0):
    n = validate_non_negative_int(n_days, default=0, name="天数")
    if n == 0:
        return np.zeros(0, dtype=int)
    p = validate_non_negative_int(period, default=0, name="周期")
    off = validate_non_negative_int(offset, default=0, name="相位")
    log = np.ones(n, dtype=int)
    if p <= 0:
        return log
    idx = np.arange(n)
    log[((idx - off) % p == 0) & (idx >= off)] = 0
    return log


def simulate_consecutive_missing(n_days, miss_start, miss_len):
    n = validate_non_negative_int(n_days, default=0, name="天数")
    start = validate_non_negative_int(miss_start, default=0, name="起始日")
    length = validate_non_negative_int(miss_len, default=0, name="漏服时长")
    log = np.ones(n, dtype=int)
    if n == 0 or length == 0 or start >= n:
        return log
    log[start:min(start + length, n)] = 0
    return log


def longest_consecutive_gap(dose_log, n_days=None):
    log = validate_dose_log(dose_log, n_days=n_days)
    longest = current = 0
    for v in log:
        if v == 0:
            current += 1
            if current > longest:
                longest = current
        else:
            current = 0
    return int(longest)


def count_gaps(dose_log, n_days=None):
    log = validate_dose_log(dose_log, n_days=n_days)
    gaps = 0
    prev = 1
    for v in log:
        if v == 0 and prev == 1:
            gaps += 1
        prev = v
    return int(gaps)


# ===== 依从性 → 保护浓度 =====

def steady_state_fraction(adherence_rate, n_per_week_for_full=7.0):
    # TFV-DP 在直肠组织约每周 4 次给药即可接近最大保护；这里用饱和曲线近似。
    a = validate_probability(adherence_rate, default=0.0, name="依从率")
    weekly = a * 7.0
    return float(np.clip(weekly / (weekly + 2.0), 0.0, 1.0))


def adherence_protection_curve(adherence_rates, max_conc=1000.0, ec50=700.0, slope=100.0):
    rates = np.clip(np.atleast_1d(np.asarray(adherence_rates, dtype=float)), 0.0, 1.0)
    fracs = np.array([steady_state_fraction(a) for a in rates])
    concs = fracs * float(max_conc)
    x = np.clip((concs - ec50) / slope, -700, 700)
    return concs, 1.0 / (1.0 + np.exp(-x))


def protection_from_adherence(adherence_rate, max_conc=1000.0, ec50=700.0, slope=100.0):
    _, prot = adherence_protection_curve(
        [adherence_rate], max_conc=max_conc, ec50=ec50, slope=slope
    )
    return float(prot[0])


# ===== forgiveness window =====

def forgiveness_window(steady_conc=1000.0, k_elim=0.15, threshold=700.0):
    c0 = validate_positive_numeric(steady_conc, default=1000.0, name="稳态浓度")
    k = validate_positive_numeric(k_elim, default=0.15, name="消除速率")
    if k >= 1:  # 每日衰减 100% 以上无意义
        k = 0.15
    thr = validate_positive_numeric(threshold, default=700.0, name="阈值")
    if c0 <= thr:
        return 0.0
    # (1-k)^t = thr/c0
    return float(max(0.0, math.log(thr / c0) / math.log(1.0 - k)))


def days_of_protection_remaining(current_conc, k_elim=0.15, threshold=700.0):
    if not current_conc or current_conc <= 0:
        return 0.0
    c = validate_positive_numeric(current_conc, default=0.0, name="当前浓度")
    k = validate_positive_numeric(k_elim, default=0.15, name="消除速率")
    thr = validate_positive_numeric(threshold, default=700.0, name="阈值")
    if c <= thr:
        return 0.0
    return float(max(0.0, math.log(thr / c) / math.log(1.0 - k)))


# ===== 服药提醒最优时点 =====

def optimal_reminder_time(historical_times, default_hour=20.0):
    # 用循环均值处理跨午夜的情况。
    try:
        times = np.asarray(list(historical_times), dtype=float)
    except (TypeError, ValueError):
        _warn("历史服药时刻无法解析，使用默认提醒时点")
        return float(default_hour) % 24.0
    times = times[~np.isnan(times)]
    if times.size == 0:
        return float(default_hour) % 24.0
    angles = times / 24.0 * 2.0 * math.pi
    angle = math.atan2(float(np.sin(angles).mean()), float(np.cos(angles).mean()))
    if angle < 0:
        angle += 2.0 * math.pi
    return float((angle / (2.0 * math.pi) * 24.0) % 24.0)


def reminder_lead_minutes(missed_recent, base_lead=30.0, step=15.0, max_lead=120.0):
    n = validate_non_negative_int(missed_recent, default=0, name="近期漏服次数")
    return float(min(base_lead + n * step, max_lead))


# ===== 连续漏服 → 中断风险 =====

def protection_interruption_risk(consecutive_missed, forgiveness=3.0, steepness=1.2):
    days = validate_non_negative_int(consecutive_missed, default=0, name="连续漏服天数")
    fw = validate_positive_numeric(forgiveness, default=3.0, name="允许漏服窗口")
    s = validate_positive_numeric(steepness, default=1.2, name="陡峭度")
    x = float(np.clip((days - fw) * s, -700, 700))
    return float(1.0 / (1.0 + math.exp(-x)))


def cumulative_interruption_risk(dose_log, forgiveness=3.0, n_days=None):
    # 最长那一段连续漏服决定中断风险。
    return protection_interruption_risk(
        longest_consecutive_gap(dose_log, n_days=n_days),
        forgiveness=forgiveness,
    )


# ===== 依从性分层 =====

def adherence_tier(adherence_rate, high=0.85, mid=0.6):
    a = validate_probability(adherence_rate, default=0.0, name="依从率")
    h = validate_probability(high, default=0.85, name="高阈值")
    m = validate_probability(mid, default=0.6, name="中阈值")
    if m > h:
        _warn("中阈值大于高阈值，已回退默认阈值")
        h, m = 0.85, 0.6
    if a >= h:
        return "高", 2
    if a >= m:
        return "中", 1
    return "低", 0


def classify_log(dose_log, n_days=None, high=0.85, mid=0.6):
    rate = proportion_days_covered(dose_log, n_days=n_days)
    tier, level = adherence_tier(rate, high=high, mid=mid)
    return rate, tier, level


# ===== 滑动平滑 / 趋势 =====

def rolling_adherence(dose_log, window=7, n_days=None):
    log = validate_dose_log(dose_log, n_days=n_days)
    if log.size == 0:
        return np.zeros(0, dtype=float)
    w = max(1, validate_non_negative_int(window, default=7, name="窗口"))
    out = np.empty(log.size, dtype=float)
    for i in range(log.size):
        out[i] = log[max(0, i - w + 1): i + 1].mean()
    return out


def adherence_trend(dose_log, window=7, n_days=None):
    roll = rolling_adherence(dose_log, window=window, n_days=n_days)
    if roll.size < 2:
        return "平稳", 0.0
    delta = float(roll[-1] - roll[0])
    if delta > 0.05:
        return "上升", delta
    if delta < -0.05:
        return "下降", delta
    return "平稳", delta


# ===== 重启爬坡 =====

def reinitiation_ramp(days, daily_increment=0.3, k_elim=0.15, steady_max=1000.0):
    n = validate_non_negative_int(days, default=0, name="天数")
    if n == 0:
        return np.zeros(0, dtype=float)
    inc = validate_probability(daily_increment, default=0.3, name="日增比例")
    k = validate_positive_numeric(k_elim, default=0.15, name="消除速率")
    if k >= 1:
        k = 0.15
    smax = validate_positive_numeric(steady_max, default=1000.0, name="稳态上限")

    out = np.empty(n, dtype=float)
    conc = 0.0
    for i in range(n):
        conc = (conc + smax * inc) * (1.0 - k)
        out[i] = conc
    return out


def days_to_protection(days_horizon, threshold=700.0, daily_increment=0.3,
                       k_elim=0.15, steady_max=1000.0):
    ramp = reinitiation_ramp(days_horizon, daily_increment=daily_increment,
                             k_elim=k_elim, steady_max=steady_max)
    thr = validate_positive_numeric(threshold, default=700.0, name="阈值")
    hits = np.where(ramp >= thr)[0]
    return -1 if hits.size == 0 else int(hits[0] + 1)


# ===== 按需 vs 每日 =====

def on_demand_coverage(event_log, lead_doses=2, tail_doses=2):
    log = validate_dose_log(event_log)
    total = int(log.sum())
    if total == 0:
        return 0, 0, 0.0
    # 这里假定所有事件都被正确覆盖；与每日方案做结构性对比用
    validate_non_negative_int(lead_doses, default=2, name="前置剂量")
    validate_non_negative_int(tail_doses, default=2, name="事后剂量")
    return total, total, 1.0


def compare_daily_vs_on_demand(daily_adherence, sex_frequency_per_week,
                               on_demand_adherence=0.9):
    da = validate_probability(daily_adherence, default=0.0, name="每日依从率")
    oda = validate_probability(on_demand_adherence, default=0.9, name="按需依从率")
    freq = validate_non_negative_int(sex_frequency_per_week, default=0,
                                     name="每周性行为次数")

    daily_cov = steady_state_fraction(da)
    # 性行为越频繁，按需方案“漏掉负荷剂量”的风险越高
    on_demand_cov = float(np.clip(
        oda * (1.0 - 0.5 * freq / (freq + 4.0)), 0.0, 1.0
    ))
    recommend = "每日 PrEP" if daily_cov >= on_demand_cov else "按需 PrEP"
    return {
        "daily_coverage": float(daily_cov),
        "on_demand_coverage": on_demand_cov,
        "recommend": recommend,
        "sex_frequency_per_week": freq,
    }


# ===== 0-100 评分 =====

def adherence_score_0_100(dose_log, n_days=None, gap_penalty=6.0):
    log = validate_dose_log(dose_log, n_days=n_days)
    if log.size == 0:
        return 0

    pdc = float(log.sum() / log.size)
    missed = int(log.size - log.sum())
    gaps = count_gaps(log)
    # fragmentation = 1 表示每次漏服都独立(最碎)；越小越集中成块
    fragmentation = (gaps / missed) if missed > 0 else 0.0

    total = pdc * 80.0 + (1.0 - fragmentation) * 20.0 \
        - longest_consecutive_gap(log) * float(gap_penalty)
    return int(round(max(0.0, min(100.0, total))))


def score_to_grade(score):
    s = min(validate_non_negative_int(score, default=0, name="评分"), 100)
    if s >= 85:
        return "优秀", "依从性很好，继续保持当前服药习惯"
    if s >= 70:
        return "良好", "依从性较好，注意避免连续漏服"
    if s >= 50:
        return "一般", "存在明显漏服，建议设置服药提醒"
    return "较差", "依从性不足，保护可能中断，建议就医评估方案"


def summarize_adherence(dose_log, n_days=None):
    log = validate_dose_log(dose_log, n_days=n_days)
    rate = proportion_days_covered(log)
    tier, level = adherence_tier(rate)
    score = adherence_score_0_100(log)
    grade, advice = score_to_grade(score)
    return {
        "n_days": int(log.size),
        "adherence_rate": float(rate),
        "tier": tier,
        "tier_level": int(level),
        "score": int(score),
        "grade": grade,
        "advice": advice,
        "longest_gap": longest_consecutive_gap(log),
        "interruption_risk": cumulative_interruption_risk(log),
    }
