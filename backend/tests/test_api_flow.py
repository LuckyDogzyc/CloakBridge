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
    assert payload["sanitized_text"] == "xxx项目服务器aa.bb.cc.dd"

    restored = client.post(
        "/api/restore-text",
        json={"sanitized_text": "分析xxx项目和aa.bb.cc.dd", "token_map": payload["token_map"]},
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
    assert sanitized.json()["sanitized_text"] == "xxx项目服务器aa.bb.cc.dd 测试123456"
