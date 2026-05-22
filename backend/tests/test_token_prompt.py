from cloakbridge.gateway.token_prompt import build_token_handling_prompt


def test_token_prompt_tells_external_ai_to_preserve_surface_tokens_and_use_group_only_for_generic_reference():
    prompt = build_token_handling_prompt(
        {
            "[[PRJ:001]]": "西调工程",
            "[[PRJ:001#001]]": "西调工程",
            "[[PRJ:001#002]]": "西调搬迁",
            "[[IP:A.B.C.018]]": "10.18.2.18",
            "[[IP_RANGE:A.B.C.018-090]]": "10.18.2.18-90",
        }
    )

    assert "不要翻译、改写、拆分、合并、补全或重新编号任何 [[...]] 标记" in prompt
    assert "优先原样使用同一个完整标记" in prompt
    assert "[[PRJ:001#001]] 与 [[PRJ:001#002]] 属于同一项目 [[PRJ:001]]" in prompt
    assert "只有在需要泛指整个项目" in prompt
    assert "[[IP:A.B.C.018]] 属于 [[IP_PREFIX:A.B.C.*]]" in prompt
    assert "[[IP_RANGE:A.B.C.018-090]]" in prompt
