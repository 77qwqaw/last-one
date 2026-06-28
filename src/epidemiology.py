# HIV 流行病学：SEIR/SEIRS/SIS、接触矩阵、R0/Rt、PrEP 干预、90-90-90 级联等。
# 逐日迭代沿用 pharmacokinetic_models.sir_simulation 的约定：
# days<=0 返回空数组；用显式欧拉步进并按需归一化以保人口守恒。
import math
import warnings

import numpy as np


# ---- 通用工具 ----
def _validate_days(days):
    # 校验天数，返回整数天数；<=0 视为非法，由调用方处理空数组返回。
    try:
        d = int(days)
    except (ValueError, TypeError):
        warnings.warn("days 必须为整数，已重置为 0", UserWarning)
        return 0
    return d


def _validate_positive(value, default, name):
    # 校验严格正数参数，非法返回默认值并警告。
    try:
        v = float(value)
    except (ValueError, TypeError):
        warnings.warn(f"{name} 必须为数字，使用默认值 {default}", UserWarning)
        return float(default)
    if v <= 0:
        warnings.warn(f"{name} 必须为正数，使用默认值 {default}", UserWarning)
        return float(default)
    return v


def _validate_rate(value, default, name):
    # 校验 0~1 之间的速率/比例参数，越界裁剪并警告。
    try:
        v = float(value)
    except (ValueError, TypeError):
        warnings.warn(f"{name} 必须为数字，使用默认值 {default}", UserWarning)
        return float(default)
    if v < 0:
        warnings.warn(f"{name} 不能为负，已裁剪为 0", UserWarning)
        return 0.0
    if v > 1:
        warnings.warn(f"{name} 不能超过 1，已裁剪为 1", UserWarning)
        return 1.0
    return v


# ---- SEIR 模型（含潜伏期 E） ----
def seir_simulation(beta, sigma, gamma, N, I0, days, E0=0.0):
    """
    SEIR 模型：易感 S -> 潜伏 E -> 感染 I -> 康复/移除 R。

    参数：
      beta  : 有效接触传播率（每日）
      sigma : 潜伏->感染转化率（1/潜伏期）
      gamma : 感染->康复率（1/传染期）
      N     : 总人口
      I0    : 初始感染人数
      days  : 模拟天数
      E0    : 初始潜伏人数

    返回 (S, I, ...) 元组 (S, E, I, R)，每步归一化保证 S+E+I+R = N。
    days <= 0 返回四个空数组。
    """
    days = _validate_days(days)
    if days <= 0:
        empty = np.array([])
        return empty, empty.copy(), empty.copy(), empty.copy()

    N = _validate_positive(N, 1.0, "N")
    beta = max(float(beta), 0.0)
    sigma = max(float(sigma), 0.0)
    gamma = max(float(gamma), 0.0)

    S = np.zeros(days)
    E = np.zeros(days)
    I = np.zeros(days)
    R = np.zeros(days)

    I0 = min(max(float(I0), 0.0), N)
    E0 = min(max(float(E0), 0.0), N - I0)
    S[0] = N - I0 - E0
    E[0] = E0
    I[0] = I0
    R[0] = 0.0

    for t in range(days - 1):
        new_exposed = beta * S[t] * I[t] / N
        new_infectious = sigma * E[t]
        new_recoveries = gamma * I[t]

        S[t + 1] = S[t] - new_exposed
        E[t + 1] = E[t] + new_exposed - new_infectious
        I[t + 1] = I[t] + new_infectious - new_recoveries
        R[t + 1] = R[t] + new_recoveries

        # 防止数值漂移产生负值
        S[t + 1] = max(S[t + 1], 0.0)
        E[t + 1] = max(E[t + 1], 0.0)
        I[t + 1] = max(I[t + 1], 0.0)
        R[t + 1] = max(R[t + 1], 0.0)

        total = S[t + 1] + E[t + 1] + I[t + 1] + R[t + 1]
        if total > 0:
            factor = N / total
            S[t + 1] *= factor
            E[t + 1] *= factor
            I[t + 1] *= factor
            R[t + 1] *= factor

    return S, E, I, R


# ---- SEIRS 模型（康复后免疫消退回到易感） ----
def seirs_simulation(beta, sigma, gamma, xi, N, I0, days, E0=0.0):
    # SEIRS 模型：在 SEIR 基础上增加 R -> S 的免疫消退率 xi。
    days = _validate_days(days)
    if days <= 0:
        empty = np.array([])
        return empty, empty.copy(), empty.copy(), empty.copy()

    N = _validate_positive(N, 1.0, "N")
    beta = max(float(beta), 0.0)
    sigma = max(float(sigma), 0.0)
    gamma = max(float(gamma), 0.0)
    xi = max(float(xi), 0.0)

    S = np.zeros(days)
    E = np.zeros(days)
    I = np.zeros(days)
    R = np.zeros(days)

    I0 = min(max(float(I0), 0.0), N)
    E0 = min(max(float(E0), 0.0), N - I0)
    S[0] = N - I0 - E0
    E[0] = E0
    I[0] = I0
    R[0] = 0.0

    for t in range(days - 1):
        new_exposed = beta * S[t] * I[t] / N
        new_infectious = sigma * E[t]
        new_recoveries = gamma * I[t]
        new_susceptible = xi * R[t]

        S[t + 1] = S[t] - new_exposed + new_susceptible
        E[t + 1] = E[t] + new_exposed - new_infectious
        I[t + 1] = I[t] + new_infectious - new_recoveries
        R[t + 1] = R[t] + new_recoveries - new_susceptible

        S[t + 1] = max(S[t + 1], 0.0)
        E[t + 1] = max(E[t + 1], 0.0)
        I[t + 1] = max(I[t + 1], 0.0)
        R[t + 1] = max(R[t + 1], 0.0)

        total = S[t + 1] + E[t + 1] + I[t + 1] + R[t + 1]
        if total > 0:
            factor = N / total
            S[t + 1] *= factor
            E[t + 1] *= factor
            I[t + 1] *= factor
            R[t + 1] *= factor

    return S, E, I, R


# ---- SIS 模型（无免疫，康复后回到易感） ----
def sis_simulation(beta, gamma, N, I0, days):
    # SIS 模型：感染后不获得免疫，康复直接回到易感池。
    days = _validate_days(days)
    if days <= 0:
        return np.array([]), np.array([])

    N = _validate_positive(N, 1.0, "N")
    beta = max(float(beta), 0.0)
    gamma = max(float(gamma), 0.0)

    S = np.zeros(days)
    I = np.zeros(days)
    I0 = min(max(float(I0), 0.0), N)
    S[0] = N - I0
    I[0] = I0

    for t in range(days - 1):
        new_infections = beta * S[t] * I[t] / N
        new_recoveries = gamma * I[t]

        S[t + 1] = S[t] - new_infections + new_recoveries
        I[t + 1] = I[t] + new_infections - new_recoveries

        S[t + 1] = max(S[t + 1], 0.0)
        I[t + 1] = max(I[t + 1], 0.0)

        total = S[t + 1] + I[t + 1]
        if total > 0:
            factor = N / total
            S[t + 1] *= factor
            I[t + 1] *= factor

    return S, I


def sis_endemic_equilibrium(beta, gamma, N):
    """
    SIS 模型地方性平衡感染人数 I*。
    若 R0 = beta/gamma <= 1，疾病消亡，返回 0。
    否则 I* = N (1 - gamma/beta)。
    """
    N = _validate_positive(N, 1.0, "N")
    beta = max(float(beta), 0.0)
    gamma = max(float(gamma), 0.0)
    if beta <= gamma or beta == 0:
        return 0.0
    return N * (1.0 - gamma / beta)


# ---- 基本再生数 R0 与有效再生数 Rt ----
def basic_reproduction_number(beta, gamma):
    # 简单 SIR/SIS 模型基本再生数 R0 = beta / gamma。
    beta = max(float(beta), 0.0)
    gamma = float(gamma)
    if gamma <= 0:
        warnings.warn("gamma 必须为正数，R0 无定义，返回 inf", UserWarning)
        return float("inf")
    return beta / gamma


def effective_reproduction_number(R0, susceptible_fraction):
    """
    有效再生数 Rt = R0 * (S / N)。
    susceptible_fraction 为当前易感人群占比 (0~1)。
    """
    R0 = max(float(R0), 0.0)
    frac = _validate_rate(susceptible_fraction, 1.0, "susceptible_fraction")
    return R0 * frac


def reproduction_number_from_series(incidence, generation_time):
    # 由每日新增感染序列估计有效再生数 Rt（简化版）。 用相隔 generation_time 天的增量比近似：Rt[t] ≈ I[t] / I[t - g]。…
    incidence = np.asarray(incidence, dtype=float)
    g = int(generation_time)
    if g <= 0:
        warnings.warn("generation_time 必须为正整数，已重置为 1", UserWarning)
        g = 1
    n = len(incidence)
    rt = np.full(n, np.nan)
    for t in range(g, n):
        prev = incidence[t - g]
        if prev > 0:
            rt[t] = incidence[t] / prev
    return rt


# ---- 群体免疫阈值与覆盖率干预 ----
def herd_immunity_threshold(R0):
    """
    群体免疫阈值 HIT = 1 - 1/R0。
    R0 <= 1 时无需群体免疫，返回 0。
    """
    R0 = float(R0)
    if R0 <= 1:
        return 0.0
    return 1.0 - 1.0 / R0


def critical_vaccination_coverage(R0, vaccine_efficacy):
    """
    达到群体免疫所需的最小接种覆盖率 Vc = (1 - 1/R0) / efficacy。
    若疫苗效力不足以达到群体免疫，返回 >1（提示无法仅靠接种实现）。
    """
    R0 = float(R0)
    eff = _validate_rate(vaccine_efficacy, 1.0, "vaccine_efficacy")
    hit = herd_immunity_threshold(R0)
    if eff <= 0:
        warnings.warn("vaccine_efficacy 为 0，无法通过接种实现群体免疫", UserWarning)
        return float("inf")
    return hit / eff


def intervention_sir_simulation(beta, gamma, N, I0, days,
                                 coverage=0.0, efficacy=1.0):
    """
    带预防覆盖率（疫苗 / PrEP）干预的 SIR 模拟。
    覆盖且有效保护的人群在初始即移入 R（视为不可感染）。
    有效保护比例 = coverage * efficacy。

    返回 (S, I, R)，每步归一化保证总人数守恒。
    days <= 0 返回三个空数组。
    """
    days = _validate_days(days)
    if days <= 0:
        empty = np.array([])
        return empty, empty.copy(), empty.copy()

    N = _validate_positive(N, 1.0, "N")
    beta = max(float(beta), 0.0)
    gamma = max(float(gamma), 0.0)
    coverage = _validate_rate(coverage, 0.0, "coverage")
    efficacy = _validate_rate(efficacy, 1.0, "efficacy")

    protected = N * coverage * efficacy

    S = np.zeros(days)
    I = np.zeros(days)
    R = np.zeros(days)
    I0 = min(max(float(I0), 0.0), N)
    protected = min(protected, N - I0)
    S[0] = N - I0 - protected
    I[0] = I0
    R[0] = protected

    for t in range(days - 1):
        new_infections = beta * S[t] * I[t] / N
        new_recoveries = gamma * I[t]

        S[t + 1] = max(S[t] - new_infections, 0.0)
        I[t + 1] = max(I[t] + new_infections - new_recoveries, 0.0)
        R[t + 1] = max(R[t] + new_recoveries, 0.0)

        total = S[t + 1] + I[t + 1] + R[t + 1]
        if total > 0:
            factor = N / total
            S[t + 1] *= factor
            I[t + 1] *= factor
            R[t + 1] *= factor

    return S, I, R


# ---- 分组接触矩阵传播（年龄 / 风险组） ----
def next_generation_R0(contact_matrix, transmissibility, infectious_period):
    # 由接触矩阵通过下一代矩阵法计算 R0。
    C = np.asarray(contact_matrix, dtype=float)
    if C.ndim != 2 or C.shape[0] != C.shape[1]:
        raise ValueError("contact_matrix 必须为方阵")
    p = max(float(transmissibility), 0.0)
    d = max(float(infectious_period), 0.0)
    K = p * d * C
    eigvals = np.linalg.eigvals(K)
    return float(np.max(np.abs(eigvals)))


def grouped_sir_simulation(contact_matrix, transmissibility, gamma,
                           N_groups, I0_groups, days):
    """
    分组 SIR 模型，组间通过接触矩阵耦合传播。

    contact_matrix[i][j]：组 i 接触组 j 的接触率。
    各组内部新感染 = transmissibility * S_i * sum_j C[i][j] * I_j / N_j。

    返回 (S, I, R)，每个均为 shape (days, n_groups) 的数组。
    days <= 0 返回三个空数组。每步对各组分别归一化保证组内人数守恒。
    """
    days = _validate_days(days)
    n = len(N_groups)
    if days <= 0:
        empty = np.zeros((0, n))
        return empty, empty.copy(), empty.copy()

    C = np.asarray(contact_matrix, dtype=float)
    N = np.asarray(N_groups, dtype=float)
    I0 = np.asarray(I0_groups, dtype=float)
    p = max(float(transmissibility), 0.0)
    gamma = max(float(gamma), 0.0)

    S = np.zeros((days, n))
    I = np.zeros((days, n))
    R = np.zeros((days, n))
    S[0] = N - I0
    I[0] = I0

    safeN = np.where(N > 0, N, 1.0)
    for t in range(days - 1):
        # 各组感染力：来自所有组感染者的加权贡献
        force = p * np.array([
            np.sum(C[i] * I[t] / safeN) for i in range(n)
        ])
        new_inf = S[t] * force
        new_rec = gamma * I[t]

        S[t + 1] = np.maximum(S[t] - new_inf, 0.0)
        I[t + 1] = np.maximum(I[t] + new_inf - new_rec, 0.0)
        R[t + 1] = np.maximum(R[t] + new_rec, 0.0)

        total = S[t + 1] + I[t + 1] + R[t + 1]
        for i in range(n):
            if total[i] > 0:
                f = N[i] / total[i]
                S[t + 1, i] *= f
                I[t + 1, i] *= f
                R[t + 1, i] *= f

    return S, I, R


# ---- HIV 90-90-90 级联模型 ----
def hiv_care_cascade(total_infected, prop_diagnosed,
                     prop_on_treatment, prop_suppressed):
    """
    HIV 90-90-90 级联模型。

    UNAIDS 目标：90% 被诊断，诊断者 90% 接受治疗，治疗者 90% 病毒抑制。
    各比例为相对上一阶段的条件比例 (0~1)。

    返回 dict，含各阶段人数与相对总感染者的总体抑制比例。
    """
    total = max(float(total_infected), 0.0)
    p_dx = _validate_rate(prop_diagnosed, 0.9, "prop_diagnosed")
    p_tx = _validate_rate(prop_on_treatment, 0.9, "prop_on_treatment")
    p_vs = _validate_rate(prop_suppressed, 0.9, "prop_suppressed")

    diagnosed = total * p_dx
    on_treatment = diagnosed * p_tx
    suppressed = on_treatment * p_vs

    overall_suppression = (suppressed / total) if total > 0 else 0.0

    return {
        "total_infected": total,
        "diagnosed": diagnosed,
        "on_treatment": on_treatment,
        "virally_suppressed": suppressed,
        "undiagnosed": total - diagnosed,
        "diagnosed_untreated": diagnosed - on_treatment,
        "treated_unsuppressed": on_treatment - suppressed,
        "overall_suppression_rate": overall_suppression,
    }


def cascade_gap_to_target(total_infected, current_suppressed, target_rate=0.729):
    # 计算距离级联目标抑制人数的差距。 默认目标 0.729 = 0.9^3（90-90-90 的总体抑制率）。 返回还需新增达到病毒抑制的人数（>=0）。
    total = max(float(total_infected), 0.0)
    current = max(float(current_suppressed), 0.0)
    target_rate = _validate_rate(target_rate, 0.729, "target_rate")
    target_count = total * target_rate
    return max(target_count, current) - current


# ---- 增量感染估计与接触追踪 ----
def incident_infections(prevalence_start, prevalence_end, population,
                        diagnoses_observed=None):
    # 由两个时点的现患人数估计期间增量（新发）感染数（简化）。 增量 = (期末现患 - 期初现患) 占人群的增加； 若提供 diagnoses_observed…
    p0 = max(float(prevalence_start), 0.0)
    p1 = max(float(prevalence_end), 0.0)
    population = _validate_positive(population, 1.0, "population")
    net_increase = p1 - p0
    if diagnoses_observed is None:
        return max(net_increase, 0.0)
    obs = max(float(diagnoses_observed), 0.0)
    # 新发感染至少等于现患净增长，也不少于期间实际诊断数
    return max(max(net_increase, 0.0), obs)


def contact_tracing_yield(index_cases, contacts_per_case,
                          trace_completeness, positivity_rate):
    # 接触追踪产出模型：预计可发现的阳性接触者人数。
    index_cases = max(float(index_cases), 0.0)
    cpc = max(float(contacts_per_case), 0.0)
    completeness = _validate_rate(trace_completeness, 1.0, "trace_completeness")
    positivity = _validate_rate(positivity_rate, 0.0, "positivity_rate")

    total_contacts = index_cases * cpc
    traced = total_contacts * completeness
    positives = traced * positivity
    return {
        "total_contacts": total_contacts,
        "traced_and_tested": traced,
        "expected_positives": positives,
    }


# ---- 增长指标：倍增时间 / 增长率 ----
def exponential_growth_rate(value_start, value_end, days):
    # 由两时点的数值估计指数增长率 r：value_end = value_start * exp(r * days)。 返回每日增长率 r。非法输入返回 0。
    days = float(days)
    v0 = float(value_start)
    v1 = float(value_end)
    if days <= 0 or v0 <= 0 or v1 <= 0:
        warnings.warn("增长率估计需要正的时间与数值，返回 0", UserWarning)
        return 0.0
    return math.log(v1 / v0) / days


def doubling_time(growth_rate):
    """
    指数增长期倍增时间 Td = ln(2) / r。
    r <= 0 表示无增长或衰减，返回 inf。
    """
    r = float(growth_rate)
    if r <= 0:
        return float("inf")
    return math.log(2.0) / r


def doubling_time_from_series(value_start, value_end, days):
    # 由两时点直接估计倍增时间（先估增长率再换算）。
    r = exponential_growth_rate(value_start, value_end, days)
    return doubling_time(r)


# ---- 流行曲线分析：峰值与拐点 ----
def epidemic_peak(infectious_series):
    # 返回流行曲线峰值的 (峰值日索引, 峰值人数)。 空序列返回 (None, 0.0)。
    series = np.asarray(infectious_series, dtype=float)
    if series.size == 0:
        return None, 0.0
    idx = int(np.argmax(series))
    return idx, float(series[idx])


def epidemic_final_size(R0, tol=1e-10, max_iter=1000):
    # SIR 最终流行规模方程的数值解：
    R0 = float(R0)
    if R0 <= 1:
        return 0.0
    z = 0.5
    for _ in range(max_iter):
        z_new = 1.0 - math.exp(-R0 * z)
        if abs(z_new - z) < tol:
            return z_new
        z = z_new
    return z


def inflection_points(series):
    """
    检测序列的拐点（二阶差分变号处）索引列表。
    用于定位流行曲线由加速转为减速的时间点。
    序列过短（<3）返回空列表。
    """
    series = np.asarray(series, dtype=float)
    if series.size < 3:
        return []
    second_diff = np.diff(series, n=2)
    points = []
    for i in range(1, len(second_diff)):
        if second_diff[i - 1] == 0:
            continue
        if second_diff[i] == 0:
            continue
        if (second_diff[i - 1] > 0) != (second_diff[i] > 0):
            # 拐点位于原序列索引 i+1 附近
            points.append(i + 1)
    return points


def attack_rate(total_infected, population_at_risk):
    """
    累计罹患率 = 累计感染数 / 风险人群。结果裁剪到 [0, 1]。
    """
    total = max(float(total_infected), 0.0)
    pop = _validate_positive(population_at_risk, 1.0, "population_at_risk")
    return min(total / pop, 1.0)


def prevalence(current_cases, population):
    """现患率 = 现存病例 / 总人口，裁剪到 [0, 1]。"""
    cases = max(float(current_cases), 0.0)
    pop = _validate_positive(population, 1.0, "population")
    return min(cases / pop, 1.0)


def incidence_rate(new_cases, person_time):
    """发病密度 = 新发病例 / 人时。person_time <= 0 返回 0。"""
    new_cases = max(float(new_cases), 0.0)
    pt = float(person_time)
    if pt <= 0:
        warnings.warn("person_time 必须为正，返回 0", UserWarning)
        return 0.0
    return new_cases / pt
