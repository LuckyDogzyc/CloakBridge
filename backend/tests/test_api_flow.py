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


def test_api_uses_alias_groups_to_keep_related_project_surfaces_in_one_entity():
    client = TestClient(app)
    text = "西调工程服务器10.18.2.18已上线，西调搬迁清单缺少10.18.2.90。"
    findings = [
        {"text": "西调工程", "entity_type": "PROJECT", "start": 0, "end": 4, "source": "manual", "confidence": 1},
        {"text": "10.18.2.18", "entity_type": "IP_ADDRESS", "start": 7, "end": 17, "source": "regex", "confidence": 1},
        {"text": "西调搬迁", "entity_type": "PROJECT", "start": 21, "end": 25, "source": "manual", "confidence": 1},
        {"text": "10.18.2.90", "entity_type": "IP_ADDRESS", "start": 29, "end": 39, "source": "regex", "confidence": 1},
    ]

    sanitized = client.post(
        "/api/sanitize-text",
        json={
            "text": text,
            "findings": findings,
            "alias_groups": [
                {
                    "entity_type": "PROJECT",
                    "canonical": "西调工程",
                    "aliases": ["西调工程", "西调2025工程", "西调搬迁", "2025资源补强"],
                }
            ],
        },
    )

    assert sanitized.status_code == 200
    payload = sanitized.json()
    assert payload["sanitized_text"] == (
        "[[PRJ:001#001]]服务器[[IP:A.B.C.018]]已上线，[[PRJ:001#003]]清单缺少[[IP:A.B.C.090]]。"
    )
    assert payload["token_map"]["[[PRJ:001]]"] == "西调工程"


def test_api_persists_alias_groups_in_local_store(tmp_path, monkeypatch):
    monkeypatch.setenv("CLOAKBRIDGE_DATA_DIR", str(tmp_path))
    client = TestClient(app)

    created = client.post(
        "/api/alias-groups",
        json={
            "entity_type": "PROJECT",
            "canonical": "西调工程",
            "aliases": ["西调工程", "西调2025工程", "西调搬迁", "2025资源补强"],
            "scope": "project",
        },
    )

    assert created.status_code == 200
    assert created.json()["aliases"] == ["西调工程", "西调2025工程", "西调搬迁", "2025资源补强"]

    listed = client.get("/api/alias-groups")
    assert listed.status_code == 200
    assert listed.json()["alias_groups"] == [created.json()]
    assert (tmp_path / "cloakbridge.sqlite").exists()


def test_api_saves_lists_and_tests_local_model_configs(tmp_path, monkeypatch):
    monkeypatch.setenv("CLOAKBRIDGE_DATA_DIR", str(tmp_path))
    client = TestClient(app)

    created = client.post(
        "/api/model-configs",
        json={
            "name": "MiniMax 生产网关",
            "provider": "minimax",
            "model": "MiniMax-M1",
            "base_url": "https://api.minimax.chat/v1",
            "api_key": "sk-local-secret",
        },
    )

    assert created.status_code == 200
    payload = created.json()
    assert payload["name"] == "MiniMax 生产网关"
    assert payload["masked_api_key"] == "sk-****cret"
    assert "api_key" not in payload

    database_bytes = (tmp_path / "cloakbridge.sqlite").read_bytes()
    assert b"sk-local-secret" not in database_bytes

    listed = client.get("/api/model-configs")
    assert listed.status_code == 200
    assert listed.json()["model_configs"] == [payload]

    tested = client.post(f"/api/model-configs/{payload['id']}/test")
    assert tested.status_code == 200
    assert tested.json()["ok"] is True
