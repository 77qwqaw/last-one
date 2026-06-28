# HIV 预防卫生经济学：贴现/QALY/ICER、Markov 队列模型、敏感性分析、预算影响。
# 非法输入按项目约定：返回保守默认值并 warnings.warn。
import warnings

import numpy as np


# ---- 默认成本 / 效用参数（人民币，年度，示意值） ----
DEFAULT_WTP_PER_QALY = 240000.0   # 支付意愿阈值（约 3 倍人均 GDP，示意）

# 各 HIV 状态的年度效用值（QALY 权重，0-1）
STATE_UTILITY = {
    "uninfected": 1.0,
    "hiv_undiagnosed": 0.85,
    "hiv_on_art": 0.92,
    "hiv_aids": 0.6,
    "death": 0.0,
}

MARKOV_STATES = ["uninfected", "hiv_undiagnosed", "hiv_on_art", "hiv_aids", "death"]


# ---- 输入校验 ----
def validate_rate(value, name="比率", default=0.0):
    try:
        v = float(value)
    except (ValueError, TypeError):
        warnings.warn(f"{name} 输入非法，已重置为 {default}", UserWarning)
        return default
    if not (0.0 <= v <= 1.0):
        warnings.warn(f"{name} 必须在 0-1 之间，已重置为 {default}", UserWarning)
        return default
    return v


def validate_positive(value, name="数值", default=0.0):
    try:
        v = float(value)
    except (ValueError, TypeError):
        warnings.warn(f"{name} 输入非法，已重置为 {default}", UserWarning)
        return default
    if v < 0:
        warnings.warn(f"{name} 不能为负，已重置为 {default}", UserWarning)
        return default
    return v


# ---- 贴现 ----
def discount_factor(year, discount_rate=0.03):
    """单期贴现因子 1/(1+r)^t。"""
    r = validate_rate(discount_rate, "discount_rate", 0.03)
    try:
        t = float(year)
    except (ValueError, TypeError):
        warnings.warn("year 非法，已重置为 0", UserWarning)
        t = 0.0
    return 1.0 / ((1.0 + r) ** t)


def discount_stream(values, discount_rate=0.03):
    # 对逐年流（list/array，下标即年份 0,1,2...）做贴现求和。 返回 {undiscounted, discounted, factors}。
    arr = np.asarray(values, dtype=float)
    r = validate_rate(discount_rate, "discount_rate", 0.03)
    years = np.arange(len(arr))
    factors = 1.0 / ((1.0 + r) ** years)
    discounted = arr * factors
    return {
        "undiscounted": float(np.sum(arr)),
        "discounted": float(np.sum(discounted)),
        "factors": factors,
        "discounted_stream": discounted,
    }


# ---- QALY ----
def compute_qaly(utility, years, discount_rate=0.0):
    """
    单一健康状态下的 QALY = 效用 * 年数（可贴现）。
    若 discount_rate>0，则按逐年贴现累加。
    """
    u = validate_rate(utility, "utility", 0.0)
    n = validate_positive(years, "years", 0.0)
    r = validate_rate(discount_rate, "discount_rate", 0.0)
    if r <= 0:
        return float(u * n)
    # 逐年贴现：整数年 + 残余年
    total = 0.0
    full = int(n)
    for t in range(full):
        total += u * (1.0 / ((1.0 + r) ** t))
    frac = n - full
    if frac > 0:
        total += u * frac * (1.0 / ((1.0 + r) ** full))
    return float(total)


def qaly_from_state_path(state_path, years_per_cycle=1.0, discount_rate=0.0):
    # 给定逐周期所处状态序列，累加 QALY。 state_path: list[str]，每个元素须为 STATE_UTILITY 的键。
    r = validate_rate(discount_rate, "discount_rate", 0.0)
    ypc = validate_positive(years_per_cycle, "years_per_cycle", 1.0)
    total = 0.0
    for t, state in enumerate(state_path):
        u = STATE_UTILITY.get(state)
        if u is None:
            warnings.warn(f"未知状态 {state}，按效用 0 处理", UserWarning)
            u = 0.0
        factor = 1.0 / ((1.0 + r) ** t) if r > 0 else 1.0
        total += u * ypc * factor
    return float(total)


# ---- 成本汇总 ----
def summarize_costs(drug_cost=0.0, testing_cost=0.0, followup_cost=0.0, other_cost=0.0):
    """汇总单人年度成本，返回 dict（含分项与合计）。"""
    drug = validate_positive(drug_cost, "drug_cost", 0.0)
    testing = validate_positive(testing_cost, "testing_cost", 0.0)
    followup = validate_positive(followup_cost, "followup_cost", 0.0)
    other = validate_positive(other_cost, "other_cost", 0.0)
    total = drug + testing + followup + other
    return {
        "drug": drug,
        "testing": testing,
        "followup": followup,
        "other": other,
        "total": total,
    }


def program_cost(cost_per_person, n_people, years=1.0, discount_rate=0.0):
    """项目总成本 = 人均成本 * 人数 * 年数（可贴现）。"""
    cpp = validate_positive(cost_per_person, "cost_per_person", 0.0)
    n = validate_positive(n_people, "n_people", 0.0)
    yrs = validate_positive(years, "years", 1.0)
    r = validate_rate(discount_rate, "discount_rate", 0.0)
    if r <= 0:
        return float(cpp * n * yrs)
    annual = cpp * n
    total = 0.0
    full = int(yrs)
    for t in range(full):
        total += annual * (1.0 / ((1.0 + r) ** t))
    frac = yrs - full
    if frac > 0:
        total += annual * frac * (1.0 / ((1.0 + r) ** full))
    return float(total)


# ---- 避免感染数 / 每避免一例成本 ----
def infections_averted(baseline_incidence, effectiveness, n_people, years=1.0):
    """
    估计干预避免的感染数。

    baseline_incidence: 无干预的年发病率（0-1）
    effectiveness: 干预相对降低风险的比例（0-1）
    n_people, years: 队列规模与年数
    返回 dict: baseline_cases / intervention_cases / averted
    """
    inc = validate_rate(baseline_incidence, "baseline_incidence", 0.0)
    eff = validate_rate(effectiveness, "effectiveness", 0.0)
    n = validate_positive(n_people, "n_people", 0.0)
    yrs = validate_positive(years, "years", 1.0)

    person_years = n * yrs
    baseline_cases = inc * person_years
    intervention_cases = inc * (1.0 - eff) * person_years
    averted = baseline_cases - intervention_cases
    return {
        "baseline_cases": float(baseline_cases),
        "intervention_cases": float(intervention_cases),
        "averted": float(averted),
        "person_years": float(person_years),
    }


def cost_per_infection_averted(total_cost, averted):
    """每避免一例感染的成本；averted<=0 时返回 inf。"""
    cost = validate_positive(total_cost, "total_cost", 0.0)
    if averted is None:
        averted = 0.0
    try:
        a = float(averted)
    except (ValueError, TypeError):
        warnings.warn("averted 非法，已重置为 0", UserWarning)
        a = 0.0
    if a <= 0:
        return float("inf")
    return float(cost / a)


# ---- ICER / WTP ----
def compute_icer(cost_a, qaly_a, cost_b, qaly_b):
    """
    增量成本效果比 ICER = (成本A - 成本B) / (效果A - 效果B)。
    约定 A 为新干预，B 为对照。
    返回 dict: incremental_cost / incremental_qaly / icer / dominant 状态。
    """
    ca = validate_positive(cost_a, "cost_a", 0.0)
    cb = validate_positive(cost_b, "cost_b", 0.0)
    try:
        qa = float(qaly_a)
        qb = float(qaly_b)
    except (ValueError, TypeError):
        warnings.warn("QALY 输入非法，已重置为 0", UserWarning)
        qa = qb = 0.0

    inc_cost = ca - cb
    inc_qaly = qa - qb

    if inc_qaly == 0:
        if inc_cost <= 0:
            status = "dominant"  # 效果相同、成本更低
        else:
            status = "dominated"  # 效果相同、成本更高
        icer = float("inf") if inc_cost > 0 else float("-inf")
    else:
        icer = inc_cost / inc_qaly
        if inc_cost < 0 and inc_qaly > 0:
            status = "dominant"      # 更便宜又更有效
        elif inc_cost > 0 and inc_qaly < 0:
            status = "dominated"     # 更贵又更差
        else:
            status = "trade_off"     # 需与 WTP 比较
    return {
        "incremental_cost": float(inc_cost),
        "incremental_qaly": float(inc_qaly),
        "icer": float(icer),
        "status": status,
    }


def is_cost_effective(icer, wtp=DEFAULT_WTP_PER_QALY):
    # 依据 WTP 阈值判定成本效益。 icer <= wtp 视为具成本效益（含负值/0=占优）。
    wtp_v = validate_positive(wtp, "wtp", DEFAULT_WTP_PER_QALY)
    try:
        v = float(icer)
    except (ValueError, TypeError):
        warnings.warn("icer 非法，按不具成本效益处理", UserWarning)
        return False
    if v == float("inf"):
        return False
    if v == float("-inf"):
        return True
    return v <= wtp_v


# ---- Markov 队列模型 ----
def build_transition_matrix(
    incidence=0.02,
    diag_rate=0.7,
    art_rate=0.9,
    progression=0.05,
    art_mortality=0.01,
    aids_mortality=0.15,
    background_mortality=0.005,
):
    """
    构造 5 状态年度转移矩阵（行=起始状态，列=终止状态），每行和为 1。
    状态顺序见 MARKOV_STATES。
    """
    inc = validate_rate(incidence, "incidence", 0.02)
    diag = validate_rate(diag_rate, "diag_rate", 0.7)
    art = validate_rate(art_rate, "art_rate", 0.9)
    prog = validate_rate(progression, "progression", 0.05)
    art_mort = validate_rate(art_mortality, "art_mortality", 0.01)
    aids_mort = validate_rate(aids_mortality, "aids_mortality", 0.15)
    bg_mort = validate_rate(background_mortality, "background_mortality", 0.005)

    n = len(MARKOV_STATES)
    M = np.zeros((n, n))
    idx = {s: i for i, s in enumerate(MARKOV_STATES)}

    # uninfected
    u = idx["uninfected"]
    M[u, idx["death"]] = bg_mort
    M[u, idx["hiv_undiagnosed"]] = inc * (1 - bg_mort)
    M[u, u] = 1.0 - M[u, idx["death"]] - M[u, idx["hiv_undiagnosed"]]

    # hiv_undiagnosed
    d = idx["hiv_undiagnosed"]
    M[d, idx["death"]] = bg_mort
    M[d, idx["hiv_on_art"]] = diag * art * (1 - bg_mort)
    M[d, idx["hiv_aids"]] = prog * (1 - bg_mort) * (1 - diag * art)
    M[d, d] = 1.0 - M[d, idx["death"]] - M[d, idx["hiv_on_art"]] - M[d, idx["hiv_aids"]]

    # hiv_on_art
    a = idx["hiv_on_art"]
    M[a, idx["death"]] = art_mort
    M[a, idx["hiv_aids"]] = prog * 0.2 * (1 - art_mort)
    M[a, a] = 1.0 - M[a, idx["death"]] - M[a, idx["hiv_aids"]]

    # hiv_aids
    s = idx["hiv_aids"]
    M[s, idx["death"]] = aids_mort
    M[s, idx["hiv_on_art"]] = art * 0.5 * (1 - aids_mort)
    M[s, s] = 1.0 - M[s, idx["death"]] - M[s, idx["hiv_on_art"]]

    # death（吸收态）
    M[idx["death"], idx["death"]] = 1.0

    # 数值上夹紧负的微小值并重新归一
    M = np.clip(M, 0.0, 1.0)
    row_sums = M.sum(axis=1, keepdims=True)
    M = M / row_sums
    return M


def run_markov_cohort(transition_matrix, initial_distribution, cycles, n_cohort=1.0):
    """
    运行 Markov 队列多周期模拟。

    transition_matrix: (n,n) 行随机矩阵
    initial_distribution: 长度 n 的初始人数/比例向量
    cycles: 周期数
    n_cohort: 若 initial_distribution 是比例，可用于换算人数（默认按原值）

    返回 dict: trace (cycles+1, n) 各周期分布 / states / conserved(bool)
    """
    M = np.asarray(transition_matrix, dtype=float)
    dist0 = np.asarray(initial_distribution, dtype=float)
    n = M.shape[0]
    if M.shape[0] != M.shape[1]:
        raise ValueError("transition_matrix 必须为方阵")
    if dist0.shape[0] != n:
        raise ValueError("initial_distribution 维度与矩阵不匹配")
    try:
        c = int(cycles)
    except (ValueError, TypeError):
        warnings.warn("cycles 非法，已重置为 1", UserWarning)
        c = 1
    c = max(0, c)

    scale = validate_positive(n_cohort, "n_cohort", 1.0)
    if scale > 0 and not np.isclose(dist0.sum(), scale) and np.isclose(dist0.sum(), 1.0):
        dist0 = dist0 * scale

    total0 = dist0.sum()
    trace = np.zeros((c + 1, n))
    trace[0] = dist0
    for t in range(c):
        trace[t + 1] = trace[t] @ M

    conserved = np.allclose(trace.sum(axis=1), total0, rtol=1e-6, atol=1e-6)
    return {
        "trace": trace,
        "states": list(MARKOV_STATES) if n == len(MARKOV_STATES) else list(range(n)),
        "total": float(total0),
        "conserved": bool(conserved),
        "final_distribution": trace[-1],
    }


def markov_total_qaly(markov_result, years_per_cycle=1.0, discount_rate=0.03, utilities=None):
    # 基于 Markov trace 计算队列累计 QALY（可贴现）。
    trace = np.asarray(markov_result["trace"], dtype=float)
    n = trace.shape[1]
    if utilities is None:
        utilities = np.array([STATE_UTILITY[s] for s in MARKOV_STATES])[:n]
    else:
        utilities = np.asarray(utilities, dtype=float)
    r = validate_rate(discount_rate, "discount_rate", 0.03)
    ypc = validate_positive(years_per_cycle, "years_per_cycle", 1.0)

    total = 0.0
    for t in range(trace.shape[0]):
        factor = 1.0 / ((1.0 + r) ** t) if r > 0 else 1.0
        total += float(np.dot(trace[t], utilities)) * ypc * factor
    return float(total)


# ---- 敏感性分析 / 预算影响 ----
def one_way_sensitivity(func, base_kwargs, param, values):
    # 单因素敏感性分析：固定其余参数，扫描 param 取 values 中各值。
    if not callable(func):
        raise ValueError("func 必须可调用")
    if param not in base_kwargs:
        warnings.warn(f"param {param} 不在 base_kwargs 中，仍将注入", UserWarning)

    out = []
    for v in values:
        kwargs = dict(base_kwargs)
        kwargs[param] = v
        res = func(**kwargs)
        out.append({"value": v, "result": res})
    return out


def budget_impact_analysis(
    cost_per_person, uptake_people, years, baseline_incidence,
    effectiveness, lifetime_treatment_cost, discount_rate=0.03,
):
    # 预算影响分析：比较项目投入 vs 因避免感染节省的终生治疗费。
    prog = program_cost(cost_per_person, uptake_people, years, discount_rate)
    averted_info = infections_averted(baseline_incidence, effectiveness, uptake_people, years)
    lt_cost = validate_positive(lifetime_treatment_cost, "lifetime_treatment_cost", 0.0)
    savings = averted_info["averted"] * lt_cost
    net = prog - savings
    return {
        "program_cost": float(prog),
        "averted": averted_info["averted"],
        "treatment_savings": float(savings),
        "net_budget_impact": float(net),
        "net_saving": net < 0,
    }


def full_cea(
    intervention_cost, comparator_cost,
    intervention_qaly, comparator_qaly,
    wtp=DEFAULT_WTP_PER_QALY,
):
    # 完整成本效果分析封装：ICER + WTP 判定，返回结构化 dict。
    icer_res = compute_icer(
        intervention_cost, intervention_qaly, comparator_cost, comparator_qaly
    )
    cost_effective = is_cost_effective(icer_res["icer"], wtp)
    return {
        "icer_result": icer_res,
        "wtp": validate_positive(wtp, "wtp", DEFAULT_WTP_PER_QALY),
        "cost_effective": cost_effective,
        "conclusion": "具成本效益" if cost_effective else "不具成本效益",
    }
