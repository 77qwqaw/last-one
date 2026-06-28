"""轻量级国际化（i18n）层 —— 中文（zh，默认）/ 英文（en）双语。

设计原则：
- **纯函数、零 streamlit 依赖**，与 ``pharmacokinetic_models`` 一样可独立单测。
- 译文集中在 ``TRANSLATIONS``，以「点分命名空间」key 组织（如 ``home.subtitle``、
  ``nav.kepu.desc``）。app.py 通过 ``t(key)`` 取当前语言文案。
- ``t`` 采用「目标语言 → 中文兜底 → 返回 key 本身」三级回退，保证：
  即使某条英文译文缺失，也会回落到中文而不是报错或显示空白；
  这样可以「逐页翻译、增量上线」，未翻译的部分自动维持中文。

约定：
- key 一律小写、用 ``.`` 分层；新增页面时按 ``<page>.<section>`` 命名。
- 含换行的按钮文案用 ``\n`` 保留多行（配合 CSS ``white-space:pre-line``）。
"""

# 支持的语言代码及其在切换按钮上显示的名称
SUPPORTED_LANGS = ("zh", "en")
DEFAULT_LANG = "zh"

# 语言切换按钮上显示的「下一个语言」名称（点击即切到该语言）
LANG_SWITCH_LABEL = {
    "zh": "🌐 EN",      # 当前中文 → 按钮提示切到英文
    "en": "🌐 中文",    # 当前英文 → 按钮提示切到中文
}


TRANSLATIONS = {
    "zh": {
        # ---- 全局 / 通用 ----
        "app.page_title": "知药护身｜HIV预防辅助平台",
        "common.back_home": "← 返回首页",

        # ---- 首页 ----
        "home.title": "🛡️ 知药护身",
        "home.subtitle": "HIV Prevention Decision Support System｜HIV预防辅助决策平台",
        "home.intro": (
            "融合行为风险分析、PEP/PrEP辅助判断、药物保护状态模拟与动态保护窗口评估，"
            "构建面向青年群体的数字化HIV预防辅助评估平台。"
        ),
        "home.choose_module": "📌 选择功能模块",

        # 首页四个数据概览卡片（数字 + 标签）
        "home.stat.pep_window.num": "72h",
        "home.stat.pep_window.label": "PEP启动黄金窗口",
        "home.stat.prep_rate.num": "99%",
        "home.stat.prep_rate.label": "规律服药PrEP保护率",
        "home.stat.fourinone.num": "4合1",
        "home.stat.fourinone.label": "行为·药理·决策·可视化",
        "home.stat.threestep.num": "3步",
        "home.stat.threestep.label": "从评估到行动建议",

        # 首页 8 个导航大按钮（多行文案，\n 用于换行）
        "nav.kepu": "🏫 公共科普\n\n校园与社区健康教育，HIV基础知识\nPrEP/PEP科普宣传",
        "nav.risk": "🧠 风险认知\n\n行为自评与心理支持\n降低恐慌，指引就医路径",
        "nav.medical": "🏥 医疗支持\n\n检测·就医·咨询全路径\nPEP/PrEP获取指南",
        "nav.assess": "🛡️ AI辅助评估\n\nPEP紧急度·PrEP启动建议\n药物保护状态动态模拟",
        "nav.insight": "📊 数据洞察\n\n传播模型·群体模拟\n预防效果可视化",
        "nav.tools": "🧰 个人工具\n\n窗口期计算器·漏服指导\n保护状态日志",
        "nav.policy": "⚖️ 政策与权益\n\n反歧视法规·隐私保护\n就医权益指南",
        "nav.story": "📖 故事与案例\n\n真实案例改编\n增强风险意识",

        # ---- 侧边栏 ----
        "sidebar.title": "### 关于本平台",
        "sidebar.info": (
            "**“知药护身”** 是一款专注于 **HIV暴露前预防（PrEP）** 的开源健康教育与风险评估辅助平台，"
            "旨在帮助大众科学认知PrEP用药、HIV感染风险、高危行为防护及社会污名相关问题。\n\n"
            "本平台**仅用于健康科普、风险自测、行为指导、用药依从性提醒**，"
            "**不具备医疗诊断、处方开具、替代医生诊疗功能**。"
            "所有评估结果仅供参考，不能替代专业感染科/皮肤科医生的临床判断。\n\n"
            "如需服用PrEP、PEP阻断药、HIV检测、咨询高危行为防护，请务必前往"
            "**正规医院感染科、疾控中心、社区卫生服务中心**进行专业咨询与诊疗。\n\n"
            "⚠️ 隐私提示：本平台所有数据本地存储，不上传个人隐私信息，严格保护您的健康隐私。"
        ),

        # ========== 科普页 ==========
        "kepu.section_card": '<div class="card"><div class="section-title">🏫 公共科普：风险感知与健康教育</div><p class="caption-text">面向校园与社区场景，提供系统化的HIV防控知识、PrEP/PEP科普内容与可传播的宣传素材。</p></div>',
        "kepu.tab.knowledge": "📘 知识百科",
        "kepu.tab.campus": "🎓 校园专区",
        "kepu.tab.community": "🏘️ 社区专区",
        "kepu.tab.myths": "❓ 常见误区",
        "kepu.tab.progress": "🔬 治疗进展",
        # --- tab1 知识百科 ---
        "kepu.t1.heading": "### HIV基础知识",
        "kepu.t1.what_is_hiv": (
            '<div class="highlight-card">\n'
            '<h4 style="color:#60a5fa; margin-top:0;">🔬 什么是HIV？</h4>\n'
            '<p style="color:#cbd5e1; line-height:1.8;">\n'
            'HIV（人类免疫缺陷病毒）是一种攻击人体免疫系统的病毒，主要破坏CD4⁺T淋巴细胞，'
            '导致免疫功能逐渐丧失。未经治疗的HIV感染最终会发展为艾滋病（AIDS）。\n'
            '</p>\n</div>'
        ),
        "kepu.t1.transmission": (
            '<div class="card">\n'
            '<h4 style="color:#93c5fd;">🦠 传播途径</h4>\n'
            '<ul style="color:#cbd5e1; line-height:2;">\n'
            '<li><strong>性传播</strong>：最主要的传播方式，包括异性与同性性行为</li>\n'
            '<li><strong>血液传播</strong>：共用注射器、不安全输血等</li>\n'
            '<li><strong>母婴传播</strong>：孕期、分娩或哺乳过程中传播</li>\n'
            '</ul>\n'
            '<p style="color:#94a3b8; font-size:14px;">❌ 日常接触（拥抱、共餐、蚊虫叮咬）<strong>不会</strong>传播HIV</p>\n'
            '</div>'
        ),
        "kepu.t1.prevention": (
            '<div class="card">\n'
            '<h4 style="color:#93c5fd;">🛡️ 预防手段</h4>\n'
            '<ul style="color:#cbd5e1; line-height:2;">\n'
            '<li><strong>安全套</strong>：正确使用可大幅降低风险</li>\n'
            '<li><strong>PrEP</strong>：暴露前预防，规律服药保护率>99%</li>\n'
            '<li><strong>PEP</strong>：暴露后72小时内紧急阻断</li>\n'
            '<li><strong>U=U</strong>：HIV感染者持续检测不到病毒=不传染</li>\n'
            '</ul>\n</div>'
        ),
        "kepu.t1.prep_pep_heading": "### PrEP与PEP详解",
        "kepu.t1.prep": (
            '<div class="card">\n'
            '<h4 style="color:#4ade80;">💊 PrEP（暴露前预防）</h4>\n'
            '<p style="color:#cbd5e1; line-height:1.8;">\n'
            '<strong>PrEP</strong>是在可能暴露于HIV<strong>之前</strong>开始服用药物，使体内维持足够的药物浓度，'
            '从而阻止HIV在体内建立感染。\n</p>\n'
            '<ul style="color:#cbd5e1; line-height:2;">\n'
            '<li>常用方案：恩曲他滨/替诺福韦（TDF/FTC）</li>\n'
            '<li><strong>每日服药</strong>：保护率>99%</li>\n'
            '<li><strong>按需服药（2-1-1方案）</strong>：适用于计划性行为</li>\n'
            '<li>需在医生指导下启动并定期检测</li>\n'
            '</ul>\n</div>'
        ),
        "kepu.t1.pep": (
            '<div class="card">\n'
            '<h4 style="color:#f87171;">🚨 PEP（暴露后预防）</h4>\n'
            '<p style="color:#cbd5e1; line-height:1.8;">\n'
            '<strong>PEP</strong>是在可能暴露于HIV<strong>之后</strong>紧急服用药物，以阻断病毒感染。\n</p>\n'
            '<ul style="color:#cbd5e1; line-height:2;">\n'
            '<li>⏰ <strong>72小时黄金窗口</strong>，越早越好</li>\n'
            '<li>连续服药<strong>28天</strong>，不可中断</li>\n'
            '<li>暴露后<strong>2小时内</strong>启动效果最佳</li>\n'
            '<li>需前往感染科/急诊获取处方</li>\n'
            '</ul>\n</div>'
        ),
        # --- tab2 校园专区 ---
        "kepu.t2.heading": "### 🎓 校园宣传教育素材",
        "kepu.t2.subtitle": '<p class="section-subtitle">适用于高校健康教育课程、社团活动、新生入学教育</p>',
        "kepu.t2.tips": (
            '<div class="highlight-card">\n'
            '<h4 style="color:#60a5fa; margin-top:0;">📋 校园科普活动建议</h4>\n'
            '<ul style="color:#cbd5e1; line-height:2;">\n'
            '<li>🎯 <strong>新生入学教育</strong>：嵌入防艾知识讲座（30分钟）</li>\n'
            '<li>🎯 <strong>12·1世界艾滋病日</strong>：校园宣传周+免费检测日</li>\n'
            '<li>🎯 <strong>同伴教育</strong>：培训学生志愿者进行朋辈科普</li>\n'
            '<li>🎯 <strong>安全套+检测试纸</strong>：通过自动贩卖机/健康驿站发放</li>\n'
            '</ul>\n</div>'
        ),
        # --- tab3 社区专区 ---
        "kepu.t3.heading": "### 🏘️ 社区宣传教育素材",
        "kepu.t3.subtitle": '<p class="section-subtitle">适用于社区卫生服务中心、公益组织、疾控宣传活动</p>',
        "kepu.t3.tips": (
            '<div class="highlight-card">\n'
            '<h4 style="color:#60a5fa; margin-top:0;">📋 社区科普活动建议</h4>\n'
            '<ul style="color:#cbd5e1; line-height:2;">\n'
            '<li>🎯 <strong>社区健康讲座</strong>：邀请疾控/医院专家定期宣讲</li>\n'
            '<li>🎯 <strong>免费快速检测</strong>：设置社区流动检测点</li>\n'
            '<li>🎯 <strong>宣传展板</strong>：在社区公告栏、卫生站设置科普展板</li>\n'
            '<li>🎯 <strong>重点人群外展</strong>：联合社会组织开展针对性宣教</li>\n'
            '</ul>\n</div>'
        ),
        # --- tab4 常见误区 ---
        "kepu.t4.heading": "### ❓ HIV常见误区澄清",
        "kepu.t4.myths": [
            ("蚊子叮咬会传播HIV？", "❌ 错误。HIV在蚊子体内无法存活和繁殖，蚊虫叮咬不会传播HIV。"),
            ("和HIV感染者一起吃饭会感染？", "❌ 错误。HIV不通过消化道传播，共餐、共用水杯、拥抱、握手等日常接触都是安全的。"),
            ("感染HIV就等于得了艾滋病？", "❌ 错误。HIV感染后经规范治疗，可以长期不发展为艾滋病。早期治疗可维持正常免疫功能。"),
            ("HIV感染者不能有健康的性生活？", "❌ 错误。当感染者持续检测不到病毒载量（U=U），就不会通过性行为传播HIV。"),
            ("口交不会传播HIV？", "⚠️ 风险较低但不为零。口腔有破损或溃疡时存在传播风险，建议使用口交安全套。"),
            ("PrEP可以100%预防HIV？", "⚠️ PrEP规律服药保护率>99%，但非100%。且PrEP不能预防其他性传播疾病。"),
        ],
        # --- tab5 治疗进展 ---
        "kepu.t5.heading": "### 🔬 HIV治疗最新进展",
        "kepu.t5.art": (
            '<div class="card">\n'
            '<h4 style="color:#93c5fd;">抗逆转录病毒治疗（ART）</h4>\n'
            '<p style="color:#cbd5e1; line-height:1.8;">\n'
            '目前HIV尚无法彻底治愈，但通过联合使用至少三种抗逆转录病毒药物，可将病毒载量抑制到检测不到的水平。\n</p>\n'
            '<ul style="color:#cbd5e1;">\n'
            '<li>一线方案：整合酶抑制剂+两种核苷类逆转录酶抑制剂</li>\n'
            '<li>长效注射剂：每2个月注射一次，已获批用于维持治疗</li>\n'
            '<li>功能性治愈研究：基因编辑、广谱中和抗体等处于临床试验阶段</li>\n'
            '</ul>\n</div>'
        ),

        # ========== 风险认知页 ==========
        "risk.section_card": '<div class="card"><div class="section-title">🧠 风险认知：行为自评与心理支持</div><p class="caption-text">帮助用户科学认识HIV传播风险，根据个人情况进行初步自评，降低不必要的恐慌，并给出明确的行为指引和就医途径建议。</p></div>',
        "risk.tab.self": "🔍 快速自评",
        "risk.tab.levels": "📊 风险等级对照",
        "risk.tab.support": "💬 心理支持",
        # --- tab1 快速自评（场景 → 结构化建议；用 label 匹配，双语通用）---
        "risk.t1.heading": "### 🔍 请描述你的情况，获取初步建议",
        "risk.t1.select_label": "选择最符合你当前状态的描述：",
        "risk.t1.get_assessment": "📋 获取初步评估",
        "risk.t1.scenarios": [
            {"label": "只是担心，没有明确风险行为", "level": "success",
             "title": "✅ 风险极低",
             "body": "没有实质性的高风险暴露，更多是焦虑情绪。建议通过正规渠道了解HIV知识，消除不必要的恐惧。",
             "tip_level": "info",
             "tip": "💡 建议：保持科学认知，如有持续焦虑可进行1次HIV检测以彻底安心。"},
            {"label": "近期有无保护性行为，但对方HIV状态未知", "level": "warning",
             "title": "⚠️ 存在一定风险",
             "body": "无保护性行为是HIV传播的主要途径之一。对方虽自称HIV阴性，但不能完全排除窗口期或不知情感染的可能。",
             "tip_level": "info",
             "tip": "💡 建议：① 尽快进行HIV检测（可考虑第四代抗原抗体联合检测，窗口期约2-4周）；② 如暴露在72小时内，立即咨询PEP；③ 今后坚持使用安全套或考虑PrEP。"},
            {"label": "安全套破裂/滑脱", "level": "warning",
             "title": "⚠️ 存在一定风险",
             "body": "安全套破裂导致防护失效，属于潜在暴露事件。风险程度取决于对方HIV状态及是否处于高病毒载量期。",
             "tip_level": "info",
             "tip": "💡 建议：① 如暴露在72小时内，强烈建议立即前往医院咨询PEP；② 在适当时间（4周、3个月）进行HIV检测；③ 学习安全套正确使用方法。"},
            {"label": "与已知HIV阳性者发生无保护性行为", "level": "error",
             "title": "🔴 高风险暴露",
             "body": "与已知HIV阳性者发生无保护性行为属于高风险暴露。如对方正在接受抗病毒治疗且病毒载量持续检测不到（U=U），则传播风险极低；否则风险显著升高。",
             "tip_level": "error",
             "tip": "💡 建议：① 如暴露在72小时内，**立即**前往医院启动PEP；② 即使超过72小时，也应尽快就医评估；③ 在医生指导下完成后续检测（基线、4周、3个月）。"},
            {"label": "共用注射器具", "level": "error",
             "title": "🔴 高风险暴露",
             "body": "共用注射器具是HIV血液传播的主要途径之一，属于极高风险行为。",
             "tip_level": "error",
             "tip": "💡 建议：① 如暴露在72小时内，**立即**就医咨询PEP；② 同时需检测乙肝、丙肝等其他血源性传染病；③ 寻求专业的戒毒或减害服务支持。"},
            {"label": "被不明来源的针具刺伤", "level": "error",
             "title": "🔴 高风险暴露",
             "body": "针刺伤属于血液暴露事件，需评估暴露源的HIV状态。如来源不明或已知阳性，风险较高。",
             "tip_level": "error",
             "tip": "💡 建议：① **2小时内**尽快就医，评估是否需要PEP；② 进行基线HIV、乙肝、丙肝检测；③ 在医生指导下完成后续随访。"},
            {"label": "已经出现发热、皮疹、淋巴结肿大等症状", "level": "warning",
             "title": "⚠️ 需警惕但不一定是HIV",
             "body": "发热、皮疹、淋巴结肿大等症状可能由多种原因引起，包括但不限于HIV急性感染。不能仅凭症状自我诊断。",
             "tip_level": "info",
             "tip": "💡 建议：① **尽快就医**，如实告知医生近期可能暴露史；② 进行HIV检测（第四代检测可在2-4周内检测出早期感染）；③ 不要过度恐慌，大多数出现类似症状的人最终并非HIV感染。"},
        ],
        # --- tab2 风险等级对照 ---
        "risk.t2.heading": "### 📊 行为风险等级对照表",
        "risk.t2.subtitle": '<p class="section-subtitle">以下为不同行为类型的HIV传播风险大致分级，仅供参考，个体情况需结合具体场景评估</p>',
        "risk.t2.data": [
            ("🟢 无风险", "日常接触", "拥抱、握手、共餐、共用卫生间、蚊虫叮咬", "无需检测，保持科学认知"),
            ("🟢 极低风险", "口交（无口腔破损）", "接受或主动口交且口腔完整", "风险极低但非零，可自愿检测"),
            ("🟡 低风险", "有保护性行为", "全程正确使用安全套", "安全套大幅降低风险，定期检测是好习惯"),
            ("🟠 中风险", "无保护性行为（对方状态未知）", "无安全套阴道/肛交，对方HIV状态不明", "72小时内咨询PEP，4周后检测"),
            ("🔴 高风险", "无保护性行为（对方HIV阳性）", "与已知阳性且未治疗/病毒载量未知者无套性交", "立即启动PEP，按医嘱完成检测"),
            ("🔴 极高风险", "共用注射器具", "共用针具静脉吸毒", "立即启动PEP，同时检测多血源性疾病"),
        ],
        # --- tab3 心理支持 ---
        "risk.t3.heading": "### 💬 心理支持与恐慌管理",
        "risk.t3.anxiety_card": (
            '<div class="highlight-card">\n'
            '<h4 style="color:#60a5fa; margin-top:0;">🧠 当焦虑来袭时，请记住</h4>\n'
            '<ul style="color:#cbd5e1; line-height:2;">\n'
            '<li>HIV是可防可控的慢性疾病，不再是"绝症"</li>\n'
            '<li>即使发生高风险暴露，及时启动PEP可以大幅降低感染概率</li>\n'
            '<li>检测是唯一确认HIV状态的方式，猜疑只会增加焦虑</li>\n'
            '<li>等待检测结果期间的焦虑是正常的，但绝大多数恐惧最终被证明是多余的</li>\n'
            '</ul>\n</div>'
        ),
        "risk.t3.support_heading": "### 📞 你可以寻求这些支持",
        "risk.t3.hotline_card": (
            '<div class="card">\n'
            '<h4 style="color:#93c5fd;">全国24小时心理援助热线</h4>\n'
            '<p style="font-size:28px; font-weight:800; color:#60a5fa;">12320</p>\n'
            '<p style="color:#cbd5e1;">卫生健康热线，可转接心理支持</p>\n</div>'
        ),
        "risk.t3.vct_card": (
            '<div class="card">\n'
            '<h4 style="color:#93c5fd;">各地疾控中心VCT门诊</h4>\n'
            '<p style="color:#cbd5e1;">提供免费、保密、自愿的HIV咨询检测服务</p>\n'
            '<p style="color:#94a3b8;">咨询过程全程保密，专业人员一对一服务</p>\n</div>'
        ),
        "risk.t3.fear_card": (
            '<div class="card">\n'
            '<h4 style="color:#93c5fd;">💡 如何应对"恐艾"心理</h4>\n'
            '<ol style="color:#cbd5e1; line-height:2;">\n'
            '<li><strong>停止反复搜索症状</strong>：网上自我诊断会加剧焦虑</li>\n'
            '<li><strong>设置"焦虑时间"</strong>：每天只允许自己用15分钟处理与HIV相关的担忧</li>\n'
            '<li><strong>相信科学</strong>：窗口期后做一次检测，结果阴性即可安心</li>\n'
            '<li><strong>必要时寻求专业帮助</strong>：如果焦虑持续影响日常生活，请咨询心理医生</li>\n'
            '</ol>\n</div>'
        ),

        # ========== 医疗支持页 ==========
        "medical.section_card": '<div class="card"><div class="section-title">🏥 医疗支持：检测·就医·咨询完整路径</div><p class="caption-text">整合检测机构、就医科室、PEP/PrEP获取途径等关键信息，帮助用户在需要时快速找到正确的医疗服务。</p></div>',
        "medical.tab.test": "🔬 检测指南",
        "medical.tab.path": "🏥 就医路径",
        "medical.tab.get": "💊 PEP/PrEP获取",
        "medical.tab.online": "📱 线上资源",
        # --- tab1 检测指南 ---
        "medical.t1.heading": "### 🔬 HIV检测完整指南",
        "medical.t1.window_card": (
            '<div class="highlight-card">\n'
            '<h4 style="color:#60a5fa; margin-top:0;">⏱️ 你需要知道的窗口期</h4>\n'
            '<p style="color:#cbd5e1; line-height:1.8;">\n'
            '窗口期是指从HIV感染到能被检测方法检测出来的时间间隔。不同检测方法的窗口期不同：\n'
            '</p>\n</div>'
        ),
        "medical.t1.test4": (
            '<div class="card" style="text-align:center;">\n'
            '<h4 style="color:#4ade80;">第四代检测</h4>\n'
            '<p style="font-size:32px; font-weight:800; color:#4ade80;">2-4周</p>\n'
            '<p style="color:#cbd5e1;">抗原+抗体联合检测<br>推荐首选</p>\n</div>'
        ),
        "medical.t1.test3": (
            '<div class="card" style="text-align:center;">\n'
            '<h4 style="color:#facc15;">第三代检测</h4>\n'
            '<p style="font-size:32px; font-weight:800; color:#facc15;">4-6周</p>\n'
            '<p style="color:#cbd5e1;">仅检测抗体<br>常用方法</p>\n</div>'
        ),
        "medical.t1.nat": (
            '<div class="card" style="text-align:center;">\n'
            '<h4 style="color:#60a5fa;">核酸检测</h4>\n'
            '<p style="font-size:32px; font-weight:800; color:#60a5fa;">1-2周</p>\n'
            '<p style="color:#cbd5e1;">检测病毒RNA<br>最早最灵敏</p>\n</div>'
        ),
        "medical.t1.where_heading": "### 🏢 去哪里检测",
        "medical.t1.where_table": (
            '<div class="card">\n'
            '<table style="color:#cbd5e1; width:100%; border-collapse:collapse;">\n'
            '<tr><th style="text-align:left; padding:8px; border-bottom:1px solid rgba(255,255,255,0.1);">机构类型</th><th style="text-align:left; padding:8px; border-bottom:1px solid rgba(255,255,255,0.1);">特点</th><th style="text-align:left; padding:8px; border-bottom:1px solid rgba(255,255,255,0.1);">费用</th></tr>\n'
            '<tr><td style="padding:8px; border-bottom:1px solid rgba(255,255,255,0.05);">各地疾控中心 VCT门诊</td><td style="padding:8px; border-bottom:1px solid rgba(255,255,255,0.05);">免费、保密、专业咨询</td><td style="padding:8px; border-bottom:1px solid rgba(255,255,255,0.05); color:#4ade80;">免费</td></tr>\n'
            '<tr><td style="padding:8px; border-bottom:1px solid rgba(255,255,255,0.05);">三甲医院 感染科/皮肤性病科</td><td style="padding:8px; border-bottom:1px solid rgba(255,255,255,0.05);">专业权威，可同步咨询PEP/PrEP</td><td style="padding:8px; border-bottom:1px solid rgba(255,255,255,0.05);">数十元至百元</td></tr>\n'
            '<tr><td style="padding:8px; border-bottom:1px solid rgba(255,255,255,0.05);">社会组织/公益机构</td><td style="padding:8px; border-bottom:1px solid rgba(255,255,255,0.05);">快速检测试纸，同伴支持</td><td style="padding:8px; border-bottom:1px solid rgba(255,255,255,0.05); color:#4ade80;">免费或低价</td></tr>\n'
            '<tr><td style="padding:8px;">自检试纸</td><td style="padding:8px;">可网购或药店购买，隐私方便</td><td style="padding:8px;">数十元</td></tr>\n'
            '</table>\n</div>'
        ),
        # --- tab2 就医路径 ---
        "medical.t2.heading": "### 🏥 就医路径指引",
        "medical.t2.subtitle": '<p class="section-subtitle">根据你的情况，选择正确的就医路径</p>',
        "medical.t2.pep_path": (
            '<div class="path-card pep">\n'
            '<h4 style="color:#f87171; margin-top:0;">🚨 高风险暴露 → PEP紧急处置</h4>\n'
            '<p style="color:#cbd5e1; line-height:1.8;">\n'
            '<strong>适用场景：</strong>72小时内发生无保护性行为、安全套破裂、性侵、针刺伤等高风险暴露<br>\n'
            '<strong>就医科室：</strong>综合医院<strong>感染科</strong>、<strong>急诊科</strong>、部分设有<strong>暴露后预防门诊</strong>的传染病医院<br>\n'
            '<strong>就医药店：</strong>部分城市指定药店可凭处方购买PEP药物<br>\n'
            '<strong>关键时间：</strong>暴露后<strong>2小时内</strong>启动最佳，<strong>24小时内</strong>效果很好，<strong>72小时内</strong>仍有效\n'
            '</p>\n</div>'
        ),
        "medical.t2.prep_path": (
            '<div class="path-card prep">\n'
            '<h4 style="color:#4ade80; margin-top:0;">💊 持续性风险 → PrEP启动评估</h4>\n'
            '<p style="color:#cbd5e1; line-height:1.8;">\n'
            '<strong>适用场景：</strong>伴侣为HIV阳性且未达到U=U、频繁更换性伴侣且难以坚持使用安全套、性工作者等<br>\n'
            '<strong>就医科室：</strong>综合医院<strong>感染科</strong>、<strong>皮肤性病科</strong>、部分疾控中心PrEP门诊<br>\n'
            '<strong>启动前需做：</strong>HIV检测（必须阴性）、肾功能检测、乙肝检测、性病筛查<br>\n'
            '<strong>服药后需定期：</strong>每3个月复查HIV、肾功能、性病\n'
            '</p>\n</div>'
        ),
        "medical.t2.test_path": (
            '<div class="path-card test">\n'
            '<h4 style="color:#facc15; margin-top:0;">🔬 定期检测/首次检测</h4>\n'
            '<p style="color:#cbd5e1; line-height:1.8;">\n'
            '<strong>推荐频率：</strong>性活跃人群每年至少1次，有高风险行为者每3-6个月1次<br>\n'
            '<strong>检测地点：</strong>疾控中心VCT门诊（免费）、医院感染科、社区快速检测点、自检试纸<br>\n'
            '<strong>注意事项：</strong>选择保密性好的正规机构，检测前后均可获得专业咨询\n'
            '</p>\n</div>'
        ),
        # --- tab3 PEP/PrEP获取 ---
        "medical.t3.heading": "### 💊 PEP/PrEP获取全流程",
        "medical.t3.pep_steps_heading": "<h4>🚨 PEP获取5步流程</h4>",
        "medical.t3.pep_steps": [
            ("暴露后尽快就医", "72小时内前往指定医院感染科/急诊科，告知医生暴露情况"),
            ("医生评估与检测", "进行HIV快速检测（排除已感染）、肝功能/肾功能检查"),
            ("开具处方取药", "医生根据评估结果开具PEP处方（通常为28天药物），在医院药房或指定药店取药"),
            ("规律服药28天", "每天固定时间服用，不可漏服、不可自行停药"),
            ("服药后随访检测", "服药完成后在4周、3个月进行HIV检测，确认预防效果"),
        ],
        "medical.t3.prep_steps_heading": "<h4>💊 PrEP启动5步流程</h4>",
        "medical.t3.prep_steps": [
            ("自我评估或使用本平台AI评估", "判断自己是否属于PrEP适用人群（持续高风险暴露）"),
            ("前往指定医疗机构", "感染科/PrEP门诊，与医生讨论启动PrEP的必要性"),
            ("完成基线检查", "HIV检测（必须阴性）+ 肾功能 + 乙肝 + 性病筛查"),
            ("获取处方并开始服药", "每日服用或按需服用方案，遵医嘱"),
            ("定期随访", "每3个月复查HIV及其他相关指标"),
        ],
        "medical.t3.pep_color": "#f87171",
        "medical.t3.prep_color": "#4ade80",
        # --- tab4 线上资源 ---
        "medical.t4.heading": "### 📱 线上资源与热线",
        "medical.t4.hotline_card": (
            '<div class="card">\n'
            '<h4 style="color:#93c5fd;">📞 全国卫生热线</h4>\n'
            '<p style="font-size:24px; font-weight:800; color:#60a5fa;">12320</p>\n'
            '<p style="color:#cbd5e1;">卫生健康咨询与投诉举报</p>\n</div>'
        ),
        "medical.t4.cdc_card": (
            '<div class="card">\n'
            '<h4 style="color:#93c5fd;">🌐 中国疾控中心艾防中心</h4>\n'
            '<p style="color:#cbd5e1;">全国HIV防治权威信息发布<br>疫情数据、政策法规、科普知识</p>\n</div>'
        ),
        "medical.t4.channels_card": (
            '<div class="highlight-card">\n'
            '<h4 style="color:#60a5fa; margin-top:0;">📱 推荐关注以下官方渠道</h4>\n'
            '<ul style="color:#cbd5e1; line-height:2;">\n'
            '<li>微信公众号：中国疾控中心艾防中心、各地疾控中心公众号</li>\n'
            '<li>小程序：部分省市已开通HIV检测预约、PEP地图等便民小程序</li>\n'
            '<li>公益组织：国内多家社会组织提供免费的检测咨询和同伴支持服务</li>\n'
            '</ul>\n'
            '<p style="color:#94a3b8; font-size:14px;">⚠️ 请认准官方或可信公益渠道，避免受到不实信息误导</p>\n</div>'
        ),

        # ========== 政策与权益页 ==========
        "policy.section_card": '<div class="card"><div class="section-title">⚖️ 政策法规与权益保护</div><p class="caption-text">了解我国艾滋病防治相关法律法规、隐私保护政策及感染者平等就业权利。</p></div>',
        "policy.tab.laws": "📜 法律法规",
        "policy.tab.privacy": "🔒 隐私保护",
        "policy.tab.antidiscrim": "🤝 反歧视与就业",
        "policy.laws_heading": "### 📜 主要法律法规",
        "policy.laws": [
            ("《艾滋病防治条例》", "明确各级政府、机构和个人在艾滋病防治中的责任，规定“四免一关怀”政策。"),
            ("《传染病防治法》", "将艾滋病列为乙类传染病，规定疫情报告、控制措施和法律责任。"),
            ("《民法典》", "保护个人隐私权，明确泄露、公开他人病情需承担民事责任。"),
        ],
        "policy.privacy_heading": "### 🔒 隐私保护",
        "policy.privacy_card": (
            '<div class="highlight-card">\n'
            '<ul style="color:#cbd5e1; line-height:2;">\n'
            '<li>HIV检测遵循“知情同意”和“保密”原则</li>\n'
            '<li>未经本人同意，任何单位和个人不得公开HIV感染者的个人信息</li>\n'
            '<li>医务人员违反保密义务将承担法律责任</li>\n'
            '</ul>\n</div>'
        ),
        "policy.anti_heading": "### 🤝 反歧视与平等就业",
        "policy.anti_card": (
            '<div class="highlight-card">\n'
            '<p style="color:#cbd5e1;">国家禁止在就业、教育、医疗等领域歧视HIV感染者及患者。用人单位不得以感染HIV为由拒绝录用或辞退员工。</p>\n'
            '<p style="color:#94a3b8;">如有遭遇歧视，可向当地卫生行政部门或劳动监察部门投诉。</p>\n</div>'
        ),

        # ========== 故事与案例页 ==========
        "story.section_card": '<div class="card"><div class="section-title">📖 故事与案例</div><p class="caption-text">通过真实案例改编的叙述，增强公众对HIV风险及科学防治的理解。</p></div>',
        "story.list": [
            ("小A的故事：一次侥幸的代价", "大学二年级的小A在一次聚会后发生无保护性行为，事后极度恐慌。由于缺乏知识，他没有在72小时内寻求PEP，直到6周后检测才确认未感染，但焦虑的日子让他深刻认识到安全套与PrEP的重要性。"),
            ("小B的觉醒：从恐惧到科学应对", "小B的伴侣被检出HIV阳性，第一时间咨询医生，并启动PrEP。在伴侣病毒载量检测不到后，两人生活如常，真正理解了U=U的意义。"),
            ("志愿者的坚持：社区防艾的微光", "社工小C在社区开展免费检测与咨询，遇到过无数恐艾咨询者，也帮助过高危人群及时获得PEP。她坚信，每减少一份歧视，就多一份预防的力量。"),
        ],

        # ========== 评估页 ==========
        # 注意：下面 *_opts / *_map 的「键」是中文，必须与模型函数内部匹配的字符串一致，
        # 不可改动；只翻译「值」（显示文案）。app 端用 format_func 显示译文、用原键传模型。
        "assess.section_card": '<div class="card"><div class="section-title">🧠 HIV预防辅助决策引擎</div><p class="caption-text">系统结合近期暴露情况、行为风险、服药连续性与药物保护变化，动态生成PEP/PrEP辅助建议和保护状态评估结果。</p></div>',
        "assess.disclaimer": "⚠️ 本工具用于风险评估与行为辅助，不替代医生建议",
        "assess.exposure_label": "近期是否发生明确或可能的高风险暴露？",
        "assess.exposure_opts": {"没有明确近期暴露": "没有明确近期暴露", "有，72小时以内": "有，72小时以内", "有，超过72小时": "有，超过72小时"},
        "assess.usertype_label": "你当前状态",
        "assess.usertype_opts": {"尚未使用PrEP": "尚未使用PrEP", "已经在使用PrEP": "已经在使用PrEP"},
        "assess.social_label": "如果身边有人感染HIV，你会：",
        "assess.social_opts": {"正常交往": "正常交往", "不确定": "不确定", "保持距离": "保持距离", "不接触": "不接触"},
        "assess.moral_label": "你认为HIV更像：",
        "assess.moral_opts": {"公共卫生问题": "公共卫生问题", "部分个人行为": "部分个人行为", "道德问题": "道德问题"},
        "assess.behavior_label": "近期是否存在以下行为：",
        "assess.behavior_opts": {"无高风险行为": "无高风险行为", "偶尔风险行为": "偶尔风险行为", "频繁高风险行为": "频繁高风险行为"},
        "assess.adv_expander": "⚙️ 高级药代动力学参数（可选）",
        "assess.drug_label": "药物方案",
        "assess.drug_opts": {"TDF/FTC (每日口服)": "TDF/FTC (每日口服)", "TAF/FTC (每日口服)": "TAF/FTC (每日口服)", "长效注射 (CAB-LA)": "长效注射 (CAB-LA)"},
        "assess.days_label": "连续服药天数",
        "assess.miss_label": "漏服天数",
        "assess.view_history": "查看历史评估记录",
        "assess.history_nth": "**第{n}次**：{rec}",
        "assess.no_records": "暂无记录",
        "assess.start_btn": "🚀 开始评估",
        "assess.pep_priority_metric": "PEP紧急优先级",
        "assess.pep_now": "优先级最高：立即线下就医咨询PEP",
        "assess.pep_late": "已超过PEP启动窗口，尽快检测",
        "assess.pep_none": "未提示PEP紧急窗口，可进行PrEP评估",
        "assess.prep_metric": "启动PrEP建议概率",
        "assess.prep_high": "强烈建议咨询医生启动PrEP",
        "assess.prep_mid": "建议咨询医生是否适合启动PrEP",
        "assess.prep_low": "PrEP需求较低，保持检测与防护",
        "assess.prep_info": "👉 判断是否进入PrEP人群",
        "assess.actions_heading": "### 建议行动",
        "assess.action1": "• 高风险暴露 → PEP咨询",
        "assess.action2": "• 持续风险 → 医生评估PrEP",
        "assess.action3": "• 定期检测，保持安全行为",
        "assess.status_card_h2": "🛡️ 当前保护状态",
        "assess.risk_level_label": "风险等级",
        "assess.score_label": "综合评分",
        "assess.status_map": {"保护较好": "保护较好", "部分保护": "部分保护", "保护不足": "保护不足"},
        "assess.risk_map": {"低风险": "低风险", "中风险": "中风险", "高风险": "高风险"},
        "assess.m_behavior": "行为概率",
        "assess.m_conc": "体内浓度",
        "assess.m_remain": "保护时间",
        "assess.m_protprob": "保护概率",
        "assess.m_score": "评分",
        "assess.m_risk": "风险等级",
        "assess.unit_days": "天",
        "assess.intervention_heading": "### 干预效果模拟",
        "assess.current_plan": "#### 当前方案",
        "assess.improved_plan": "#### 改进方案",
        "assess.improve_oral": "改进策略：连续服药 {d} 天，漏服减少至 {m} 天",
        "assess.improve_inject": "改进策略：下次注射提前 {d} 天",
        "assess.curve_heading": "### 体内药物保护曲线",
        "assess.curve_current": "当前方案",
        "assess.curve_improved": "改进方案",
        "assess.curve_threshold": "保护阈值",
        "assess.curve_xaxis": "时间(天)",
        "assess.curve_yaxis": "浓度(ng/mL)",
        "assess.mc_heading": "### 📊 群体模拟（Monte Carlo）",
        "assess.mc_pop_avg": "群体平均保护概率",
        "assess.mc_high_ratio": "高保护比例（>80%）",
        "assess.mc_xaxis": "保护概率(%)",
        "assess.mc_yaxis": "频数",
        "assess.sens_heading": "### 🧠 敏感性分析",
        "assess.sens_xaxis": "连续服药天数",
        "assess.sens_yaxis": "保护概率(%)",
        "assess.refs_expander": "📚 文献依据（点击展开）",
        "assess.refs_text": (
            "Grant et al., 2010（iPrEx研究）  \n"
            "Anderson et al., 2012（细胞内药物浓度）  \n"
            "Zhang et al., 2025（PK/PD模型）  \n"
            "CDC：PEP应在可能暴露后72小时内尽快启动，通常需持续28天"
        ),
        "assess.conclusion_heading": "### 🧪 科研结论",
        "assess.conclusion_text": (
            "本系统实现：\n"
            "① 近期暴露后PEP紧急提示\n"
            "② 是否需要启动PrEP（未服药人群）\n"
            "③ 当前是否被保护（已服药人群）\n"
            "④ 行为 → 药代 → 保护概率耦合分析\n"
            "👉 构建\"PEP紧急处置 — PrEP启动判断 — 保护窗口评估\"的HIV预防决策闭环"
        ),

        # ---- 数据洞察 ----
        # exposure_opts / method_opts / drug_opts 的「键」是程序逻辑用串，不可改动；只翻译「值」。
        "data.section_card": '<div class="card"><div class="section-title">📊 数据洞察与数学模型</div><p class="caption-text">利用数学模型和模拟算法，展示HIV传播概率、群体传播趋势及PrEP/PEP的人群影响。</p></div>',
        "data.tab1": "🔁 单次暴露传播概率",
        "data.tab2": "👥 SIR群体传播模拟",
        "data.tab3": "💊 PrEP群体有效性",
        "data.t1_heading": "### 🔁 单次暴露HIV传播概率计算器",
        "data.t1_subtitle": "根据暴露类型与病毒载量，估算单次行为感染风险",
        "data.t1_viral": "对方病毒载量 (拷贝/mL)",
        "data.t1_exposure": "暴露方式",
        "data.t1_exposure_opts": {"receptive_anal": "肛交（接受方）", "insertive_anal": "肛交（插入方）", "vaginal": "阴道性交", "oral": "口交"},
        "data.t1_condom": "使用安全套",
        "data.t1_circ": "已行包皮环切（仅对插入方有效）",
        "data.t1_sti": "存在其他性病",
        "data.t1_metric": "估算单次感染概率",
        "data.t1_caption": "模型基于文献综述，实际风险受多种因素影响，仅供参考。",
        "data.t2_heading": "### 👥 SIR模型模拟群体HIV传播",
        "data.t2_subtitle": "调整传染率与恢复率，观察疫情趋势变化",
        "data.t2_beta": "传染率 β",
        "data.t2_gamma": "恢复/治疗率 γ",
        "data.t2_pop": "总人口",
        "data.t2_i0": "初始感染者数量",
        "data.t2_days": "模拟天数",
        "data.t2_legend_s": "易感者",
        "data.t2_legend_i": "感染者",
        "data.t2_legend_r": "移出者",
        "data.t2_xaxis": "天数",
        "data.t2_yaxis": "人数",
        "data.t3_heading": "### 💊 PrEP覆盖率对群体传播的影响",
        "data.t3_subtitle": "假设不同PrEP覆盖率下新发感染减少比例",
        "data.t3_coverage": "PrEP在高风险人群中的覆盖率",
        "data.t3_metric": "预估新发感染减少",
        "data.t3_xaxis": "PrEP覆盖率(%)",
        "data.t3_yaxis": "新发感染减少(%)",

        # ---- 个人工具 ----
        "tools.section_card": '<div class="card"><div class="section-title">🧰 个人实用工具</div><p class="caption-text">提供窗口期计算、漏服补救指导及个人保护状态日志。</p></div>',
        "tools.tab1": "📅 窗口期计算器",
        "tools.tab2": "⚠️ 药物漏服处理",
        "tools.tab3": "📋 保护状态日志",
        "tools.t1_heading": "### 📅 HIV检测窗口期计算器",
        "tools.t1_intro": "输入可能暴露日期，计算不同检测方法的最早可靠检测时间",
        "tools.t1_date": "可能暴露日期",
        "tools.t1_method": "检测方法",
        "tools.t1_method_opts": {"第四代抗原抗体检测": "第四代抗原抗体检测", "第三代抗体检测": "第三代抗体检测", "核酸检测": "核酸检测"},
        "tools.t1_earliest": "最早可能检测时间：{date}（可能不够可靠）",
        "tools.t1_reliable": "推荐可靠检测时间：{date} 之后",
        "tools.t1_note": "注意：个体差异可能导致窗口期延长，必要时在3个月后复检确认。",
        "tools.t2_heading": "### ⚠️ 药物漏服处理指南",
        "tools.t2_drug": "正在使用的药物",
        "tools.t2_drug_opts": {"TDF/FTC (每日口服)": "TDF/FTC (每日口服)", "TAF/FTC (每日口服)": "TAF/FTC (每日口服)", "长效注射剂": "长效注射剂"},
        "tools.t2_miss": "漏服时间（小时）",
        "tools.t2_ok": "漏服不超过12小时，立即补服，下一剂按原时间服用。",
        "tools.t2_warn": "漏服12-24小时，立即补服，但可能降低保护效果。如果已接近下一次服药时间，跳过漏服剂量。",
        "tools.t2_err": "漏服超过24小时，保护可能失效。尽快联系医生，评估是否需要采取额外预防措施。",
        "tools.t2_inject": "长效注射剂漏服较少见，若超过预定注射日期2周以上，请尽快联系医生补打，并考虑临时加用口服PrEP。",
        "tools.t3_heading": "### 📋 保护状态日志",
        "tools.t3_intro": "记录每日服药情况，生成保护趋势图",
        "tools.t3_days": "记录天数",
        "tools.t3_status_intro": "每日服药状态（1=已服，0=漏服）：",
        "tools.t3_day_label": "第{n}天",
        "tools.t3_gen_btn": "生成保护曲线",
        "tools.t3_conc_name": "药物浓度",
        "tools.t3_threshold": "阈值",
        "tools.t3_xaxis": "天数",
        "tools.t3_yaxis": "浓度 (ng/mL)",
        "tools.t3_protected": "保护天数",
    },

    "en": {
        # ---- Global / common ----
        "app.page_title": "PrEP Guardian | HIV Prevention Support",
        "common.back_home": "← Back to Home",

        # ---- Home ----
        "home.title": "🛡️ PrEP Guardian",
        "home.subtitle": "HIV Prevention Decision Support System",
        "home.intro": (
            "An integrated platform combining behavioral risk analysis, PEP/PrEP decision support, "
            "drug-protection simulation and dynamic protection-window assessment — "
            "a digital HIV-prevention support tool designed for young people."
        ),
        "home.choose_module": "📌 Choose a Module",

        # Four overview stat cards on the home page (number + label)
        "home.stat.pep_window.num": "72h",
        "home.stat.pep_window.label": "PEP golden window",
        "home.stat.prep_rate.num": "99%",
        "home.stat.prep_rate.label": "Adherent PrEP protection",
        "home.stat.fourinone.num": "4-in-1",
        "home.stat.fourinone.label": "Behavior · Pharmacology · Decision · Visualization",
        "home.stat.threestep.num": "3 steps",
        "home.stat.threestep.label": "From assessment to action",

        # Eight navigation buttons (multi-line, \n for line breaks)
        "nav.kepu": "🏫 Public Education\n\nCampus & community health education, HIV basics\nPrEP/PEP awareness",
        "nav.risk": "🧠 Risk Awareness\n\nBehavioral self-assessment & psychological support\nEasing anxiety, guiding care",
        "nav.medical": "🏥 Medical Support\n\nTesting · care · counseling pathways\nHow to get PEP/PrEP",
        "nav.assess": "🛡️ AI-Assisted Assessment\n\nPEP urgency · PrEP start advice\nDrug-protection simulation",
        "nav.insight": "📊 Data Insights\n\nTransmission models · population simulation\nPrevention-effect visualization",
        "nav.tools": "🧰 Personal Tools\n\nWindow-period calculator · missed-dose guidance\nProtection-status log",
        "nav.policy": "⚖️ Policy & Rights\n\nAnti-discrimination law · privacy protection\nPatient-rights guide",
        "nav.story": "📖 Stories & Cases\n\nAdapted from real cases\nBuilding risk awareness",

        # ---- Sidebar ----
        "sidebar.title": "### About This Platform",
        "sidebar.info": (
            "**PrEP Guardian** is an open-source health-education and risk-assessment support platform "
            "focused on **HIV pre-exposure prophylaxis (PrEP)**, helping the public understand PrEP use, "
            "HIV infection risk, high-risk-behavior protection and stigma-related issues.\n\n"
            "This platform is **for health education, risk self-testing, behavioral guidance and "
            "adherence reminders only**, and **does not provide medical diagnosis, prescriptions, or "
            "any substitute for a doctor's care**. All assessment results are for reference only and "
            "cannot replace the clinical judgment of an infectious-disease/dermatology specialist.\n\n"
            "For PrEP, PEP blocking medication, HIV testing or high-risk-behavior counseling, please "
            "visit a **licensed hospital infectious-disease department, CDC, or community health center** "
            "for professional consultation.\n\n"
            "⚠️ Privacy note: all data on this platform is stored locally; no personal private "
            "information is uploaded, strictly protecting your health privacy."
        ),

        # ========== Public-education page ==========
        "kepu.section_card": '<div class="card"><div class="section-title">🏫 Public Education: Risk Awareness & Health Education</div><p class="caption-text">For campus and community settings — systematic HIV-prevention knowledge, PrEP/PEP educational content, and shareable outreach materials.</p></div>',
        "kepu.tab.knowledge": "📘 Knowledge Base",
        "kepu.tab.campus": "🎓 Campus Zone",
        "kepu.tab.community": "🏘️ Community Zone",
        "kepu.tab.myths": "❓ Common Myths",
        "kepu.tab.progress": "🔬 Treatment Advances",
        # --- tab1 ---
        "kepu.t1.heading": "### HIV Basics",
        "kepu.t1.what_is_hiv": (
            '<div class="highlight-card">\n'
            '<h4 style="color:#60a5fa; margin-top:0;">🔬 What is HIV?</h4>\n'
            '<p style="color:#cbd5e1; line-height:1.8;">\n'
            'HIV (human immunodeficiency virus) attacks the immune system, mainly destroying CD4⁺ '
            'T-lymphocytes and progressively impairing immune function. Untreated HIV infection '
            'eventually develops into AIDS.\n'
            '</p>\n</div>'
        ),
        "kepu.t1.transmission": (
            '<div class="card">\n'
            '<h4 style="color:#93c5fd;">🦠 Routes of Transmission</h4>\n'
            '<ul style="color:#cbd5e1; line-height:2;">\n'
            '<li><strong>Sexual transmission</strong>: the main route, including heterosexual and same-sex contact</li>\n'
            '<li><strong>Blood-borne</strong>: shared needles, unsafe transfusions, etc.</li>\n'
            '<li><strong>Mother-to-child</strong>: during pregnancy, delivery or breastfeeding</li>\n'
            '</ul>\n'
            '<p style="color:#94a3b8; font-size:14px;">❌ Everyday contact (hugging, sharing meals, mosquito bites) does <strong>not</strong> transmit HIV</p>\n'
            '</div>'
        ),
        "kepu.t1.prevention": (
            '<div class="card">\n'
            '<h4 style="color:#93c5fd;">🛡️ Prevention Methods</h4>\n'
            '<ul style="color:#cbd5e1; line-height:2;">\n'
            '<li><strong>Condoms</strong>: correct use greatly reduces risk</li>\n'
            '<li><strong>PrEP</strong>: pre-exposure prophylaxis, &gt;99% protection with regular dosing</li>\n'
            '<li><strong>PEP</strong>: emergency blocking within 72h after exposure</li>\n'
            '<li><strong>U=U</strong>: an undetectable viral load means untransmittable</li>\n'
            '</ul>\n</div>'
        ),
        "kepu.t1.prep_pep_heading": "### PrEP and PEP Explained",
        "kepu.t1.prep": (
            '<div class="card">\n'
            '<h4 style="color:#4ade80;">💊 PrEP (Pre-Exposure Prophylaxis)</h4>\n'
            '<p style="color:#cbd5e1; line-height:1.8;">\n'
            '<strong>PrEP</strong> means taking medication <strong>before</strong> possible HIV exposure, '
            'maintaining sufficient drug levels in the body to stop HIV from establishing infection.\n</p>\n'
            '<ul style="color:#cbd5e1; line-height:2;">\n'
            '<li>Common regimen: emtricitabine/tenofovir (TDF/FTC)</li>\n'
            '<li><strong>Daily dosing</strong>: &gt;99% protection</li>\n'
            '<li><strong>On-demand (2-1-1)</strong>: for planned encounters</li>\n'
            '<li>Must be started under medical guidance with regular testing</li>\n'
            '</ul>\n</div>'
        ),
        "kepu.t1.pep": (
            '<div class="card">\n'
            '<h4 style="color:#f87171;">🚨 PEP (Post-Exposure Prophylaxis)</h4>\n'
            '<p style="color:#cbd5e1; line-height:1.8;">\n'
            '<strong>PEP</strong> means taking medication urgently <strong>after</strong> possible HIV exposure to block infection.\n</p>\n'
            '<ul style="color:#cbd5e1; line-height:2;">\n'
            '<li>⏰ <strong>72-hour golden window</strong> — the sooner the better</li>\n'
            '<li>Take continuously for <strong>28 days</strong>, without interruption</li>\n'
            '<li>Most effective when started <strong>within 2 hours</strong> of exposure</li>\n'
            '<li>Obtain a prescription from an infectious-disease dept./ER</li>\n'
            '</ul>\n</div>'
        ),
        # --- tab2 ---
        "kepu.t2.heading": "### 🎓 Campus Outreach Materials",
        "kepu.t2.subtitle": '<p class="section-subtitle">For university health-education courses, club activities and freshman orientation</p>',
        "kepu.t2.tips": (
            '<div class="highlight-card">\n'
            '<h4 style="color:#60a5fa; margin-top:0;">📋 Suggested Campus Activities</h4>\n'
            '<ul style="color:#cbd5e1; line-height:2;">\n'
            '<li>🎯 <strong>Freshman orientation</strong>: embed a 30-minute HIV-prevention lecture</li>\n'
            '<li>🎯 <strong>Dec 1 World AIDS Day</strong>: campus awareness week + free testing day</li>\n'
            '<li>🎯 <strong>Peer education</strong>: train student volunteers for peer outreach</li>\n'
            '<li>🎯 <strong>Condoms + test kits</strong>: distribute via vending machines / health stations</li>\n'
            '</ul>\n</div>'
        ),
        # --- tab3 ---
        "kepu.t3.heading": "### 🏘️ Community Outreach Materials",
        "kepu.t3.subtitle": '<p class="section-subtitle">For community health centers, non-profits and CDC outreach campaigns</p>',
        "kepu.t3.tips": (
            '<div class="highlight-card">\n'
            '<h4 style="color:#60a5fa; margin-top:0;">📋 Suggested Community Activities</h4>\n'
            '<ul style="color:#cbd5e1; line-height:2;">\n'
            '<li>🎯 <strong>Community health talks</strong>: invite CDC/hospital experts for regular sessions</li>\n'
            '<li>🎯 <strong>Free rapid testing</strong>: set up mobile community testing points</li>\n'
            '<li>🎯 <strong>Info boards</strong>: place educational boards in community notice areas and clinics</li>\n'
            '<li>🎯 <strong>Key-population outreach</strong>: partner with civil-society groups for targeted education</li>\n'
            '</ul>\n</div>'
        ),
        # --- tab4 ---
        "kepu.t4.heading": "### ❓ Clearing Up Common HIV Myths",
        "kepu.t4.myths": [
            ("Do mosquito bites transmit HIV?", "❌ False. HIV cannot survive or reproduce inside mosquitoes; bites do not transmit HIV."),
            ("Can you get HIV by eating with someone who is HIV-positive?", "❌ False. HIV is not transmitted through the digestive tract; sharing meals, cups, hugging and handshakes are all safe."),
            ("Does having HIV mean you have AIDS?", "❌ False. With proper treatment, HIV infection can be kept from progressing to AIDS for a long time. Early treatment preserves normal immune function."),
            ("Can people with HIV not have a healthy sex life?", "❌ False. When viral load stays undetectable (U=U), HIV is not transmitted through sex."),
            ("Oral sex doesn't transmit HIV, right?", "⚠️ Lower risk but not zero. Risk exists when there are mouth sores or cuts; using an oral condom (dental dam) is advised."),
            ("Does PrEP prevent HIV 100%?", "⚠️ Regular PrEP gives >99% protection, but not 100%. PrEP also does not prevent other STIs."),
        ],
        # --- tab5 ---
        "kepu.t5.heading": "### 🔬 Latest Advances in HIV Treatment",
        "kepu.t5.art": (
            '<div class="card">\n'
            '<h4 style="color:#93c5fd;">Antiretroviral Therapy (ART)</h4>\n'
            '<p style="color:#cbd5e1; line-height:1.8;">\n'
            'HIV cannot yet be fully cured, but combining at least three antiretroviral drugs can suppress '
            'the viral load to undetectable levels.\n</p>\n'
            '<ul style="color:#cbd5e1;">\n'
            '<li>First-line: an integrase inhibitor + two nucleoside reverse-transcriptase inhibitors</li>\n'
            '<li>Long-acting injectable: given once every 2 months, approved for maintenance therapy</li>\n'
            '<li>Functional-cure research: gene editing, broadly neutralizing antibodies, etc., in clinical trials</li>\n'
            '</ul>\n</div>'
        ),

        # ========== Risk-awareness page ==========
        "risk.section_card": '<div class="card"><div class="section-title">🧠 Risk Awareness: Self-Assessment & Psychological Support</div><p class="caption-text">Helps users understand HIV transmission risk scientifically, do a preliminary self-assessment based on their situation, reduce unnecessary panic, and get clear behavioral guidance and care-seeking advice.</p></div>',
        "risk.tab.self": "🔍 Quick Self-Check",
        "risk.tab.levels": "📊 Risk-Level Reference",
        "risk.tab.support": "💬 Psychological Support",
        # --- tab1 ---
        "risk.t1.heading": "### 🔍 Describe your situation to get preliminary advice",
        "risk.t1.select_label": "Choose the description that best fits your current situation:",
        "risk.t1.get_assessment": "📋 Get Preliminary Assessment",
        "risk.t1.scenarios": [
            {"label": "Just worried, no clear risk behavior", "level": "success",
             "title": "✅ Very low risk",
             "body": "There is no substantial high-risk exposure — mostly anxiety. We suggest learning about HIV through reliable channels to ease unnecessary fear.",
             "tip_level": "info",
             "tip": "💡 Advice: keep a science-based view; if anxiety persists, one HIV test can give you full peace of mind."},
            {"label": "Recent unprotected sex, partner's HIV status unknown", "level": "warning",
             "title": "⚠️ Some risk exists",
             "body": "Unprotected sex is one of the main routes of HIV transmission. Even if the partner claims to be HIV-negative, a window-period or unknown infection cannot be fully ruled out.",
             "tip_level": "info",
             "tip": "💡 Advice: ① Get tested soon (a 4th-gen antigen/antibody test, window ~2–4 weeks); ② If within 72h of exposure, consult about PEP immediately; ③ Use condoms consistently or consider PrEP going forward."},
            {"label": "Condom broke / slipped off", "level": "warning",
             "title": "⚠️ Some risk exists",
             "body": "A broken condom means protection failed — a potential exposure event. The level of risk depends on the partner's HIV status and whether they have a high viral load.",
             "tip_level": "info",
             "tip": "💡 Advice: ① If within 72h, strongly consider going to a hospital about PEP immediately; ② Test for HIV at appropriate times (4 weeks, 3 months); ③ Learn how to use condoms correctly."},
            {"label": "Unprotected sex with a known HIV-positive person", "level": "error",
             "title": "🔴 High-risk exposure",
             "body": "Unprotected sex with a known HIV-positive person is a high-risk exposure. If the partner is on antiretroviral therapy with a sustained undetectable viral load (U=U), transmission risk is very low; otherwise risk rises significantly.",
             "tip_level": "error",
             "tip": "💡 Advice: ① If within 72h, go to a hospital and start PEP **immediately**; ② Even past 72h, seek medical evaluation as soon as possible; ③ Complete follow-up testing under medical guidance (baseline, 4 weeks, 3 months)."},
            {"label": "Shared injection equipment", "level": "error",
             "title": "🔴 High-risk exposure",
             "body": "Sharing injection equipment is one of the main routes of blood-borne HIV transmission — an extremely high-risk behavior.",
             "tip_level": "error",
             "tip": "💡 Advice: ① If within 72h, seek care about PEP **immediately**; ② Also test for hepatitis B, hepatitis C and other blood-borne infections; ③ Seek professional drug-treatment or harm-reduction support."},
            {"label": "Pricked by a needle of unknown origin", "level": "error",
             "title": "🔴 High-risk exposure",
             "body": "A needle-stick is a blood-exposure event; the HIV status of the source must be assessed. If the source is unknown or known positive, risk is higher.",
             "tip_level": "error",
             "tip": "💡 Advice: ① Seek care as soon as possible **within 2 hours** to assess whether PEP is needed; ② Get baseline HIV, hepatitis B and C testing; ③ Complete follow-up under medical guidance."},
            {"label": "Already have symptoms such as fever, rash, swollen lymph nodes", "level": "warning",
             "title": "⚠️ Be alert, but it is not necessarily HIV",
             "body": "Fever, rash and swollen lymph nodes can have many causes, including but not limited to acute HIV infection. You cannot self-diagnose from symptoms alone.",
             "tip_level": "info",
             "tip": "💡 Advice: ① **Seek care soon** and honestly tell your doctor about any recent possible exposure; ② Get an HIV test (a 4th-gen test can detect early infection within 2–4 weeks); ③ Don't over-panic — most people with such symptoms turn out not to have HIV."},
        ],
        # --- tab2 ---
        "risk.t2.heading": "### 📊 Behavioral Risk-Level Reference Table",
        "risk.t2.subtitle": '<p class="section-subtitle">Below is an approximate grading of HIV transmission risk by behavior type — for reference only; individual situations must be assessed in context</p>',
        "risk.t2.data": [
            ("🟢 No risk", "Everyday contact", "Hugging, handshakes, shared meals, shared toilets, mosquito bites", "No testing needed; keep a science-based view"),
            ("🟢 Very low risk", "Oral sex (no mouth lesions)", "Receptive or insertive oral sex with an intact mouth", "Very low but non-zero risk; voluntary testing optional"),
            ("🟡 Low risk", "Protected sex", "Correct condom use throughout", "Condoms greatly reduce risk; regular testing is a good habit"),
            ("🟠 Medium risk", "Unprotected sex (partner status unknown)", "Condomless vaginal/anal sex with a partner of unknown HIV status", "Consult about PEP within 72h; test after 4 weeks"),
            ("🔴 High risk", "Unprotected sex (partner HIV-positive)", "Condomless sex with a known-positive, untreated/unknown-viral-load partner", "Start PEP immediately; complete testing as advised"),
            ("🔴 Very high risk", "Shared injection equipment", "Sharing needles for intravenous drug use", "Start PEP immediately; also test for multiple blood-borne diseases"),
        ],
        # --- tab3 ---
        "risk.t3.heading": "### 💬 Psychological Support & Panic Management",
        "risk.t3.anxiety_card": (
            '<div class="highlight-card">\n'
            '<h4 style="color:#60a5fa; margin-top:0;">🧠 When anxiety hits, remember</h4>\n'
            '<ul style="color:#cbd5e1; line-height:2;">\n'
            '<li>HIV is a preventable, controllable chronic condition — no longer a "death sentence"</li>\n'
            '<li>Even after high-risk exposure, starting PEP promptly greatly lowers infection risk</li>\n'
            '<li>Testing is the only way to confirm HIV status; speculation only increases anxiety</li>\n'
            '<li>Anxiety while awaiting results is normal, but the vast majority of fears prove unfounded</li>\n'
            '</ul>\n</div>'
        ),
        "risk.t3.support_heading": "### 📞 Support you can reach out to",
        "risk.t3.hotline_card": (
            '<div class="card">\n'
            '<h4 style="color:#93c5fd;">National 24h Psychological Support Hotline</h4>\n'
            '<p style="font-size:28px; font-weight:800; color:#60a5fa;">12320</p>\n'
            '<p style="color:#cbd5e1;">Health hotline; can transfer to psychological support</p>\n</div>'
        ),
        "risk.t3.vct_card": (
            '<div class="card">\n'
            '<h4 style="color:#93c5fd;">Local CDC VCT Clinics</h4>\n'
            '<p style="color:#cbd5e1;">Free, confidential, voluntary HIV counseling and testing</p>\n'
            '<p style="color:#94a3b8;">Fully confidential, one-on-one service by professionals</p>\n</div>'
        ),
        "risk.t3.fear_card": (
            '<div class="card">\n'
            '<h4 style="color:#93c5fd;">💡 How to cope with HIV-related fear ("AIDS phobia")</h4>\n'
            '<ol style="color:#cbd5e1; line-height:2;">\n'
            '<li><strong>Stop repeatedly searching symptoms</strong>: online self-diagnosis worsens anxiety</li>\n'
            '<li><strong>Set a "worry time"</strong>: allow yourself only 15 minutes a day for HIV-related concerns</li>\n'
            '<li><strong>Trust science</strong>: one test after the window period; a negative result means you can relax</li>\n'
            '<li><strong>Seek professional help if needed</strong>: if anxiety keeps disrupting daily life, consult a mental-health professional</li>\n'
            '</ol>\n</div>'
        ),

        # ========== Medical-support page ==========
        "medical.section_card": '<div class="card"><div class="section-title">🏥 Medical Support: Testing · Care · Counseling Pathways</div><p class="caption-text">Brings together key information on testing facilities, clinical departments and how to obtain PEP/PrEP, helping users quickly find the right medical service when needed.</p></div>',
        "medical.tab.test": "🔬 Testing Guide",
        "medical.tab.path": "🏥 Care Pathways",
        "medical.tab.get": "💊 Getting PEP/PrEP",
        "medical.tab.online": "📱 Online Resources",
        # --- tab1 ---
        "medical.t1.heading": "### 🔬 Complete HIV Testing Guide",
        "medical.t1.window_card": (
            '<div class="highlight-card">\n'
            '<h4 style="color:#60a5fa; margin-top:0;">⏱️ The window period you should know</h4>\n'
            '<p style="color:#cbd5e1; line-height:1.8;">\n'
            'The window period is the interval between HIV infection and when a test can detect it. Different test methods have different windows:\n'
            '</p>\n</div>'
        ),
        "medical.t1.test4": (
            '<div class="card" style="text-align:center;">\n'
            '<h4 style="color:#4ade80;">4th-Generation Test</h4>\n'
            '<p style="font-size:32px; font-weight:800; color:#4ade80;">2-4 weeks</p>\n'
            '<p style="color:#cbd5e1;">Combined antigen + antibody<br>Recommended first choice</p>\n</div>'
        ),
        "medical.t1.test3": (
            '<div class="card" style="text-align:center;">\n'
            '<h4 style="color:#facc15;">3rd-Generation Test</h4>\n'
            '<p style="font-size:32px; font-weight:800; color:#facc15;">4-6 weeks</p>\n'
            '<p style="color:#cbd5e1;">Antibody only<br>Common method</p>\n</div>'
        ),
        "medical.t1.nat": (
            '<div class="card" style="text-align:center;">\n'
            '<h4 style="color:#60a5fa;">Nucleic-Acid Test (NAT)</h4>\n'
            '<p style="font-size:32px; font-weight:800; color:#60a5fa;">1-2 weeks</p>\n'
            '<p style="color:#cbd5e1;">Detects viral RNA<br>Earliest & most sensitive</p>\n</div>'
        ),
        "medical.t1.where_heading": "### 🏢 Where to Get Tested",
        "medical.t1.where_table": (
            '<div class="card">\n'
            '<table style="color:#cbd5e1; width:100%; border-collapse:collapse;">\n'
            '<tr><th style="text-align:left; padding:8px; border-bottom:1px solid rgba(255,255,255,0.1);">Facility type</th><th style="text-align:left; padding:8px; border-bottom:1px solid rgba(255,255,255,0.1);">Features</th><th style="text-align:left; padding:8px; border-bottom:1px solid rgba(255,255,255,0.1);">Cost</th></tr>\n'
            '<tr><td style="padding:8px; border-bottom:1px solid rgba(255,255,255,0.05);">Local CDC VCT clinic</td><td style="padding:8px; border-bottom:1px solid rgba(255,255,255,0.05);">Free, confidential, professional counseling</td><td style="padding:8px; border-bottom:1px solid rgba(255,255,255,0.05); color:#4ade80;">Free</td></tr>\n'
            '<tr><td style="padding:8px; border-bottom:1px solid rgba(255,255,255,0.05);">Tertiary hospital infectious-disease / dermatology-STI dept.</td><td style="padding:8px; border-bottom:1px solid rgba(255,255,255,0.05);">Authoritative; can also consult about PEP/PrEP</td><td style="padding:8px; border-bottom:1px solid rgba(255,255,255,0.05);">Tens to ~100 RMB</td></tr>\n'
            '<tr><td style="padding:8px; border-bottom:1px solid rgba(255,255,255,0.05);">Civil-society / non-profit groups</td><td style="padding:8px; border-bottom:1px solid rgba(255,255,255,0.05);">Rapid test kits, peer support</td><td style="padding:8px; border-bottom:1px solid rgba(255,255,255,0.05); color:#4ade80;">Free or low-cost</td></tr>\n'
            '<tr><td style="padding:8px;">Self-test kits</td><td style="padding:8px;">Buy online or at pharmacies; private and convenient</td><td style="padding:8px;">Tens of RMB</td></tr>\n'
            '</table>\n</div>'
        ),
        # --- tab2 ---
        "medical.t2.heading": "### 🏥 Care-Pathway Guidance",
        "medical.t2.subtitle": '<p class="section-subtitle">Choose the right care pathway based on your situation</p>',
        "medical.t2.pep_path": (
            '<div class="path-card pep">\n'
            '<h4 style="color:#f87171; margin-top:0;">🚨 High-risk exposure → emergency PEP</h4>\n'
            '<p style="color:#cbd5e1; line-height:1.8;">\n'
            '<strong>When it applies:</strong> high-risk exposure within 72h — unprotected sex, broken condom, sexual assault, needle-stick, etc.<br>\n'
            '<strong>Department:</strong> hospital <strong>infectious-disease</strong> or <strong>emergency</strong> dept.; some infectious-disease hospitals have a <strong>post-exposure prophylaxis clinic</strong><br>\n'
            '<strong>Pharmacies:</strong> in some cities, designated pharmacies dispense PEP drugs with a prescription<br>\n'
            '<strong>Timing:</strong> best started <strong>within 2 hours</strong> of exposure, very effective <strong>within 24 hours</strong>, still effective <strong>within 72 hours</strong>\n'
            '</p>\n</div>'
        ),
        "medical.t2.prep_path": (
            '<div class="path-card prep">\n'
            '<h4 style="color:#4ade80; margin-top:0;">💊 Ongoing risk → PrEP-start assessment</h4>\n'
            '<p style="color:#cbd5e1; line-height:1.8;">\n'
            '<strong>When it applies:</strong> an HIV-positive partner not yet at U=U, frequent partner changes with inconsistent condom use, sex workers, etc.<br>\n'
            '<strong>Department:</strong> hospital <strong>infectious-disease</strong> or <strong>dermatology-STI</strong> dept.; some CDC PrEP clinics<br>\n'
            '<strong>Before starting:</strong> HIV test (must be negative), kidney-function test, hepatitis B test, STI screening<br>\n'
            '<strong>While on PrEP:</strong> re-check HIV, kidney function and STIs every 3 months\n'
            '</p>\n</div>'
        ),
        "medical.t2.test_path": (
            '<div class="path-card test">\n'
            '<h4 style="color:#facc15; margin-top:0;">🔬 Regular / first-time testing</h4>\n'
            '<p style="color:#cbd5e1; line-height:1.8;">\n'
            '<strong>Suggested frequency:</strong> sexually active people at least once a year; those with high-risk behavior every 3–6 months<br>\n'
            '<strong>Where:</strong> CDC VCT clinic (free), hospital infectious-disease dept., community rapid-test points, self-test kits<br>\n'
            '<strong>Note:</strong> choose a confidential, accredited facility; professional counseling is available before and after testing\n'
            '</p>\n</div>'
        ),
        # --- tab3 ---
        "medical.t3.heading": "### 💊 Full Process for Getting PEP/PrEP",
        "medical.t3.pep_steps_heading": "<h4>🚨 PEP: 5-Step Process</h4>",
        "medical.t3.pep_steps": [
            ("Seek care ASAP after exposure", "Go to a designated hospital infectious-disease/ER dept. within 72h and tell the doctor about the exposure"),
            ("Doctor assessment & testing", "Rapid HIV test (to rule out existing infection), liver- and kidney-function checks"),
            ("Get prescription & medication", "The doctor issues a PEP prescription (usually 28 days); pick up the drugs at the hospital pharmacy or a designated pharmacy"),
            ("Take medication for 28 days", "Take at a fixed time daily; do not miss doses or stop on your own"),
            ("Follow-up testing after the course", "Test for HIV at 4 weeks and 3 months after finishing to confirm prevention"),
        ],
        "medical.t3.prep_steps_heading": "<h4>💊 PrEP: 5-Step Process</h4>",
        "medical.t3.prep_steps": [
            ("Self-assess or use this platform's AI assessment", "Decide whether you fit the PrEP-eligible group (ongoing high-risk exposure)"),
            ("Go to a designated facility", "Infectious-disease / PrEP clinic; discuss with a doctor whether to start PrEP"),
            ("Complete baseline checks", "HIV test (must be negative) + kidney function + hepatitis B + STI screening"),
            ("Get a prescription and start", "Daily or on-demand regimen, as directed by your doctor"),
            ("Regular follow-up", "Re-check HIV and other relevant markers every 3 months"),
        ],
        "medical.t3.pep_color": "#f87171",
        "medical.t3.prep_color": "#4ade80",
        # --- tab4 ---
        "medical.t4.heading": "### 📱 Online Resources & Hotlines",
        "medical.t4.hotline_card": (
            '<div class="card">\n'
            '<h4 style="color:#93c5fd;">📞 National Health Hotline</h4>\n'
            '<p style="font-size:24px; font-weight:800; color:#60a5fa;">12320</p>\n'
            '<p style="color:#cbd5e1;">Health consultation and complaints/reporting</p>\n</div>'
        ),
        "medical.t4.cdc_card": (
            '<div class="card">\n'
            '<h4 style="color:#93c5fd;">🌐 China CDC — National Center for AIDS/STD Control</h4>\n'
            '<p style="color:#cbd5e1;">Authoritative national HIV-prevention information<br>Surveillance data, policy & regulations, health education</p>\n</div>'
        ),
        "medical.t4.channels_card": (
            '<div class="highlight-card">\n'
            '<h4 style="color:#60a5fa; margin-top:0;">📱 Recommended official channels to follow</h4>\n'
            '<ul style="color:#cbd5e1; line-height:2;">\n'
            '<li>WeChat official accounts: China CDC AIDS center and local CDC accounts</li>\n'
            '<li>Mini-programs: some provinces/cities offer HIV-test booking, PEP maps and other convenience tools</li>\n'
            '<li>Non-profits: many domestic civil-society groups offer free testing counseling and peer support</li>\n'
            '</ul>\n'
            '<p style="color:#94a3b8; font-size:14px;">⚠️ Verify official or trusted non-profit channels to avoid being misled by false information</p>\n</div>'
        ),

        # ========== Policy & rights page ==========
        "policy.section_card": '<div class="card"><div class="section-title">⚖️ Policy, Law & Rights Protection</div><p class="caption-text">Understand China\'s HIV/AIDS-prevention laws and regulations, privacy-protection policy, and the equal-employment rights of people living with HIV.</p></div>',
        "policy.tab.laws": "📜 Laws & Regulations",
        "policy.tab.privacy": "🔒 Privacy Protection",
        "policy.tab.antidiscrim": "🤝 Anti-Discrimination & Employment",
        "policy.laws_heading": "### 📜 Key Laws & Regulations",
        "policy.laws": [
            ("Regulations on the Prevention and Treatment of AIDS", "Define the responsibilities of governments, institutions and individuals in AIDS prevention, and set out the \"Four Frees and One Care\" policy."),
            ("Law on the Prevention and Treatment of Infectious Diseases", "Classify AIDS as a Class-B infectious disease, with rules on outbreak reporting, control measures and legal liability."),
            ("Civil Code", "Protects the right to privacy and makes clear that disclosing or publicizing another person's medical condition incurs civil liability."),
        ],
        "policy.privacy_heading": "### 🔒 Privacy Protection",
        "policy.privacy_card": (
            '<div class="highlight-card">\n'
            '<ul style="color:#cbd5e1; line-height:2;">\n'
            '<li>HIV testing follows the principles of "informed consent" and "confidentiality"</li>\n'
            '<li>Without the person\'s consent, no organization or individual may disclose a person living with HIV\'s personal information</li>\n'
            '<li>Medical staff who breach confidentiality bear legal liability</li>\n'
            '</ul>\n</div>'
        ),
        "policy.anti_heading": "### 🤝 Anti-Discrimination & Equal Employment",
        "policy.anti_card": (
            '<div class="highlight-card">\n'
            '<p style="color:#cbd5e1;">The state prohibits discrimination against people living with HIV in employment, education, healthcare and other fields. Employers may not refuse to hire or dismiss staff on the grounds of HIV infection.</p>\n'
            '<p style="color:#94a3b8;">If you experience discrimination, you can file a complaint with the local health authority or labor-inspection department.</p>\n</div>'
        ),

        # ========== Stories & cases page ==========
        "story.section_card": '<div class="card"><div class="section-title">📖 Stories & Cases</div><p class="caption-text">Narratives adapted from real cases, to deepen public understanding of HIV risk and science-based prevention.</p></div>',
        "story.list": [
            ("A's story: the price of a close call", "A second-year university student, A, had unprotected sex after a party and panicked afterward. Lacking knowledge, he didn't seek PEP within 72 hours; only a test 6 weeks later confirmed he wasn't infected. Those anxious days made him deeply realize the importance of condoms and PrEP."),
            ("B's awakening: from fear to a science-based response", "B's partner tested HIV-positive. B consulted a doctor right away and started PrEP. After the partner's viral load became undetectable, the two lived life as usual and truly understood the meaning of U=U."),
            ("A volunteer's persistence: a glimmer in community HIV prevention", "Social worker C runs free testing and counseling in the community, meeting countless people anxious about HIV and helping high-risk individuals get PEP in time. She firmly believes that every bit of stigma reduced adds a bit more prevention."),
        ],

        # ---- Assessment (评估) ----
        # 注意：*_opts / *_map 的「键」是中文，必须与模型函数内部匹配的字符串一致，不可改动；只翻译「值」。
        "assess.section_card": '<div class="card"><div class="section-title">🧠 HIV Prevention Decision Engine</div><p class="caption-text">The system combines recent exposure, behavioral risk, dosing adherence and drug-protection dynamics to generate PEP/PrEP support advice and a protection-status assessment in real time.</p></div>',
        "assess.disclaimer": "⚠️ This tool is for risk assessment and behavioral support; it does not replace a doctor's advice.",
        "assess.exposure_label": "Has a definite or possible high-risk exposure occurred recently?",
        "assess.exposure_opts": {"没有明确近期暴露": "No clear recent exposure", "有，72小时以内": "Yes, within 72 hours", "有，超过72小时": "Yes, more than 72 hours ago"},
        "assess.usertype_label": "Your current status",
        "assess.usertype_opts": {"尚未使用PrEP": "Not yet using PrEP", "已经在使用PrEP": "Already using PrEP"},
        "assess.social_label": "If someone around you were infected with HIV, you would:",
        "assess.social_opts": {"正常交往": "Interact normally", "不确定": "Not sure", "保持距离": "Keep distance", "不接触": "Avoid contact"},
        "assess.moral_label": "You think HIV is more of:",
        "assess.moral_opts": {"公共卫生问题": "A public-health issue", "部分个人行为": "Partly personal behavior", "道德问题": "A moral issue"},
        "assess.behavior_label": "Have the following behaviors occurred recently:",
        "assess.behavior_opts": {"无高风险行为": "No high-risk behavior", "偶尔风险行为": "Occasional risk behavior", "频繁高风险行为": "Frequent high-risk behavior"},
        "assess.adv_expander": "⚙️ Advanced pharmacokinetic parameters (optional)",
        "assess.drug_label": "Drug regimen",
        "assess.drug_opts": {"TDF/FTC (每日口服)": "TDF/FTC (daily oral)", "TAF/FTC (每日口服)": "TAF/FTC (daily oral)", "长效注射 (CAB-LA)": "Long-acting injection (CAB-LA)"},
        "assess.days_label": "Consecutive days on medication",
        "assess.miss_label": "Missed days",
        "assess.view_history": "View past assessment records",
        "assess.history_nth": "**#{n}**: {rec}",
        "assess.no_records": "No records yet",
        "assess.start_btn": "🚀 Start assessment",
        "assess.pep_priority_metric": "PEP urgency priority",
        "assess.pep_now": "Highest priority: seek in-person medical care for PEP immediately",
        "assess.pep_late": "Past the PEP initiation window; get tested as soon as possible",
        "assess.pep_none": "No urgent PEP window indicated; you can proceed with PrEP assessment",
        "assess.prep_metric": "Recommended probability of starting PrEP",
        "assess.prep_high": "Strongly recommend consulting a doctor to start PrEP",
        "assess.prep_mid": "Recommend consulting a doctor about whether PrEP is suitable",
        "assess.prep_low": "PrEP need is low; keep testing and protection",
        "assess.prep_info": "👉 Determine whether you belong to the PrEP population",
        "assess.actions_heading": "### Recommended actions",
        "assess.action1": "• High-risk exposure → PEP consultation",
        "assess.action2": "• Ongoing risk → doctor evaluation for PrEP",
        "assess.action3": "• Test regularly, maintain safe behavior",
        "assess.status_card_h2": "🛡️ Current protection status",
        "assess.risk_level_label": "Risk level",
        "assess.score_label": "Overall score",
        "assess.status_map": {"保护较好": "Well protected", "部分保护": "Partially protected", "保护不足": "Insufficient protection"},
        "assess.risk_map": {"低风险": "Low risk", "中风险": "Moderate risk", "高风险": "High risk"},
        "assess.m_behavior": "Behavior probability",
        "assess.m_conc": "In-body concentration",
        "assess.m_remain": "Protection time",
        "assess.m_protprob": "Protection probability",
        "assess.m_score": "Score",
        "assess.m_risk": "Risk level",
        "assess.unit_days": "days",
        "assess.intervention_heading": "### Intervention-effect simulation",
        "assess.current_plan": "#### Current plan",
        "assess.improved_plan": "#### Improved plan",
        "assess.improve_oral": "Improvement strategy: take medication for {d} consecutive days, reduce missed days to {m}",
        "assess.improve_inject": "Improvement strategy: move the next injection {d} days earlier",
        "assess.curve_heading": "### In-body drug-protection curve",
        "assess.curve_current": "Current plan",
        "assess.curve_improved": "Improved plan",
        "assess.curve_threshold": "Protection threshold",
        "assess.curve_xaxis": "Time (days)",
        "assess.curve_yaxis": "Concentration (ng/mL)",
        "assess.mc_heading": "### 📊 Population simulation (Monte Carlo)",
        "assess.mc_pop_avg": "Population mean protection probability",
        "assess.mc_high_ratio": "High-protection ratio (>80%)",
        "assess.mc_xaxis": "Protection probability (%)",
        "assess.mc_yaxis": "Frequency",
        "assess.sens_heading": "### 🧠 Sensitivity analysis",
        "assess.sens_xaxis": "Consecutive days on medication",
        "assess.sens_yaxis": "Protection probability (%)",
        "assess.refs_expander": "📚 References (click to expand)",
        "assess.refs_text": (
            "Grant et al., 2010 (iPrEx study)  \n"
            "Anderson et al., 2012 (intracellular drug concentration)  \n"
            "Zhang et al., 2025 (PK/PD model)  \n"
            "CDC: PEP should be started as soon as possible within 72 hours of a possible exposure, and usually continued for 28 days"
        ),
        "assess.conclusion_heading": "### 🧪 Research conclusion",
        "assess.conclusion_text": (
            "This system implements:\n"
            "① Urgent PEP alert after recent exposure\n"
            "② Whether PrEP should be started (for those not on medication)\n"
            "③ Whether currently protected (for those on medication)\n"
            "④ Behavior → pharmacokinetics → protection-probability coupling analysis\n"
            "👉 Building a closed-loop HIV-prevention decision process of \"urgent PEP handling — PrEP-start judgment — protection-window assessment\""
        ),

        # ---- Data insights (数据洞察) ----
        "data.section_card": '<div class="card"><div class="section-title">📊 Data Insights & Mathematical Models</div><p class="caption-text">Using mathematical models and simulation algorithms to show HIV transmission probability, population spread trends and the impact of PrEP/PEP.</p></div>',
        "data.tab1": "🔁 Per-exposure transmission probability",
        "data.tab2": "👥 SIR population-spread simulation",
        "data.tab3": "💊 Population-level PrEP effectiveness",
        "data.t1_heading": "### 🔁 Per-exposure HIV transmission probability calculator",
        "data.t1_subtitle": "Estimate per-act infection risk based on exposure type and viral load",
        "data.t1_viral": "Partner's viral load (copies/mL)",
        "data.t1_exposure": "Exposure type",
        "data.t1_exposure_opts": {"receptive_anal": "Anal (receptive)", "insertive_anal": "Anal (insertive)", "vaginal": "Vaginal sex", "oral": "Oral sex"},
        "data.t1_condom": "Condom used",
        "data.t1_circ": "Circumcised (effective for insertive partner only)",
        "data.t1_sti": "Other STI present",
        "data.t1_metric": "Estimated per-act infection probability",
        "data.t1_caption": "The model is based on a literature review; actual risk is affected by many factors and is for reference only.",
        "data.t2_heading": "### 👥 SIR model simulation of population HIV spread",
        "data.t2_subtitle": "Adjust transmission and recovery rates to observe epidemic trends",
        "data.t2_beta": "Transmission rate β",
        "data.t2_gamma": "Recovery/treatment rate γ",
        "data.t2_pop": "Total population",
        "data.t2_i0": "Initial number of infected",
        "data.t2_days": "Simulation days",
        "data.t2_legend_s": "Susceptible",
        "data.t2_legend_i": "Infected",
        "data.t2_legend_r": "Removed",
        "data.t2_xaxis": "Days",
        "data.t2_yaxis": "People",
        "data.t3_heading": "### 💊 Impact of PrEP coverage on population spread",
        "data.t3_subtitle": "Assumed reduction in new infections under different PrEP coverage levels",
        "data.t3_coverage": "PrEP coverage among high-risk population",
        "data.t3_metric": "Estimated reduction in new infections",
        "data.t3_xaxis": "PrEP coverage (%)",
        "data.t3_yaxis": "Reduction in new infections (%)",

        # ---- Personal tools (个人工具) ----
        "tools.section_card": '<div class="card"><div class="section-title">🧰 Personal Practical Tools</div><p class="caption-text">Provides a window-period calculator, missed-dose guidance and a personal protection-status log.</p></div>',
        "tools.tab1": "📅 Window-period calculator",
        "tools.tab2": "⚠️ Missed-dose handling",
        "tools.tab3": "📋 Protection-status log",
        "tools.t1_heading": "### 📅 HIV testing window-period calculator",
        "tools.t1_intro": "Enter the possible exposure date to calculate the earliest reliable testing time for different methods",
        "tools.t1_date": "Possible exposure date",
        "tools.t1_method": "Testing method",
        "tools.t1_method_opts": {"第四代抗原抗体检测": "4th-gen antigen/antibody test", "第三代抗体检测": "3rd-gen antibody test", "核酸检测": "Nucleic acid test"},
        "tools.t1_earliest": "Earliest possible testing time: {date} (may not be reliable enough)",
        "tools.t1_reliable": "Recommended reliable testing time: after {date}",
        "tools.t1_note": "Note: individual variation may extend the window period; if necessary, retest after 3 months to confirm.",
        "tools.t2_heading": "### ⚠️ Missed-dose handling guide",
        "tools.t2_drug": "Medication in use",
        "tools.t2_drug_opts": {"TDF/FTC (每日口服)": "TDF/FTC (daily oral)", "TAF/FTC (每日口服)": "TAF/FTC (daily oral)", "长效注射剂": "Long-acting injection"},
        "tools.t2_miss": "Time since missed dose (hours)",
        "tools.t2_ok": "Missed by no more than 12 hours: take the dose immediately and take the next dose at the usual time.",
        "tools.t2_warn": "Missed by 12-24 hours: take the dose immediately, but protection may be reduced. If it's close to the next dose, skip the missed dose.",
        "tools.t2_err": "Missed by more than 24 hours: protection may be lost. Contact a doctor as soon as possible to assess whether extra precautions are needed.",
        "tools.t2_inject": "Missed long-acting injections are uncommon; if more than 2 weeks past the scheduled injection date, contact a doctor promptly for a catch-up dose and consider temporary oral PrEP.",
        "tools.t3_heading": "### 📋 Protection-status log",
        "tools.t3_intro": "Record daily dosing to generate a protection-trend chart",
        "tools.t3_days": "Days to record",
        "tools.t3_status_intro": "Daily dosing status (1 = taken, 0 = missed):",
        "tools.t3_day_label": "Day {n}",
        "tools.t3_gen_btn": "Generate protection curve",
        "tools.t3_conc_name": "Drug concentration",
        "tools.t3_threshold": "Threshold",
        "tools.t3_xaxis": "Days",
        "tools.t3_yaxis": "Concentration (ng/mL)",
        "tools.t3_protected": "Protected days",
    },
}


def t(key, lang=DEFAULT_LANG):
    """返回 ``key`` 在 ``lang`` 下的译文。

    三级回退：目标语言 → 中文（DEFAULT_LANG）→ key 本身。
    这样未翻译的条目会自动回落到中文，便于增量翻译而不破坏页面。
    """
    if lang not in TRANSLATIONS:
        lang = DEFAULT_LANG
    table = TRANSLATIONS[lang]
    if key in table:
        return table[key]
    # 回退到中文
    zh = TRANSLATIONS[DEFAULT_LANG]
    if key in zh:
        return zh[key]
    # 最终回退：返回 key 本身，便于发现漏翻
    return key


def available_keys(lang=DEFAULT_LANG):
    """返回某语言已登记的全部 key（测试/校验用）。"""
    return set(TRANSLATIONS.get(lang, {}).keys())


def missing_keys(lang):
    """返回 ``lang`` 相对中文基准缺失的 key 集合（用于翻译完整性校验）。"""
    return available_keys(DEFAULT_LANG) - available_keys(lang)
