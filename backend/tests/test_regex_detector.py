from cloakbridge.detection.regex_detector import RegexDetector
from cloakbridge.domain.entities import EntityType


def test_regex_detector_finds_ip_email_phone_and_project_code():
    text = "项目PRJ-2026-042联系人test@example.com，电话13800138000，内网10.18.2.4。"

    findings = RegexDetector().detect(text)
    found = {(finding.entity_type, finding.text) for finding in findings}

    assert (EntityType.PROJECT_CODE, "PRJ-2026-042") in found
    assert (EntityType.EMAIL, "test@example.com") in found
    assert (EntityType.MOBILE_PHONE, "13800138000") in found
    assert (EntityType.IP_ADDRESS, "10.18.2.4") in found


def test_regex_detector_finds_url_and_domain():
    text = "访问https://secure.example.com/path，备用域名internal.example.cn。"

    findings = RegexDetector().detect(text)
    found = {(finding.entity_type, finding.text) for finding in findings}

    assert (EntityType.URL, "https://secure.example.com/path") in found
    assert (EntityType.DOMAIN, "internal.example.cn") in found
