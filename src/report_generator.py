# 评估报告生成：表格/卡片/章节拼接，支持 markdown 与纯文本。
# 输入缺失时填占位而非抛异常。
DISCLAIMER = (
    "本报告由「知药护身」科普平台基于您提供的信息自动生成，"
    "仅用于健康教育与自我评估参考，不能替代执业医师的面诊、检测与处方。"
    "任何 PrEP/PEP 用药决策请务必在专业医疗机构完成。"
    "如出现急性症状或近期高危暴露，请立即就医。"
)


# ---- 基础工具 ----
def _safe_str(value, placeholder="—"):
    # 把任意值转为展示字符串，None/空串用占位符。
    if value is None:
        return placeholder
    s = str(value).strip()
    return s if s else placeholder


def _fmt_pct(value, digits=1):
    # 把 0-1 的小数格式化为百分比字符串；非数值返回占位。
    try:
        v = float(value)
    except (ValueError, TypeError):
        return "—"
    return f"{v * 100:.{digits}f}%"


def _fmt_num(value, digits=2):
    """格式化数值，非数值返回占位。"""
    try:
        v = float(value)
    except (ValueError, TypeError):
        return "—"
    if v == int(v):
        return str(int(v))
    return f"{v:.{digits}f}"


# ---- 表格化 ----
def render_table(headers, rows, fmt="markdown"):
    # 把表头与行数据渲染为 markdown 或纯文本表格。
    headers = [_safe_str(h) for h in (headers or [])]
    norm_rows = []
    for r in (rows or []):
        norm_rows.append([_safe_str(c) for c in r])

    if not headers:
        return ""

    if fmt == "markdown":
        lines = []
        lines.append("| " + " | ".join(headers) + " |")
        lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
        for r in norm_rows:
            # 补齐 / 截断到表头长度
            cells = (r + [""] * len(headers))[: len(headers)]
            lines.append("| " + " | ".join(cells) + " |")
        return "\n".join(lines)
    else:
        # 纯文本：按列宽对齐
        col_w = [len(h) for h in headers]
        for r in norm_rows:
            for i in range(len(headers)):
                cell = r[i] if i < len(r) else ""
                col_w[i] = max(col_w[i], len(cell))
        def fmt_row(cells):
            padded = []
            for i in range(len(headers)):
                cell = cells[i] if i < len(cells) else ""
                padded.append(cell.ljust(col_w[i]))
            return "  ".join(padded).rstrip()
        lines = [fmt_row(headers), "  ".join("-" * w for w in col_w)]
        for r in norm_rows:
            lines.append(fmt_row(r))
        return "\n".join(lines)


# ---- 风险摘要卡片 ----
def risk_summary_card(risk_data, fmt="markdown"):
    # 基于综合风险结果生成摘要卡片文本。
    if not isinstance(risk_data, dict):
        risk_data = {}
    level = _safe_str(risk_data.get("risk_level"), "未知")
    prot = _fmt_pct(risk_data.get("protection_probability"))
    beh = _fmt_pct(risk_data.get("behavior_risk_probability"))
    final = _fmt_pct(risk_data.get("final_score"))

    emoji = {"低风险": "🟢", "中风险": "🟡", "高风险": "🔴"}.get(level, "⚪")

    if fmt == "markdown":
        return (
            f"### {emoji} 风险摘要：{level}\n\n"
            f"- 药物保护概率：**{prot}**\n"
            f"- 行为风险概率：**{beh}**\n"
            f"- 综合保护评分：**{final}**\n"
        )
    else:
        return (
            f"[风险摘要] {level}\n"
            f"  药物保护概率: {prot}\n"
            f"  行为风险概率: {beh}\n"
            f"  综合保护评分: {final}"
        )


# ---- 分级建议文案 ----
def recommendation_text(risk_level, decision_type="PrEP"):
    # 根据风险等级与决策类型给出分级建议文案。
    level = _safe_str(risk_level, "未知")
    base = {
        "高风险": "您目前处于较高的暴露风险，强烈建议尽快至专业机构评估并启动预防方案。",
        "中风险": "您存在一定暴露风险，建议主动咨询医生，结合检测结果决定预防策略。",
        "低风险": "您当前风险较低，请继续保持安全行为，并定期复查。",
        "未知": "信息不足以判定风险等级，建议补充评估。",
    }
    text = base.get(level, base["未知"])
    if decision_type == "PEP":
        text += " PEP 具有 72 小时时间窗，越早启动越好。"
    elif decision_type == "PrEP":
        text += " PrEP 需在确认 HIV 阴性后规律使用才能维持保护。"
    return text


# ---- 给药 / 化验数据表格 ----
def dosing_table(dosing_data, fmt="markdown"):
    # 把给药相关数据渲染为表格。
    if not isinstance(dosing_data, dict):
        dosing_data = {}
    headers = ["指标", "数值"]
    rows = [
        ["当前浓度", _fmt_num(dosing_data.get("current_concentration"))],
        ["保护阈值", _fmt_num(dosing_data.get("threshold"))],
        ["剩余保护天数", _fmt_num(dosing_data.get("remaining_days"))],
        ["保护概率", _fmt_pct(dosing_data.get("protection_probability"))],
    ]
    return render_table(headers, rows, fmt=fmt)


def lab_results_table(lab_data, fmt="markdown"):
    # 把化验结果渲染为表格。 lab_data: dict[str, value] 或 list[(name, value, unit)]。
    headers = ["项目", "结果"]
    rows = []
    if isinstance(lab_data, dict):
        for k, v in lab_data.items():
            rows.append([_safe_str(k), _safe_str(v)])
    elif isinstance(lab_data, (list, tuple)):
        for item in lab_data:
            if isinstance(item, (list, tuple)) and len(item) >= 2:
                name = _safe_str(item[0])
                val = _safe_str(item[1])
                unit = _safe_str(item[2], "") if len(item) >= 3 else ""
                rows.append([name, (val + " " + unit).strip()])
    return render_table(headers, rows, fmt=fmt)


# ---- 随访计划文本 ----
def followup_plan_text(schedule, fmt="markdown"):
    # 把随访时间表（list[dict] 含 day/label/tests）渲染为文本。
    if not isinstance(schedule, (list, tuple)) or not schedule:
        return "暂无随访计划。" if fmt != "markdown" else "_暂无随访计划。_"

    headers = ["时间点", "天数", "检测项目"]
    rows = []
    for item in schedule:
        if not isinstance(item, dict):
            continue
        label = _safe_str(item.get("label"))
        day = _fmt_num(item.get("day"))
        tests = item.get("tests", [])
        tests_str = "、".join(_safe_str(t) for t in tests) if tests else "—"
        rows.append([label, f"第{day}天", tests_str])
    table = render_table(headers, rows, fmt=fmt)
    if fmt == "markdown":
        return "#### 随访计划\n\n" + table
    return "[随访计划]\n" + table


# ---- 章节模板填充 ----
def fill_section(title, body, fmt="markdown", level=2):
    """填充单个章节，返回标题 + 正文。"""
    title = _safe_str(title, "未命名章节")
    body = body if body else "（无内容）"
    if fmt == "markdown":
        prefix = "#" * max(1, min(6, int(level)))
        return f"{prefix} {title}\n\n{body}"
    else:
        bar = "=" * (len(title) + 4)
        return f"{bar}\n  {title}\n{bar}\n{body}"


def disclaimer_block(fmt="markdown"):
    """免责声明区块。"""
    if fmt == "markdown":
        return f"> ⚠️ **免责声明**\n>\n> {DISCLAIMER}"
    return "[免责声明]\n" + DISCLAIMER


# ---- 完整报告组装 ----
def generate_full_report(
    title="HIV 预防评估报告",
    risk_data=None,
    dosing_data=None,
    lab_data=None,
    decision=None,
    followup=None,
    decision_type="PrEP",
    fmt="markdown",
):
    """
    组装完整评估报告，返回字符串。

    decision: 来自 clinical_guidelines 的决策 dict（可含 regimen/eligibility）。
    followup: 随访时间表 list[dict]。
    """
    sections = []

    # 标题
    if fmt == "markdown":
        sections.append(f"# {_safe_str(title)}")
    else:
        sections.append(f"{_safe_str(title)}\n{'#' * 30}")

    # 风险摘要
    if risk_data is not None:
        sections.append(risk_summary_card(risk_data, fmt=fmt))
        level = risk_data.get("risk_level") if isinstance(risk_data, dict) else None
        sections.append(fill_section(
            "建议", recommendation_text(level, decision_type), fmt=fmt
        ))

    # 给药数据
    if dosing_data is not None:
        sections.append(fill_section("给药与保护状态", dosing_table(dosing_data, fmt=fmt), fmt=fmt))

    # 化验结果
    if lab_data is not None:
        sections.append(fill_section("化验结果", lab_results_table(lab_data, fmt=fmt), fmt=fmt))

    # 临床决策
    if decision is not None and isinstance(decision, dict):
        sections.append(fill_section("临床决策", decision_summary_text(decision, fmt=fmt), fmt=fmt))

    # 随访计划
    if followup is not None:
        sections.append(followup_plan_text(followup, fmt=fmt))

    # 免责声明
    sections.append(disclaimer_block(fmt=fmt))

    sep = "\n\n" if fmt == "markdown" else "\n\n"
    return sep.join(s for s in sections if s)


def decision_summary_text(decision, fmt="markdown"):
    # 把 clinical_guidelines 决策 dict 概括为文本。
    if not isinstance(decision, dict):
        return "（无决策信息）"
    lines = []
    dtype = _safe_str(decision.get("type"), "评估")
    lines.append(f"决策类型：{dtype}")

    elig = decision.get("eligibility", {})
    if isinstance(elig, dict):
        if "eligible" in elig:
            lines.append(f"是否适合启动：{'是' if elig.get('eligible') else '否'}")
        if "recommend" in elig:
            lines.append(f"是否推荐启动：{'是' if elig.get('recommend') else '否'}")
        if elig.get("decision"):
            lines.append(f"判定：{_safe_str(elig.get('decision'))}")
        blockers = elig.get("blockers") or []
        for b in blockers:
            lines.append(f"  阻断项：{_safe_str(b)}")

    regimen = decision.get("regimen")
    if isinstance(regimen, dict):
        if regimen.get("primary"):
            lines.append(f"推荐方案：{_safe_str(regimen.get('primary'))}")
        if regimen.get("regimen"):
            lines.append(f"推荐方案：{_safe_str(regimen.get('regimen'))}")
        if regimen.get("duration_days"):
            lines.append(f"疗程：{_fmt_num(regimen.get('duration_days'))} 天")

    referrals = decision.get("referrals") or []
    if referrals:
        lines.append("转诊：" + "、".join(_safe_str(r) for r in referrals))

    body = "\n".join(lines)
    if fmt == "markdown":
        return body.replace("  阻断项", "- 阻断项")
    return body
