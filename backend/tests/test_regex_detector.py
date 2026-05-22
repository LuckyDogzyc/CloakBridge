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


def test_regex_detector_url_stops_before_chinese_description_without_punctuation():
    findings = RegexDetector().detect(
        "http://epay.12306.cn/pay/wapResponseC2银行端配置修改建行将支付平台的支付结果通知地址"
    )
    found = {(finding.entity_type, finding.text) for finding in findings}

    assert (EntityType.URL, "http://epay.12306.cn/pay/wapResponseC2") in found
    assert all("银行端" not in finding.text for finding in findings)


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


def test_regex_detector_finds_ip_prefix_and_host_range_requests():
    findings = RegexDetector().detect("把10.18.2开头的都列出来，再处理10.18.2.18-90。")
    found = {(finding.entity_type, finding.text) for finding in findings}

    assert (EntityType.IP_PREFIX, "10.18.2") in found
    assert (EntityType.IP_RANGE, "10.18.2.18-90") in found


def test_regex_detector_finds_numeric_project_names_without_catching_test_numbers():
    findings = RegexDetector().detect("12306备用域名实施方案，12306APP，测试123456")
    found = {(finding.entity_type, finding.text) for finding in findings}

    assert (EntityType.PROJECT, "12306备用域名") in found
    assert (EntityType.PROJECT, "12306") in found
    assert all(finding.text != "123456" for finding in findings)


def test_regex_detector_finds_numeric_cn_domains_even_when_docx_text_is_concatenated():
    findings = RegexDetector().detect("12306.cnmobile.12306.cn和12306-backup.cn")
    found = {(finding.entity_type, finding.text) for finding in findings}

    assert (EntityType.DOMAIN, "12306.cn") in found
    assert (EntityType.DOMAIN, "12306-backup.cn") in found
