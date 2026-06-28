"""API接口与安全预哨所终端通信协议设计。"""

API_ENDPOINTS = [
    {"method": "POST", "path": "/api/v1/assessments", "purpose": "提交风险评估并返回风险等级与建议"},
    {"method": "POST", "path": "/api/v1/screening/recommend", "purpose": "根据风险、暴露时间、症状和PrEP/PEP状态推荐检测方式"},
    {"method": "POST", "path": "/api/v1/terminal/heartbeat", "purpose": "终端心跳、版本、摄像头和网络状态上报"},
    {"method": "POST", "path": "/api/v1/terminal/test-results", "purpose": "上传试纸识别结果、C/T线分值和图片证据"},
    {"method": "POST", "path": "/api/v1/interventions", "purpose": "生成检测、PrEP、PEP和药学干预建议"},
    {"method": "GET", "path": "/api/v1/medical-sites", "purpose": "按城市、机构类型和紧急程度查询转诊机构"},
]

TERMINAL_PROTOCOL = {
    "transport": "HTTPS REST优先；弱网场景可使用MQTT作为补充通道",
    "auth": "terminal_id + API key签名；服务端按终端白名单校验",
    "retry": "本地SQLite队列缓存，指数退避重试，成功后标记uploaded",
    "privacy": "图片脱敏存储；用户身份使用匿名码或一次性session_id",
    "payload": {
        "terminal_id": "SAFE-SENTRY-001",
        "session_id": "uuid",
        "test_type": "HIV尿液检测",
        "sample_type": "urine",
        "result": "阴性/阳性提示/无效",
        "c_line_score": 0.0,
        "t_line_score": 0.0,
        "image_sha256": "...",
        "captured_at": "ISO-8601",
    },
}
