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


def test_regex_detector_url_stops_at_chinese_punctuation():
    findings = RegexDetector().detect("访问https://secure.example.com/path：后续")

    assert (EntityType.URL, "https://secure.example.com/path") in {
        (finding.entity_type, finding.text) for finding in findings
    }
    assert all("后续" not in finding.text for finding in findings)


def test_regex_detector_url_stops_at_ascii_punctuation():
    findings = RegexDetector().detect("访问https://secure.example.com/path!后续")
    found = {(finding.entity_type, finding.text) for finding in findings}

    assert (EntityType.URL, "https://secure.example.com/path") in found
    assert all("后续" not in finding.text for finding in findings)


def test_regex_detector_suppresses_domain_inside_url_but_keeps_standalone_domain():
    findings = RegexDetector().detect(
        "访问https://secure.example.com/path，备用secure.example.com。"
    )
    found = [(finding.entity_type, finding.text) for finding in findings]

    assert found.count((EntityType.URL, "https://secure.example.com/path")) == 1
    assert found.count((EntityType.DOMAIN, "secure.example.com")) == 1


def test_regex_detector_rejects_invalid_ip_octets_and_cidr():
    findings = RegexDetector().detect(
        "错误IP 256.0.0.1、999.1.1.1、10.0.0.1/99，正确10.0.0.1/24"
    )
    found = {(finding.entity_type, finding.text) for finding in findings}

    assert (EntityType.IP_ADDRESS, "10.0.0.1/24") in found
    assert (EntityType.IP_ADDRESS, "256.0.0.1") not in found
    assert (EntityType.IP_ADDRESS, "999.1.1.1") not in found
    assert (EntityType.IP_ADDRESS, "10.0.0.1/99") not in found
