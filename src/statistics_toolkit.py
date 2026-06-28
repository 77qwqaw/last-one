# 统计工具：描述统计、CI、二项/泊松、RR/OR/NNT、诊断检验指标、KM 生存等。
# 非法/空输入一般返回 None 或默认值并 warnings.warn。
import math
import warnings

import numpy as np


# ---- 正态分布工具（基于 math.erf） ----
def normal_cdf(x, mu=0.0, sigma=1.0):
    """标准正态累计分布函数，用 math.erf 实现。sigma<=0 视为非法返回 nan。"""
    sigma = float(sigma)
    if sigma <= 0:
        warnings.warn("sigma 必须为正，返回 nan", UserWarning)
        return float("nan")
    z = (float(x) - float(mu)) / (sigma * math.sqrt(2.0))
    return 0.5 * (1.0 + math.erf(z))


def normal_pdf(x, mu=0.0, sigma=1.0):
    """正态分布概率密度函数。"""
    sigma = float(sigma)
    if sigma <= 0:
        warnings.warn("sigma 必须为正，返回 nan", UserWarning)
        return float("nan")
    z = (float(x) - float(mu)) / sigma
    return math.exp(-0.5 * z * z) / (sigma * math.sqrt(2.0 * math.pi))


def z_critical(confidence=0.95):
    # 给定双侧置信水平返回 z 临界值（用查表 + 线性插值近似逆正态）。 覆盖常用置信水平；其它用二分法逼近 normal_cdf 的反函数。
    confidence = float(confidence)
    if not (0 < confidence < 1):
        warnings.warn("confidence 必须在 (0,1)，已重置为 0.95", UserWarning)
        confidence = 0.95
    # 目标：找到 z 使 normal_cdf(z) = 1 - (1-confidence)/2
    target = 1.0 - (1.0 - confidence) / 2.0
    lo, hi = 0.0, 10.0
    for _ in range(100):
        mid = (lo + hi) / 2.0
        if normal_cdf(mid) < target:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2.0


# ---- 描述统计 ----
def _clean_array(data):
    """转 float 数组并去除 nan；空则返回空数组。"""
    arr = np.asarray(data, dtype=float).ravel()
    arr = arr[~np.isnan(arr)]
    return arr


def mean(data):
    """算术均值；空返回 None。"""
    arr = _clean_array(data)
    if arr.size == 0:
        warnings.warn("空数据，均值返回 None", UserWarning)
        return None
    return float(np.mean(arr))


def median(data):
    """中位数；空返回 None。"""
    arr = _clean_array(data)
    if arr.size == 0:
        warnings.warn("空数据，中位数返回 None", UserWarning)
        return None
    return float(np.median(arr))


def variance(data, ddof=1):
    """方差，默认样本方差 (ddof=1)。少于 ddof+1 个点返回 None。"""
    arr = _clean_array(data)
    if arr.size <= ddof:
        warnings.warn("数据点不足以计算方差，返回 None", UserWarning)
        return None
    return float(np.var(arr, ddof=ddof))


def std_dev(data, ddof=1):
    """标准差，默认样本标准差。"""
    v = variance(data, ddof=ddof)
    if v is None:
        return None
    return math.sqrt(v)


def quantile(data, q):
    """分位数，q 在 [0,1]。空数据或 q 越界返回 None。"""
    arr = _clean_array(data)
    if arr.size == 0:
        warnings.warn("空数据，分位数返回 None", UserWarning)
        return None
    q = float(q)
    if not (0 <= q <= 1):
        warnings.warn("q 必须在 [0,1]，分位数返回 None", UserWarning)
        return None
    return float(np.quantile(arr, q))


def iqr(data):
    """四分位距 IQR = Q3 - Q1。"""
    q1 = quantile(data, 0.25)
    q3 = quantile(data, 0.75)
    if q1 is None or q3 is None:
        return None
    return q3 - q1


def describe(data):
    # 返回描述统计 dict：n/mean/median/std/min/max/q1/q3/iqr。
    arr = _clean_array(data)
    if arr.size == 0:
        return {"n": 0}
    return {
        "n": int(arr.size),
        "mean": float(np.mean(arr)),
        "median": float(np.median(arr)),
        "std": std_dev(arr) if arr.size > 1 else 0.0,
        "min": float(np.min(arr)),
        "max": float(np.max(arr)),
        "q1": float(np.quantile(arr, 0.25)),
        "q3": float(np.quantile(arr, 0.75)),
        "iqr": float(np.quantile(arr, 0.75) - np.quantile(arr, 0.25)),
    }


# ---- 置信区间 ----
def mean_confidence_interval(data, confidence=0.95):
    # 均值的置信区间（大样本 z 近似）：mean ± z * s/sqrt(n)。
    arr = _clean_array(data)
    if arr.size < 2:
        warnings.warn("数据点不足，置信区间返回 None", UserWarning)
        return (None, None)
    m = float(np.mean(arr))
    s = float(np.std(arr, ddof=1))
    se = s / math.sqrt(arr.size)
    z = z_critical(confidence)
    return (m - z * se, m + z * se)


def proportion_confidence_interval(successes, n, confidence=0.95):
    """
    比例的 Wald 置信区间：p ± z * sqrt(p(1-p)/n)，结果裁剪到 [0,1]。
    n<=0 返回 (None, None)。
    """
    n = int(n)
    successes = int(successes)
    if n <= 0:
        warnings.warn("n 必须为正，置信区间返回 None", UserWarning)
        return (None, None)
    successes = min(max(successes, 0), n)
    p = successes / n
    z = z_critical(confidence)
    se = math.sqrt(p * (1 - p) / n)
    lower = max(0.0, p - z * se)
    upper = min(1.0, p + z * se)
    return (lower, upper)


# ---- 二项 / 泊松概率 ----
def binomial_pmf(k, n, p):
    """二项分布概率质量函数 P(X=k)。"""
    n = int(n)
    k = int(k)
    p = float(p)
    if not (0 <= p <= 1):
        warnings.warn("p 必须在 [0,1]，返回 nan", UserWarning)
        return float("nan")
    if k < 0 or k > n or n < 0:
        return 0.0
    return math.comb(n, k) * (p ** k) * ((1 - p) ** (n - k))


def binomial_cdf(k, n, p):
    """二项分布累计概率 P(X<=k)。"""
    k = int(k)
    if k < 0:
        return 0.0
    return sum(binomial_pmf(i, n, p) for i in range(0, min(k, int(n)) + 1))


def poisson_pmf(k, lam):
    """泊松分布概率质量函数 P(X=k)。"""
    k = int(k)
    lam = float(lam)
    if lam < 0:
        warnings.warn("lambda 不能为负，返回 nan", UserWarning)
        return float("nan")
    if k < 0:
        return 0.0
    return math.exp(-lam) * (lam ** k) / math.factorial(k)


def poisson_cdf(k, lam):
    """泊松分布累计概率 P(X<=k)。"""
    k = int(k)
    if k < 0:
        return 0.0
    return sum(poisson_pmf(i, lam) for i in range(0, k + 1))


# ---- 流行病学关联指标 ----
def relative_risk(a, b, c, d):
    """
    相对风险 RR = [a/(a+b)] / [c/(c+d)]。
    2x2 表：暴露组 a 病 b 不病；非暴露组 c 病 d 不病。
    分母为 0 时返回 None。
    """
    a, b, c, d = float(a), float(b), float(c), float(d)
    exposed_total = a + b
    unexposed_total = c + d
    if exposed_total == 0 or unexposed_total == 0:
        warnings.warn("分组人数为 0，RR 无定义，返回 None", UserWarning)
        return None
    risk_exposed = a / exposed_total
    risk_unexposed = c / unexposed_total
    if risk_unexposed == 0:
        warnings.warn("非暴露组风险为 0，RR 无定义，返回 inf", UserWarning)
        return float("inf")
    return risk_exposed / risk_unexposed


def odds_ratio(a, b, c, d):
    """
    比值比 OR = (a*d) / (b*c)。
    b 或 c 为 0 时返回 inf（提示无穷大关联）。
    """
    a, b, c, d = float(a), float(b), float(c), float(d)
    if b == 0 or c == 0:
        warnings.warn("b 或 c 为 0，OR 无定义，返回 inf", UserWarning)
        return float("inf")
    return (a * d) / (b * c)


def odds_ratio_ci(a, b, c, d, confidence=0.95):
    # OR 的对数尺度置信区间：
    a, b, c, d = float(a), float(b), float(c), float(d)
    if min(a, b, c, d) <= 0:
        warnings.warn("存在 0 格，OR 置信区间无定义，返回 None", UserWarning)
        return (None, None)
    or_val = (a * d) / (b * c)
    se_log = math.sqrt(1 / a + 1 / b + 1 / c + 1 / d)
    z = z_critical(confidence)
    log_or = math.log(or_val)
    return (math.exp(log_or - z * se_log), math.exp(log_or + z * se_log))


def number_needed_to_treat(risk_control, risk_treated):
    # 需治疗人数 NNT = 1 / |绝对风险下降 ARR|。
    rc = _validate_prob(risk_control, "risk_control")
    rt = _validate_prob(risk_treated, "risk_treated")
    arr = rc - rt
    if arr == 0:
        warnings.warn("绝对风险差为 0，NNT 无定义，返回 inf", UserWarning)
        return float("inf")
    return 1.0 / abs(arr)


def _validate_prob(p, name):
    p = float(p)
    if not (0 <= p <= 1):
        warnings.warn(f"{name} 必须在 [0,1]，已裁剪", UserWarning)
        p = min(max(p, 0.0), 1.0)
    return p


# ---- 诊断检验性能 ----
def diagnostic_metrics(tp, fp, fn, tn):
    # 由混淆矩阵计算诊断检验指标。
    tp, fp, fn, tn = float(tp), float(fp), float(fn), float(tn)
    total = tp + fp + fn + tn

    sens = tp / (tp + fn) if (tp + fn) > 0 else None
    spec = tn / (tn + fp) if (tn + fp) > 0 else None
    ppv = tp / (tp + fp) if (tp + fp) > 0 else None
    npv = tn / (tn + fn) if (tn + fn) > 0 else None
    accuracy = (tp + tn) / total if total > 0 else None
    prev = (tp + fn) / total if total > 0 else None

    lr_pos = None
    lr_neg = None
    if sens is not None and spec is not None:
        if spec < 1:
            lr_pos = sens / (1 - spec)
        else:
            lr_pos = float("inf")
        if spec > 0:
            lr_neg = (1 - sens) / spec

    return {
        "sensitivity": sens,
        "specificity": spec,
        "ppv": ppv,
        "npv": npv,
        "accuracy": accuracy,
        "lr_positive": lr_pos,
        "lr_negative": lr_neg,
        "prevalence": prev,
    }


# ---- 简单线性回归与相关 ----
def pearson_correlation(x, y):
    """皮尔逊相关系数 r。长度不一致或不足 2 点返回 None。"""
    x = np.asarray(x, dtype=float).ravel()
    y = np.asarray(y, dtype=float).ravel()
    if x.size != y.size:
        warnings.warn("x 与 y 长度不一致，返回 None", UserWarning)
        return None
    if x.size < 2:
        warnings.warn("数据点不足，相关系数返回 None", UserWarning)
        return None
    sx = np.std(x)
    sy = np.std(y)
    if sx == 0 or sy == 0:
        warnings.warn("某变量无变异，相关系数无定义，返回 None", UserWarning)
        return None
    return float(np.corrcoef(x, y)[0, 1])


def linear_regression(x, y):
    """
    最小二乘简单线性回归 y = slope * x + intercept。
    返回 dict：slope / intercept / r / r_squared。
    数据不足返回各项 None。
    """
    x = np.asarray(x, dtype=float).ravel()
    y = np.asarray(y, dtype=float).ravel()
    if x.size != y.size or x.size < 2:
        warnings.warn("数据不足或长度不一致，回归返回 None", UserWarning)
        return {"slope": None, "intercept": None, "r": None, "r_squared": None}
    xmean = np.mean(x)
    ymean = np.mean(y)
    sxx = np.sum((x - xmean) ** 2)
    if sxx == 0:
        warnings.warn("x 无变异，斜率无定义，返回 None", UserWarning)
        return {"slope": None, "intercept": None, "r": None, "r_squared": None}
    sxy = np.sum((x - xmean) * (y - ymean))
    slope = sxy / sxx
    intercept = ymean - slope * xmean
    r = pearson_correlation(x, y)
    return {
        "slope": float(slope),
        "intercept": float(intercept),
        "r": r,
        "r_squared": (r ** 2) if r is not None else None,
    }


# ---- 假设检验统计量 ----
def z_test_two_proportions(x1, n1, x2, n2):
    """
    两比例 z 检验统计量（合并比例方差）。
    返回 dict：z 统计量与双侧 p 值。
    样本量非正返回 None。
    """
    n1, n2 = int(n1), int(n2)
    if n1 <= 0 or n2 <= 0:
        warnings.warn("样本量必须为正，返回 None", UserWarning)
        return {"z": None, "p_value": None}
    p1 = x1 / n1
    p2 = x2 / n2
    p_pool = (x1 + x2) / (n1 + n2)
    se = math.sqrt(p_pool * (1 - p_pool) * (1 / n1 + 1 / n2))
    if se == 0:
        return {"z": 0.0, "p_value": 1.0}
    z = (p1 - p2) / se
    p_value = 2.0 * (1.0 - normal_cdf(abs(z)))
    return {"z": z, "p_value": p_value}


def chi_square_statistic(observed):
    """
    列联表卡方统计量（Pearson），observed 为二维计数表。
    返回 dict：chi2 统计量与自由度 df。
    任一边际为 0 时跳过相应期望（返回 None）。
    """
    obs = np.asarray(observed, dtype=float)
    if obs.ndim != 2:
        raise ValueError("observed 必须为二维列联表")
    total = obs.sum()
    if total == 0:
        warnings.warn("列联表总和为 0，卡方无定义，返回 None", UserWarning)
        return {"chi2": None, "df": None}
    row_sums = obs.sum(axis=1, keepdims=True)
    col_sums = obs.sum(axis=0, keepdims=True)
    expected = row_sums @ col_sums / total
    with np.errstate(divide="ignore", invalid="ignore"):
        terms = np.where(expected > 0, (obs - expected) ** 2 / expected, 0.0)
    chi2 = float(np.sum(terms))
    df = (obs.shape[0] - 1) * (obs.shape[1] - 1)
    return {"chi2": chi2, "df": df}


# ---- Kaplan-Meier 生存分析（简化） ----
def kaplan_meier(times, events):
    """
    简化 Kaplan-Meier 生存概率估计。

    times  : 每个个体的观察时间
    events  : 1 = 发生事件（死亡/感染），0 = 删失

    返回 dict：unique_times（事件时间点）、survival（对应生存概率 S(t)）。
    在每个事件时间 t：S(t) = S(t-) * (1 - d_t / n_t)，
    n_t 为风险集人数，d_t 为该时刻事件数。空输入返回空结果。
    """
    times = np.asarray(times, dtype=float).ravel()
    events = np.asarray(events, dtype=float).ravel()
    if times.size == 0 or times.size != events.size:
        warnings.warn("times/events 为空或长度不一致，返回空结果", UserWarning)
        return {"times": np.array([]), "survival": np.array([])}

    order = np.argsort(times)
    times = times[order]
    events = events[order]

    unique_event_times = np.unique(times[events == 1])
    survival = []
    s = 1.0
    n_total = times.size
    for t in unique_event_times:
        at_risk = np.sum(times >= t)
        deaths = np.sum((times == t) & (events == 1))
        if at_risk > 0:
            s *= (1.0 - deaths / at_risk)
        survival.append(s)
    return {"times": unique_event_times, "survival": np.array(survival)}


# ---- Bootstrap 重采样 ----
def bootstrap_mean(data, n_iterations=1000, confidence=0.95, seed=None):
    # 对均值做 bootstrap 重采样，返回 dict：
    arr = _clean_array(data)
    if arr.size == 0:
        warnings.warn("空数据，bootstrap 返回 None", UserWarning)
        return None
    rng = np.random.default_rng(seed)
    n_iterations = max(int(n_iterations), 1)
    means = np.empty(n_iterations)
    for i in range(n_iterations):
        sample = rng.choice(arr, size=arr.size, replace=True)
        means[i] = np.mean(sample)
    alpha = 1.0 - float(confidence)
    lower = float(np.quantile(means, alpha / 2.0))
    upper = float(np.quantile(means, 1.0 - alpha / 2.0))
    return {
        "estimate": float(np.mean(arr)),
        "ci_lower": lower,
        "ci_upper": upper,
        "bootstrap_means": means,
    }
