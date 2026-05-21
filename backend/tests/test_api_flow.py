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
    assert payload["sanitized_text"] == "<PROJECT_001>服务器<IP_001>"

    restored = client.post(
        "/api/restore-text",
        json={"sanitized_text": "分析<PROJECT_001>和<IP_001>", "token_map": payload["token_map"]},
    )
    assert restored.status_code == 200
    assert restored.json()["restored_text"] == "分析华东三期项目和10.18.2.4"
