"""Streamlit页面接入框架。

用法：
1. 将本文件与 screening.py、intervention.py、database.py、api_contracts.py 放入原项目 src/。
2. 在 app.py 中导入 `render_new_service_loop_pages`。
3. 在首页增加五大模块按钮，并在页面分发处调用对应页面函数。
"""

import streamlit as st
import requests
import os
from datetime import datetime

from api_contracts import API_ENDPOINTS, TERMINAL_PROTOCOL
from database import SCHEMA_SQL
from intervention import InterventionInput, build_intervention_plan, next_followup_dates
from screening import ScreeningInput, recommend_hiv_testing


def render_loop_header(title: str, subtitle: str) -> None:
    st.markdown(f"## {title}")
    st.caption(subtitle)




def render_risk_assessment_center() -> None:
    render_loop_header("风险评估中心", "保留原有PrEP风险评估，并扩展HIV暴露、行为风险、PrEP适用性、PEP紧急和KAP认知评估入口。")
    tabs = st.tabs(["暴露风险", "行为风险", "PrEP适用性", "PEP紧急", "KAP认知"])
    with tabs[0]:
        st.write("评估暴露方式、暴露次数、安全套使用、伴侣状态、STI情况和PrEP保护状态。")
        st.info("原项目的进阶风险模型仍保留在“高级工具”页面，可继续用于单次/累积风险估算。")
    with tabs[1]:
        st.write("评估伴侣数量、安全套频率、近期STI、共用针具等行为维度，输出风险等级和主要风险解释。")
    with tabs[2]:
        st.write("结合风险评分、检测结果、肾功能、乙肝状态和重复暴露模式，判断是否建议进入PrEP启动评估。")
        if st.button("进入原PrEP启动决策中心", use_container_width=True):
            st.session_state.page = "PrEP启动决策中心"
            st.rerun()
    with tabs[3]:
        st.write("判断是否处于72小时PEP窗口，并给出紧急程度和线下转诊建议。")
    with tabs[4]:
        st.write("评估HIV、PrEP、PEP、防艾知识与态度行为，作为健康教育分层依据。")
    if st.button("进入原有PrEP评估页面", use_container_width=True):
        st.session_state.page = "评估"
        st.rerun()

def render_screening_center() -> None:
    render_loop_header("检测筛查中心", "根据风险等级、暴露时间、症状和PrEP/PEP状态，推荐HIV尿液、血液或核酸检测。")
    c1, c2 = st.columns(2)
    with c1:
        risk = st.selectbox("风险等级", ["低", "中", "高", "极高"], index=1)
        hours = st.number_input("距离最近暴露小时数", 0, 365 * 24, 168)
        symptoms = st.checkbox("存在发热、皮疹、咽痛、淋巴结肿大等症状")
    with c2:
        on_prep = st.checkbox("正在使用PrEP")
        on_pep = st.checkbox("正在或近期使用PEP")
    rec = recommend_hiv_testing(ScreeningInput(risk, hours, symptoms, on_prep, on_pep))
    st.metric("推荐检测方式", rec["recommended_method"])
    st.write(f"适用场景：{rec['scenario']}")
    st.info(rec["timing_advice"])
    st.caption(rec["window_period_note"])


def _terminal_result_from_lines(c_line: bool, t_line: bool) -> str:
    if not c_line:
        return "无效"
    if t_line:
        return "阳性提示"
    return "阴性"


def _terminal_result_explanation(result: str) -> str:
    if result == "阴性":
        return "本次检测未见阳性提示。若仍处于窗口期，阴性结果不能完全排除近期感染风险。"
    if result == "阳性提示":
        return "本次结果提示可能存在感染风险，需要尽快到医疗机构或疾控机构进行建议复检与咨询医生。"
    return "本次试纸控制线异常或图像识别质量不足，结果不可用于判断，请重新检测或前往机构检测。"


def render_terminal_upload_simulator() -> None:
    render_loop_header("终端模拟上传", "模拟安全预哨所终端上传C线/T线识别结果，并保存到当前会话。")
    st.caption("图片识别只作为初判；多联检卡、截图、倾斜拍摄需要确认C/T线后再上传。用户结果展示页不会显示JSON。")

    manual_tab, image_tab = st.tabs(["手动模拟上传", "图片识别上传"])

    with manual_tab:
        col1, col2 = st.columns(2)
        with col1:
            device_id = st.text_input("设备编号", value="ZYHS-001", key="manual_device_id")
            c_line = st.radio("C线", ["存在", "不存在"], horizontal=True, key="manual_c_line") == "存在"
            t_line = st.radio("T线", ["不存在", "存在"], horizontal=True, key="manual_t_line") == "存在"
        with col2:
            c_line_score = st.slider("C线识别置信度", 0.0, 1.0, 0.86 if c_line else 0.08, 0.01, key="manual_c_score")
            t_line_score = st.slider("T线识别置信度", 0.0, 1.0, 0.82 if t_line else 0.12, 0.01, key="manual_t_score")

        result = _terminal_result_from_lines(c_line, t_line)
        st.subheader("系统自动判读")
        if result == "阴性":
            st.success("C线有、T线无：阴性")
        elif result == "阳性提示":
            st.error("C线有、T线有：阳性提示")
        else:
            st.warning("C线无：无效")

        if st.button("上传检测结果", type="primary", use_container_width=True, key="manual_upload_result"):
            record = {
                "device_id": device_id,
                "c_line": c_line,
                "t_line": t_line,
                "result": result,
                "c_line_score": float(c_line_score),
                "t_line_score": float(t_line_score),
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "source": "manual",
            }
            st.session_state.latest_terminal_result = record
            st.session_state.terminal_upload_records = st.session_state.get("terminal_upload_records", [])
            st.session_state.terminal_upload_records.append(record)
            st.success("检测结果已保存到当前会话，可前往用户结果展示页查看健康建议。")

    with image_tab:
        st.write("上传试纸图片后，系统先进行OpenCV初判；请确认C线/T线后再上传最终结果。")
        device_id = st.text_input("设备编号", value="ZYHS-001", key="image_device_id")
        test_item = st.selectbox("检测项目", ["HIV1/2", "HCV", "TP", "HBsAg"], index=0, key="image_test_item")
        uploaded = st.file_uploader("上传试纸图片", type=["png", "jpg", "jpeg"], key="strip_image_upload")

        if uploaded is not None:
            st.image(uploaded, caption="已上传试纸图片", width="stretch")

            if st.button("OpenCV初判", type="secondary", use_container_width=True, key="image_precheck_result"):
                import os
                import tempfile

                suffix = os.path.splitext(uploaded.name)[1] or ".png"
                tmp_path = None
                try:
                    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                        tmp.write(uploaded.getbuffer())
                        tmp_path = tmp.name

                    from strip_recognition import analyze_strip_image

                    analysis = analyze_strip_image(tmp_path, test_item=test_item)
                    st.session_state.pending_image_analysis = {
                        "device_id": device_id,
                        "test_item": test_item,
                        "initial_result": analysis.get("result", "无效"),
                        "auto_c_line": bool(analysis.get("c_line", False)),
                        "auto_t_line": bool(analysis.get("t_line", False)),
                        "c_line_score": float(analysis.get("c_line_score", 0.0)),
                        "t_line_score": float(analysis.get("t_line_score", 0.0)),
                    }
                    auto_record = {
                        "device_id": device_id,
                        "test_item": test_item,
                        "c_line": bool(analysis.get("c_line", False)),
                        "t_line": bool(analysis.get("t_line", False)),
                        "result": analysis.get("result", "无效"),
                        "c_line_score": float(analysis.get("c_line_score", 0.0)),
                        "t_line_score": float(analysis.get("t_line_score", 0.0)),
                        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "source": "opencv_auto",
                    }
                    st.session_state.latest_terminal_result = auto_record
                    st.session_state.terminal_upload_records = st.session_state.get("terminal_upload_records", [])
                    st.session_state.terminal_upload_records.append(auto_record)
                    st.info("已完成OpenCV自动识别并同步到用户结果展示页。如自动结果不符合所选项目，请在下方确认C线/T线并覆盖上传。")
                except Exception as exc:
                    st.error(f"图片初判未完成：{exc}")
                    st.caption("如提示 OpenCV 不可用，请先安装 requirements.txt 中的 opencv-python。")
                finally:
                    if tmp_path and os.path.exists(tmp_path):
                        os.remove(tmp_path)

            pending = st.session_state.get("pending_image_analysis")
            if pending:
                st.subheader("确认后上传")
                st.caption("注意：多联检卡请只按所选项目这一行确认。例如 HIV1/2 阴性应为 C线存在、T线不存在。")
                initial = pending.get("initial_result", "无效")
                st.write(f"OpenCV初判：{initial}（仅供参考）")
                default_c = "存在" if pending.get("auto_c_line", initial in ["阴性", "阳性提示"]) else "不存在"
                default_t = "存在" if pending.get("auto_t_line", initial == "阳性提示") else "不存在"
                c_confirm = st.radio("确认C线", ["存在", "不存在"], index=0 if default_c == "存在" else 1, horizontal=True, key="image_confirm_c")
                t_confirm = st.radio("确认T线", ["不存在", "存在"], index=1 if default_t == "存在" else 0, horizontal=True, key="image_confirm_t")
                final_c = c_confirm == "存在"
                final_t = t_confirm == "存在"
                final_result = _terminal_result_from_lines(final_c, final_t)

                if final_result == "阴性":
                    st.success("确认结果：C线有、T线无，阴性")
                elif final_result == "阳性提示":
                    st.error("确认结果：C线有、T线有，阳性提示")
                else:
                    st.warning("确认结果：C线无，无效")

                if st.button("确认并上传检测结果", type="primary", use_container_width=True, key="image_confirm_upload"):
                    record = {
                        "device_id": pending.get("device_id", device_id),
                        "test_item": pending.get("test_item", test_item),
                        "c_line": final_c,
                        "t_line": final_t,
                        "result": final_result,
                        "c_line_score": float(pending.get("c_line_score", 0.0)),
                        "t_line_score": float(pending.get("t_line_score", 0.0)),
                        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "source": "image_confirmed",
                        "initial_result": initial,
                    }
                    st.session_state.latest_terminal_result = record
                    st.session_state.terminal_upload_records = st.session_state.get("terminal_upload_records", [])
                    st.session_state.terminal_upload_records.append(record)
                    st.success("确认后的检测结果已保存，可前往用户结果展示页查看健康建议。")

    n1, n2 = st.columns(2)
    with n1:
        if st.button("查看用户结果展示", use_container_width=True, key="go_user_result_from_upload"):
            st.session_state.page = "安全预哨所智能终端"
            st.rerun()
    with n2:
        if st.button("继续上传下一次检测", use_container_width=True, key="continue_terminal_upload"):
            st.session_state.pending_image_analysis = None
            st.rerun()

def render_safety_terminal_center() -> None:
    render_loop_header("安全预哨所智能终端", "后台接收终端结构化数据；前台只向用户展示可理解、可行动的检测结果。")
    user_tab, api_tab, cv_tab = st.tabs(["用户结果展示", "后台上传接口", "终端流程与OpenCV"])

    with user_tab:
        latest = st.session_state.get("latest_terminal_result")
        if not latest:
            st.info("暂无终端上传结果。请先进入“终端模拟上传”页面生成一次检测结果。")
            if st.button("进入终端模拟上传", type="primary", use_container_width=True):
                st.session_state.page = "终端模拟上传"
                st.rerun()
            return

        result = latest.get("result", "无效")
        st.caption("用户前台不显示JSON字段，仅展示检测结论、解释和下一步行动。")
        if result == "阴性":
            st.success("检测结果：阴性")
        elif result == "阳性提示":
            st.error("检测结果：阳性提示")
        else:
            st.warning("检测结果：无效")

        st.write(f"结果解释：{_terminal_result_explanation(result)}")
        st.caption(f"检测时间：{latest.get('created_at', '未知')}")

        c1, c2 = st.columns(2)
        with c1:
            risk = st.selectbox("风险评估等级", ["低", "中", "高", "极高"], index=1)
            hours = st.number_input("距离最近可能暴露小时数", 0, 365 * 24, 168)
        with c2:
            prep_status = st.selectbox("PrEP状态", ["未使用", "每日口服", "按需服用", "长效注射"])
            pep_status = st.selectbox("PEP状态", ["未使用", "使用中", "已完成"])

        plan = build_intervention_plan(
            InterventionInput(
                risk_level=risk,
                hours_since_exposure=hours,
                test_result=result,
                prep_status=prep_status,
                pep_status=pep_status,
            )
        )
        st.subheader("结合风险评估后的PrEP/PEP建议")
        st.write(f"PrEP建议：{plan['prep_advice']}")
        st.write(f"PEP建议：{plan['pep_advice']}")

        st.subheader("就医或复查建议")
        if result == "阳性提示":
            st.write("请尽快前往感染科、皮肤性病科、疾控/VCT门诊或具备HIV建议复检服务能力的机构咨询医生。")
        elif result == "无效":
            st.write("建议立即重新检测；如近期存在高风险暴露，优先选择医疗机构血液检测或核酸检测。")
        else:
            st.write(plan["testing_advice"]["timing_advice"])
        st.caption(plan["testing_advice"]["window_period_note"])

        n1, n2, n3 = st.columns(3)
        with n1:
            if st.button("重新模拟上传", use_container_width=True):
                st.session_state.page = "终端模拟上传"
                st.rerun()
        with n2:
            if st.button("寻找医疗服务机构", use_container_width=True):
                st.session_state.page = "医疗服务中心"
                st.rerun()
        with n3:
            if st.button("重新评估风险", use_container_width=True):
                st.session_state.page = "风险评估中心"
                st.rerun()

    with api_tab:
        st.subheader("第一层：终端后台上传接口")
        st.write("终端上传给平台的是结构化数据，用于后台判读、存储、干预规则计算和转诊分流；用户前台不直接显示这些字段。")
        st.table([
            {"字段": "device_id", "类型": "string", "示例": "ZYHS-001", "用途": "终端设备编号"},
            {"字段": "c_line", "类型": "boolean", "示例": "true", "用途": "是否识别到C线"},
            {"字段": "t_line", "类型": "boolean", "示例": "false", "用途": "是否识别到T线"},
            {"字段": "result", "类型": "string", "示例": "阴性", "用途": "后台判读结果"},
            {"字段": "c_line_score", "类型": "number", "示例": "0.86", "用途": "C线识别置信度"},
            {"字段": "t_line_score", "类型": "number", "示例": "0.12", "用途": "T线识别置信度"},
            {"字段": "created_at", "类型": "datetime", "示例": "2026-06-09 14:30:00", "用途": "检测创建时间"},
        ])
        st.write("接口：POST /api/v1/terminal/test-results")
        st.write(f"传输：{TERMINAL_PROTOCOL['transport']}")
        st.write(f"鉴权：{TERMINAL_PROTOCOL['auth']}")
        st.write(f"重试：{TERMINAL_PROTOCOL['retry']}")
        st.write(f"隐私：{TERMINAL_PROTOCOL['privacy']}")

    with cv_tab:
        st.subheader("终端工作流程")
        st.markdown(
            """
```mermaid
flowchart LR
    A[插入检测试纸] --> B[点击检测按钮]
    B --> C[摄像头自动拍照]
    C --> D[OpenCV识别试纸区域]
    D --> E[读取C线/T线]
    E --> F{结果判断}
    F -->|C线有/T线无| N[阴性]
    F -->|C线有/T线有| P[阳性提示]
    F -->|C线缺失| X[无效]
    N --> U[后台上传结构化数据]
    P --> U
    X --> U
```
"""
        )
        st.subheader("OpenCV模块架构")
        st.code("图像采集 -> 灰度化/降噪 -> ROI定位 -> C/T线投影分析 -> 阈值判断 -> 结构化结果", language="text")


def render_terminal_report_viewer() -> None:
    render_loop_header("检测报告中心", "默认展示平台匿名统计；完整报告仅用户本人或获得临时授权的医生可查看。")

    def _api_candidates() -> list[str]:
        candidates: list[str] = []
        env_value = os.getenv("TERMINAL_API_BASE_URL")
        if env_value:
            candidates.append(env_value)
        try:
            secret_value = st.secrets.get("TERMINAL_API_BASE_URL", None)
            if secret_value:
                candidates.append(secret_value)
        except Exception:
            pass
        candidates.extend(["https://prep-guardian-api-production.up.railway.app", "http://172.20.10.2:8000", "http://192.168.137.1:8000", "http://127.0.0.1:8000"])
        unique: list[str] = []
        for item in candidates:
            cleaned = str(item).rstrip("/")
            if cleaned and cleaned not in unique:
                unique.append(cleaned)
        return unique

    payload = None
    endpoint = ""
    errors: list[str] = []
    for api_base in _api_candidates():
        endpoint = f"{api_base}/api/v1/terminal/test-results"
        try:
            resp = requests.get(endpoint, timeout=4)
            resp.raise_for_status()
            payload = resp.json()
            break
        except Exception as exc:
            errors.append(f"{endpoint} -> {exc}")

    st.caption(f"当前读取接口：{endpoint or '未连接'}")
    if st.button("刷新报告列表", type="primary", use_container_width=True):
        st.rerun()

    if payload is None:
        st.warning("暂时无法连接终端 API 服务。")
        st.code("uvicorn src.terminal_api:app --host 0.0.0.0 --port 8000", language="bash")
        with st.expander("连接尝试记录"):
            st.code("\n".join(errors), language="text")
        return

    reports = payload.get("reports", [])
    statistics = payload.get("statistics", {})

    st.subheader("平台匿名统计")
    s1, s2, s3, s4, s5 = st.columns(5)
    s1.metric("今日上传报告数", statistics.get("today_upload_count", 0))
    s2.metric("阴性参考数量", statistics.get("negative_reference_count", 0))
    s3.metric("阳性疑似数量", statistics.get("positive_suspected_count", 0))
    s4.metric("无效检测数量", statistics.get("invalid_count", 0))
    s5.metric("高风险提示数量", statistics.get("high_risk_count", 0))
    st.caption("平台后台默认只显示匿名汇总数据，不显示用户完整检测报告。")

    if not reports:
        st.info("暂无 ESP32 上传数据。请在终端点击“上传至知药护身平台”。")
        return

    st.subheader("平台后台最小化记录")
    table_rows = [
        {
            "匿名报告编号": item.get("anonymous_report_id", item.get("report_id", "-")),
            "接收时间": item.get("detection_time", item.get("received_at", "-")),
            "数据类型": "终端检测辅助报告",
            "权限": item.get("visibility", "仅用户本人可见"),
            "详情状态": "已隐藏，需用户本人或临时授权",
        }
        for item in reports
    ]
    st.dataframe(table_rows, use_container_width=True, hide_index=True)

    selected_id = st.selectbox(
        "选择报告编号",
        [item.get("anonymous_report_id", item.get("report_id", "-")) for item in reports],
    )
    report = next((item for item in reports if item.get("anonymous_report_id", item.get("report_id")) == selected_id), reports[0])

    st.markdown("**访问控制模拟**")
    st.info("当前为平台后台视图：只能看到匿名编号和汇总统计。完整报告需要用户本人确认，或用户主动生成临时授权后由医生查看。")
    access_key = f"report_access_{selected_id}"
    auth_info = st.session_state.get(f"auth_result_{selected_id}") or report.get("authorization", {})

    c1, c2, c3 = st.columns([1, 1, 2])
    with c1:
        if st.button("模拟用户本人查看", use_container_width=True, key=f"owner_{selected_id}"):
            st.session_state[access_key] = "owner"
    with c2:
        if st.button("生成临时授权", use_container_width=True, key=f"auth_{selected_id}"):
            auth_endpoint = endpoint.rsplit("/api/v1/terminal/test-results", 1)[0]
            auth_url = f"{auth_endpoint}/api/v1/terminal/reports/{selected_id}/authorize"
            try:
                auth_resp = requests.post(auth_url, timeout=4)
                auth_resp.raise_for_status()
                auth_info = auth_resp.json().get("authorization", {})
            except Exception:
                auth_info = {
                    "authorized": True,
                    "auth_id": "AUTH-2026-001",
                    "valid_for": "24小时",
                    "message": "请将报告编号或二维码提供给正规医疗机构医生参考",
                }
            st.session_state[f"auth_result_{selected_id}"] = auth_info
    with c3:
        typed_auth = st.text_input("医生授权码", placeholder="输入 AUTH-2026-001 后可模拟医生查看", key=f"auth_code_{selected_id}")
        if typed_auth.strip() and typed_auth.strip() == (auth_info or {}).get("auth_id"):
            st.session_state[access_key] = "doctor"

    if auth_info.get("authorized"):
        st.success("授权状态：已生成临时授权")
        st.write(f"授权编号：{auth_info.get('auth_id', 'AUTH-2026-001')}")
        st.write(f"有效期：{auth_info.get('valid_for', '24小时')}")
        st.info(auth_info.get("message", "请将报告编号或二维码提供给正规医疗机构医生参考"))

    if st.button("生成分享二维码", use_container_width=True, key=f"qr_{selected_id}"):
        st.session_state[f"qr_visible_{selected_id}"] = True
    if st.session_state.get(f"qr_visible_{selected_id}"):
        st.success("已生成模拟分享二维码。")
        st.code(f"QR-MOCK\n报告编号：{selected_id}\n授权说明：仅用户主动分享后可用于医疗转介辅助", language="text")

    access_mode = st.session_state.get(access_key)
    if not access_mode:
        st.warning("完整报告已隐藏：检测记录默认只有用户本人可见。平台后台仅保留匿名统计和最小化记录。")
        masked = {
            "匿名报告编号": selected_id,
            "检测时间": report.get("detection_time", "-"),
            "权限": report.get("visibility", "仅用户本人可见"),
            "辅助判断": "已隐藏",
            "风险等级": "已隐藏",
            "设备编号": "已隐藏",
            "C线状态": "已隐藏",
            "T线状态": "已隐藏",
            "下一步建议": "已隐藏",
        }
        st.json(masked)
        st.info("本报告仅用于健康科普、风险评估与检测辅助，不构成医学判断、用药建议或医疗决策依据。如需专业医疗服务，请前往正规医疗机构咨询医生。")
        return

    st.subheader("匿名检测辅助报告")
    if access_mode == "owner":
        st.success("访问身份：用户本人（模拟）")
    else:
        st.success("访问身份：已获临时授权的医生/机构（模拟）")

    d1, d2, d3, d4 = st.columns(4)
    d1.metric("匿名报告编号", report.get("anonymous_report_id", report.get("report_id", "-")))
    d2.metric("权限", report.get("visibility", "仅用户本人可见"))
    d3.metric("辅助判断", report.get("assist_result_label", report.get("assist_result", "-")))
    d4.metric("风险等级", report.get("risk_level_label", report.get("risk_level", "-")))

    left, right = st.columns([1, 1])
    with left:
        st.write(f"检测时间：{report.get('detection_time', '-')}")
        st.write(f"设备编号：{report.get('device_id', '-')}")
        st.write(f"C线状态：{report.get('c_line_status', '-')}")
        st.write(f"T线状态：{report.get('t_line_status', '-')}")
        st.write(f"试纸状态：{report.get('test_status_label', report.get('test_status', '-'))}")
    with right:
        st.markdown("**下一步建议**")
        for idx, step in enumerate(report.get("next_steps", []), start=1):
            st.write(f"{idx}. {step}")

    st.markdown("**附近医疗机构推荐**")
    institutions = report.get("nearby_medical_institutions", [])
    if institutions:
        st.dataframe(institutions, use_container_width=True, hide_index=True)
    else:
        st.info("暂无机构推荐。")

    st.markdown("**隐私与权限设计**")
    privacy_policy = report.get("privacy_policy", {})
    st.write(privacy_policy.get("user_default_visibility", "检测记录默认只有用户自己可见"))
    st.write(privacy_policy.get("platform_backend", "平台后台只显示匿名统计，不直接暴露个人身份"))
    st.write(privacy_policy.get("doctor_access", "医生/机构只有在用户主动授权后才能查看报告"))

    st.info(report.get("compliance_notice", "本报告仅用于健康科普、风险评估与检测辅助，不构成医学判断、用药建议或医疗决策依据。如需专业医疗服务，请前往正规医疗机构咨询医生。"))
def render_intervention_center() -> None:
    render_loop_header("智能干预中心", "整合风险评估、检测结果、PrEP服药情况和PEP时效，生成个体化干预建议。")
    c1, c2 = st.columns(2)
    with c1:
        risk = st.selectbox("风险等级", ["低", "中", "高", "极高"], index=2)
        hours = st.number_input("距离暴露小时数", 0, 365 * 24, 24)
        test_result = st.selectbox("检测结果", ["未检测", "阴性", "阳性提示", "无效"])
    with c2:
        prep_status = st.selectbox("PrEP服药情况", ["未使用", "每日口服", "按需服用", "长效注射"])
        adherence = st.selectbox("依从性", ["未知", "规律", "偶有漏服", "频繁漏服"])
        pep_status = st.selectbox("PEP状态", ["未使用", "使用中", "已完成"])
        symptoms = st.checkbox("存在急性感染样症状")
    plan = build_intervention_plan(InterventionInput(risk, hours, test_result, prep_status, adherence, pep_status, symptoms))
    st.write(f"风险等级：{plan['risk_level']}")
    st.write(f"检测建议：{plan['testing_advice']['recommended_method']} - {plan['testing_advice']['timing_advice']}")
    st.write(f"PrEP建议：{plan['prep_advice']}")
    st.write(f"PEP建议：{plan['pep_advice']}")
    st.write(f"用药提醒：{plan['medication_reminder']}")
    st.info(plan["pharmacy_guidance"])
    st.table(next_followup_dates())


def render_medical_service_center() -> None:
    render_loop_header("医疗服务中心", "按所在地推荐HIV检测机构、社区医院、PrEP/PEP门诊和疾控机构。")
    city = st.text_input("城市", "昆明")
    service = st.multiselect(
        "需要的服务",
        ["HIV检测机构", "社区医院", "PrEP门诊", "PEP门诊", "疾控机构"],
        default=["HIV检测机构", "PEP门诊"],
    )
    demo_sites = [
        {"机构": "市级疾控中心VCT门诊", "类型": "疾控机构/HIV检测", "城市": city, "建议": "匿名咨询、HIV检测与转介"},
        {"机构": "综合医院感染科/皮肤性病科", "类型": "PEP门诊/PrEP评估", "城市": city, "建议": "72小时内暴露、PEP评估和基线检查"},
        {"机构": "社区卫生服务中心", "类型": "社区医院/随访", "城市": city, "建议": "常规检测、健康教育和长期随访"},
    ]
    st.table(demo_sites)
    st.caption(f"筛选服务：{', '.join(service) if service else '全部'}。后续可接入地图API、疾控目录或医院号源接口。")


def render_platform_design_center() -> None:
    render_loop_header("系统架构与接口设计", "架构图、流程图、ER图、API接口、数据库表结构和扩展规划。")
    tabs = st.tabs(["API接口", "数据库表", "目录结构"])
    with tabs[0]:
        st.table(API_ENDPOINTS)
    with tabs[1]:
        st.code(SCHEMA_SQL, language="sql")
    with tabs[2]:
        st.code(
            """
prep_guardian/
  src/
    app.py
    risk_assessment.py
    screening.py
    intervention.py
    database.py
    strip_recognition.py
    api_contracts.py
    app_pages_framework.py
  docs/
    prep_guardian_refactor_design.md
""",
            language="text",
        )


def render_new_service_loop_pages(page: str) -> bool:
    """返回True表示已处理该页面；False表示交回原app.py继续处理。"""
    pages = {
        "风险评估中心": render_risk_assessment_center,
        "检测筛查中心": render_screening_center,
        "安全预哨所智能终端": render_safety_terminal_center,
        "终端模拟上传": render_terminal_upload_simulator,
        "终端上传报告": render_terminal_report_viewer,
        "检测报告中心": render_terminal_report_viewer,
        "智能干预中心": render_intervention_center,
        "医疗服务中心": render_medical_service_center,
        "系统架构与接口设计": render_platform_design_center,
    }
    if page in pages:
        if st.button("返回首页", key=f"service_loop_back_home_{page}"):
            st.session_state.page = "home"
            st.rerun()
        pages[page]()
        return True
    return False






