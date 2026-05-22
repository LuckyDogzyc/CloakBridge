from fastapi.testclient import TestClient

from cloakbridge.main import app


def test_api_analyzes_sanitizes_and_restores_text():
    client = TestClient(app)

    analysis = client.post(
        "/api/analyze-text",
        json={
            "text": "华东三期项目服务器10.18.2.4",
            "dictionary": [{"text": "华东三期项目", "entity_type": "PROJECT", "scope": "project"}],
        },
    )
    assert analysis.status_code == 200
    findings = analysis.json()["findings"]
    assert any(item["text"] == "华东三期项目" for item in findings)
    assert any(item["text"] == "10.18.2.4" for item in findings)

    sanitized = client.post(
        "/api/sanitize-text",
        json={"text": "华东三期项目服务器10.18.2.4", "findings": findings},
    )
    assert sanitized.status_code == 200
    payload = sanitized.json()
    assert payload["sanitized_text"] == "[[PRJ:001#001]]服务器[[IP:A.B.C.004]]"
    assert "优先原样使用同一个完整标记" in payload["token_prompt"]

    restored = client.post(
        "/api/restore-text",
        json={"sanitized_text": "分析[[PRJ:001#001]]和[[IP:A.B.C.004]]", "token_map": payload["token_map"]},
    )
    assert restored.status_code == 200
    assert restored.json()["restored_text"] == "分析华东三期项目和10.18.2.4"


def test_api_defaults_to_chinese_project_detection_and_readable_replacements():
    client = TestClient(app)

    analysis = client.post(
        "/api/analyze-text",
        json={"text": "西调工程项目服务器10.18.2.4 测试123456", "dictionary": []},
    )

    assert analysis.status_code == 200
    findings = analysis.json()["findings"]
    assert any(item["text"] == "西调工程项目" and item["entity_type"] == "PROJECT" for item in findings)
    assert any(item["text"] == "10.18.2.4" and item["entity_type"] == "IP_ADDRESS" for item in findings)
    assert all(item["text"] != "123456" for item in findings)

    sanitized = client.post(
        "/api/sanitize-text",
        json={"text": "西调工程项目服务器10.18.2.4 测试123456", "findings": findings},
    )

    assert sanitized.status_code == 200
    assert sanitized.json()["sanitized_text"] == "[[PRJ:001#001]]服务器[[IP:A.B.C.004]] 测试123456"


def test_api_preserves_ip_prefix_and_range_structure_in_sanitized_requests():
    client = TestClient(app)

    analysis = client.post(
        "/api/analyze-text",
        json={"text": "把10.18.2开头的都列出来，再处理10.18.2.18-90。", "dictionary": []},
    )
    assert analysis.status_code == 200
    findings = analysis.json()["findings"]
    assert any(item["text"] == "10.18.2" and item["entity_type"] == "IP_PREFIX" for item in findings)
    assert any(item["text"] == "10.18.2.18-90" and item["entity_type"] == "IP_RANGE" for item in findings)

    sanitized = client.post(
        "/api/sanitize-text",
        json={"text": "把10.18.2开头的都列出来，再处理10.18.2.18-90。", "findings": findings},
    )

    assert sanitized.status_code == 200
    assert sanitized.json()["sanitized_text"] == (
        "把[[IP_PREFIX:A.B.C.*]]开头的都列出来，再处理[[IP_RANGE:A.B.C.018-090]]。"
    )
