# 预防科普知识库：术语表、FAQ、误区辨析、检索与可读性评估。
# 纯字符串/数据结构处理，无数值模型。
import random
import warnings


# ---- 内置术语表（术语 -> 定义） ----
GLOSSARY = {
    "PrEP": "暴露前预防：HIV 阴性的高风险人群在可能暴露前持续服药，显著降低感染风险。",
    "PEP": "暴露后预防：在可能暴露 HIV 后 72 小时内开始、连续服用 28 天的阻断治疗。",
    "U=U": "持续检测不到即不具传染性（Undetectable = Untransmittable）：病毒载量长期受抑制者不会经性行为传播 HIV。",
    "窗口期": "从感染到检测能稳定查出的时间段，期间检测可能假阴性，常见为 2 到 6 周。",
    "血清转化": "感染后机体产生可检测抗体的过程，标志着抗体检测由阴转阳。",
    "病毒载量": "血浆中每毫升 HIV RNA 的拷贝数，反映体内病毒复制活跃程度。",
    "CD4": "一类免疫 T 细胞，是 HIV 主要攻击目标，其计数反映免疫功能强弱。",
    "抗逆转录病毒治疗": "ART：联合使用多种药物抑制 HIV 复制，使病毒载量降到检测限以下。",
    "ART": "抗逆转录病毒治疗：联合用药长期抑制 HIV 复制，是当前 HIV 治疗的核心。",
    "急性期": "感染早期病毒载量极高、传染性强的阶段，常伴流感样症状。",
    "潜伏库": "整合进长寿命细胞、处于休眠状态的 HIV，是难以治愈的主要障碍。",
    "依从性": "按医嘱规律服药的程度，PrEP 与 ART 的效果高度依赖良好依从性。",
    "TasP": "以治疗作为预防（Treatment as Prevention）：通过让感染者病毒抑制来减少传播。",
    "暴露": "皮肤黏膜或血液接触到可能含 HIV 的体液的事件，是评估风险的起点。",
    "假阴性": "实际已感染但检测结果为阴性，常因处于窗口期所致。",
}


# ---- 常见 FAQ（问 -> 答） ----
FAQ = [
    {
        "question": "PrEP 需要每天吃吗？",
        "answer": "常规口服 PrEP 通常需每日按时服用以维持药物保护浓度，特定人群可在医生指导下使用按需方案。",
        "topic": "PrEP",
    },
    {
        "question": "怀疑暴露后多久内要开始 PEP？",
        "answer": "PEP 越早越好，最好在 2 小时内，最迟不超过暴露后 72 小时开始，连续服用 28 天。",
        "topic": "PEP",
    },
    {
        "question": "U=U 是真的吗？",
        "answer": "是的，大量研究证实病毒载量持续检测不到的感染者不会经性行为把 HIV 传给伴侣。",
        "topic": "传播",
    },
    {
        "question": "窗口期检测阴性能放心吗？",
        "answer": "不能完全放心，窗口期内可能出现假阴性，建议在窗口期后复测确认。",
        "topic": "检测",
    },
    {
        "question": "安全套还有必要吗？",
        "answer": "有必要，安全套能同时预防 HIV 和其他性传播感染，是综合预防的重要一环。",
        "topic": "预防",
    },
    {
        "question": "蚊虫叮咬会传播 HIV 吗？",
        "answer": "不会，HIV 无法在蚊虫体内存活复制，日常接触如握手共餐也不会传播。",
        "topic": "传播",
    },
    {
        "question": "PrEP 能预防其他性病吗？",
        "answer": "不能，PrEP 仅针对 HIV，预防其他性传播感染仍需安全套和定期筛查。",
        "topic": "PrEP",
    },
]


# ---- 常见误区辨析（误区 -> 事实） ----
MISCONCEPTIONS = [
    {
        "myth": "只有特定人群才会感染 HIV。",
        "fact": "任何发生过暴露行为的人都可能感染，风险取决于行为而非身份标签。",
    },
    {
        "myth": "感染 HIV 就等于得了艾滋病。",
        "fact": "HIV 感染若及早规范治疗可长期不进展为艾滋病，与常人寿命接近。",
    },
    {
        "myth": "病毒检测不到就治愈了，可以停药。",
        "fact": "U=U 指不具传染性，并非治愈，擅自停药会导致病毒反弹。",
    },
    {
        "myth": "和感染者共餐握手会被传染。",
        "fact": "日常接触不会传播 HIV，它只通过血液、性接触和母婴等途径传播。",
    },
    {
        "myth": "吃了 PrEP 就完全不会感染，可以不用任何防护。",
        "fact": "PrEP 高效但非百分百，规律服药并配合其他措施才最稳妥。",
    },
]


# 主题标签集合，供分类返回。
TOPICS = ("PrEP", "PEP", "传播", "检测", "预防")


# 简单常见词表，用于可读性评估的"常见词比例"启发式。
_COMMON_WORDS = (
    "的", "了", "是", "在", "和", "与", "不", "也", "有", "会",
    "可以", "需要", "如果", "因为", "所以", "这", "那", "就", "你", "我",
)


# ---- 检索：术语 ----
def _score_match(query, text):
    # 对单条文本相对 query 的简单子串评分：命中得分，越靠前/越短得分越高。
    if not query:
        return 0.0
    q = query.strip().lower()
    t = text.lower()
    idx = t.find(q)
    if idx < 0:
        return 0.0
    # 基础命中分 + 位置奖励（越靠前越高）+ 长度奖励（query 占比越高越高）
    pos_bonus = 1.0 / (1.0 + idx)
    len_bonus = len(q) / max(len(t), 1)
    return 1.0 + pos_bonus + len_bonus


def search_glossary(query, limit=5):
    # 在术语表中按关键词检索（术语名与定义都参与匹配），按评分降序返回。
    if not isinstance(query, str) or not query.strip():
        warnings.warn("检索词为空或非字符串，返回空结果", UserWarning)
        return []
    try:
        limit = int(limit)
    except (TypeError, ValueError):
        limit = 5
    if limit < 1:
        limit = 1

    results = []
    for term, definition in GLOSSARY.items():
        score = max(_score_match(query, term) * 1.5, _score_match(query, definition))
        if score > 0:
            results.append({"term": term, "definition": definition, "score": score})
    results.sort(key=lambda r: r["score"], reverse=True)
    return results[:limit]


def lookup_term(term):
    """精确（忽略大小写）查找术语定义，未找到返回 None。"""
    if not isinstance(term, str) or not term.strip():
        warnings.warn("术语为空或非字符串", UserWarning)
        return None
    key = term.strip()
    if key in GLOSSARY:
        return GLOSSARY[key]
    lowered = key.lower()
    for k, v in GLOSSARY.items():
        if k.lower() == lowered:
            return v
    return None


# ---- 检索：FAQ ----
def search_faq(query, limit=5):
    # 在 FAQ 中按关键词检索（问题与答案都参与匹配），按评分降序返回。
    if not isinstance(query, str) or not query.strip():
        warnings.warn("检索词为空或非字符串，返回空结果", UserWarning)
        return []
    try:
        limit = int(limit)
    except (TypeError, ValueError):
        limit = 5
    if limit < 1:
        limit = 1

    results = []
    for item in FAQ:
        score = max(
            _score_match(query, item["question"]) * 1.3,
            _score_match(query, item["answer"]),
        )
        if score > 0:
            enriched = dict(item)
            enriched["score"] = score
            results.append(enriched)
    results.sort(key=lambda r: r["score"], reverse=True)
    return results[:limit]


# ---- 按主题分类返回 ----
def get_faq_by_topic(topic):
    # 返回某主题下的全部 FAQ 条目（list）。topic 不在已知主题集合时 返回空列表并警告。
    if not isinstance(topic, str) or topic not in TOPICS:
        warnings.warn(f"未知主题：{topic}，已知主题为 {TOPICS}", UserWarning)
        return []
    return [dict(item) for item in FAQ if item.get("topic") == topic]


def list_topics():
    # 返回所有可用主题标签（tuple）。
    return tuple(TOPICS)


def all_terms():
    # 返回术语表中全部术语名（list，按字典顺序）。
    return sorted(GLOSSARY.keys())


# ---- 文本可读性评分 ----
def readability_score(text):
    # 简单中文可读性启发式评分，返回 0-100，越高越易读。
    if not isinstance(text, str) or not text.strip():
        warnings.warn("文本为空或非字符串，可读性返回 0", UserWarning)
        return 0.0

    # 切句
    sentences = []
    buf = ""
    for ch in text:
        buf += ch
        if ch in "。！？!?\n":
            if buf.strip():
                sentences.append(buf.strip())
            buf = ""
    if buf.strip():
        sentences.append(buf.strip())
    if not sentences:
        sentences = [text]

    total_chars = sum(len(s) for s in sentences)
    avg_len = total_chars / len(sentences)

    # 句长得分：理想句长 ~15 字，越长扣分（线性，封顶到 50 字记 0 分）。
    len_score = max(0.0, 1.0 - max(0.0, avg_len - 15.0) / 35.0)

    # 常见词得分：命中常见词次数 / 文本字数，乘以放大系数后裁剪到 [0,1]。
    hit = sum(text.count(w) for w in _COMMON_WORDS)
    common_ratio = min(1.0, hit / max(len(text), 1) * 5.0)

    score = (0.6 * len_score + 0.4 * common_ratio) * 100.0
    return float(round(min(100.0, max(0.0, score)), 2))


def difficulty_level(text):
    # 依据可读性评分给出知识点难度分级。 返回 "入门" / "进阶" / "专业" 之一。
    score = readability_score(text) if isinstance(text, str) and text.strip() else 0.0
    if score >= 70:
        return "入门"
    elif score >= 40:
        return "进阶"
    else:
        return "专业"


# ---- 随机科普 tip（可 seed 复现） ----
TIPS = (
    "PrEP 需要规律服药才能维持有效保护浓度。",
    "怀疑暴露后 72 小时内尽快开始 PEP，越早越好。",
    "U=U：病毒持续检测不到的感染者不会经性行为传播 HIV。",
    "窗口期内检测可能假阴性，建议窗口期后复测。",
    "安全套能同时预防 HIV 和其他性传播感染。",
    "日常接触如握手、共餐不会传播 HIV。",
    "定期检测是早发现、早治疗的关键。",
    "ART 规范治疗可让感染者拥有接近常人的寿命。",
)


def random_tip(seed=None):
    """
    随机返回一条科普 tip。给定相同 seed 时结果可复现。
    """
    rng = random.Random(seed)
    return rng.choice(TIPS)


def random_tips(n=3, seed=None):
    """
    随机返回 n 条不重复的科普 tip（n 超过总数时返回全部）。
    给定相同 seed 时结果可复现。
    """
    try:
        n = int(n)
    except (TypeError, ValueError):
        warnings.warn("n 必须为整数，已使用默认 3", UserWarning)
        n = 3
    if n < 0:
        warnings.warn("n 不能为负，已使用 0", UserWarning)
        n = 0
    n = min(n, len(TIPS))
    rng = random.Random(seed)
    return rng.sample(list(TIPS), n)


# ---- 术语高亮标注 ----
def highlight_terms(text, terms=None):
    # 在文本中标出已知术语出现的位置（最长优先、不重叠匹配）。
    if not isinstance(text, str) or not text:
        warnings.warn("文本为空或非字符串，无可标注内容", UserWarning)
        return []
    if terms is None:
        terms = list(GLOSSARY.keys())
    # 长术语优先，避免被短术语先占位（如 "ART" 与 "抗逆转录病毒治疗"）。
    terms = sorted({t for t in terms if isinstance(t, str) and t}, key=len, reverse=True)

    n = len(text)
    occupied = [False] * n
    spans = []
    for term in terms:
        tlen = len(term)
        start = 0
        while True:
            idx = text.find(term, start)
            if idx < 0:
                break
            if not any(occupied[idx:idx + tlen]):
                spans.append({"term": term, "start": idx, "end": idx + tlen})
                for j in range(idx, idx + tlen):
                    occupied[j] = True
            start = idx + 1
    spans.sort(key=lambda s: s["start"])
    return spans


def annotate_text(text, open_tag="【", close_tag="】"):
    # 返回把已知术语用标签包裹后的标注文本，便于在界面中高亮显示。 无命中时原样返回。
    spans = highlight_terms(text)
    if not spans:
        return text if isinstance(text, str) else ""
    out = []
    cursor = 0
    for s in spans:
        out.append(text[cursor:s["start"]])
        out.append(open_tag + text[s["start"]:s["end"]] + close_tag)
        cursor = s["end"]
    out.append(text[cursor:])
    return "".join(out)
