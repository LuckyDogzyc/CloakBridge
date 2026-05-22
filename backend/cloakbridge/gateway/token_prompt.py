from __future__ import annotations

import re
from collections import defaultdict


GROUP_SURFACE_PATTERN = re.compile(r"^\[\[(?P<type>[A-Z_]+):(?P<group>\d{3})#(?P<surface>\d{3})\]\]$")
IP_PATTERN = re.compile(r"^\[\[IP:(?P<prefix>[A-Z.]+)\.(?P<host>\d{3})(?:/\d{1,2})?\]\]$")
IP_RANGE_PATTERN = re.compile(r"^\[\[IP_RANGE:(?P<prefix>[A-Z.]+)\.(?P<start>\d{3})-(?P<end>\d{3})\]\]$")


def build_token_handling_prompt(token_map: dict[str, str]) -> str:
    project_lines = _project_group_lines(token_map)
    ip_lines = _ip_relationship_lines(token_map)
    dynamic_sections = "\n".join(section for section in [project_lines, ip_lines] if section)

    return "\n".join(
        [
            "你正在处理经过本地脱敏的内容。所有形如 [[TYPE:ID#SURFACE]]、[[IP:...]]、"
            "[[IP_PREFIX:...]]、[[IP_RANGE:...]] 的标记都是不可修改的安全标记。",
            "",
            "规则：",
            "1. 不要翻译、改写、拆分、合并、补全或重新编号任何 [[...]] 标记。",
            "2. 如果原文中已有带 # 的标记，例如 [[PRJ:001#002]]，回复中引用该对象时应优先原样使用同一个完整标记。",
            "3. 带相同实体组编号的标记表示同一个对象的不同原始写法。你可以理解它们属于同一个对象，但输出中尽量保留输入中对应的完整标记。",
            "4. 只有在需要泛指整个项目、且无法判断应该使用哪个原始写法时，才可以使用不带 # 的组级标记，例如 [[PRJ:001]]。",
            "5. 不要创造新的项目、公司、人员、IP 标记。除非用户明确要求生成新条目，否则只能使用输入中已经出现过的标记。",
            "6. 对 IP 相关标记，必须保持结构：单个地址 [[IP:A.B.C.004]]，前缀 [[IP_PREFIX:A.B.C.*]]，范围 [[IP_RANGE:A.B.C.018-090]]。",
            "7. 当执行比较、筛选、统计、缺失检查、范围判断时，可以利用标记中的组关系和 IP 结构，但输出时仍必须保持标记原样。",
            "8. 如果你不确定某个标记该如何处理，保留原标记，不要猜测真实含义。",
            "",
            dynamic_sections,
        ]
    ).strip()


def _project_group_lines(token_map: dict[str, str]) -> str:
    grouped: dict[str, list[str]] = defaultdict(list)
    for token in token_map:
        match = GROUP_SURFACE_PATTERN.match(token)
        if not match:
            continue
        group_token = f"[[{match.group('type')}:{match.group('group')}]]"
        grouped[group_token].append(token)

    lines = []
    for group_token, surface_tokens in sorted(grouped.items()):
        if len(surface_tokens) < 2:
            continue
        lines.append(f"- {' 与 '.join(sorted(surface_tokens))} 属于同一项目 {group_token}。输出时优先使用输入中出现的完整标记。")
    if not lines:
        return ""
    return "本次任务中的项目实体关系：\n" + "\n".join(lines)


def _ip_relationship_lines(token_map: dict[str, str]) -> str:
    lines: list[str] = []
    prefixes = {match.group("prefix") for token in token_map if (match := IP_PATTERN.match(token))}
    for token in sorted(token_map):
        ip_match = IP_PATTERN.match(token)
        if ip_match:
            prefix_token = f"[[IP_PREFIX:{ip_match.group('prefix')}.*]]"
            lines.append(f"- {token} 属于 {prefix_token}。")
        range_match = IP_RANGE_PATTERN.match(token)
        if range_match:
            prefix_token = f"[[IP_PREFIX:{range_match.group('prefix')}.*]]"
            lines.append(f"- {token} 属于 {prefix_token}。")

    for prefix in sorted(prefixes):
        prefix_token = f"[[IP_PREFIX:{prefix}.*]]"
        if prefix_token in token_map:
            continue
        lines.append(f"- {prefix_token} 是本次任务中可用于前缀筛选的派生标记。")

    if not lines:
        return ""
    return "本次任务中的 IP 结构关系：\n" + "\n".join(lines)
