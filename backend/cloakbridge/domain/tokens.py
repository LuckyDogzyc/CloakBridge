from __future__ import annotations

import re
from dataclasses import dataclass, field

from cloakbridge.domain.entities import EntityType, Finding


READABLE_PROJECT_ALIASES = ("xxx项目", "yyy项目", "zzz项目")
READABLE_IP_ALIASES = ("aa.bb.cc.dd", "ee.ff.gg.hh", "ii.jj.kk.ll")


@dataclass
class TokenMap:
    original_to_token: dict[tuple[str, str], str] = field(default_factory=dict)
    token_to_original: dict[str, str] = field(default_factory=dict)
    counters: dict[str, int] = field(default_factory=dict)
    replacement_style: str = "placeholder"

    def token_for(self, finding: Finding) -> str:
        family = finding.entity_type.token_family
        key = (family, finding.text)
        if key in self.original_to_token:
            return self.original_to_token[key]
        next_index = self.counters.get(family, 0) + 1
        self.counters[family] = next_index
        token = self._allocate_token(finding, family, next_index)
        self.original_to_token[key] = token
        self.token_to_original[token] = finding.text
        return token

    def _allocate_token(self, finding: Finding, family: str, index: int) -> str:
        if self.replacement_style != "readable":
            return f"<{family}_{index:03d}>"
        if finding.entity_type is EntityType.PROJECT:
            return self._alias(READABLE_PROJECT_ALIASES, index, f"项目{index}")
        if finding.entity_type is EntityType.IP_ADDRESS:
            return self._alias(READABLE_IP_ALIASES, index, f"ip.{index:02d}.xx.yy")
        if finding.entity_type is EntityType.COMPANY:
            return f"xxx公司" if index == 1 else f"公司{index}"
        if family == "PHONE":
            return f"电话{index}"
        if family == "ID":
            return f"编号{index}"
        return f"xxx{index}"

    def _alias(self, aliases: tuple[str, ...], index: int, fallback: str) -> str:
        if index <= len(aliases):
            return aliases[index - 1]
        return fallback

    def restore(self, text: str) -> str:
        if not self.token_to_original:
            return text
        pattern = re.compile(
            "|".join(
                re.escape(token)
                for token in sorted(self.token_to_original, key=len, reverse=True)
            )
        )
        return pattern.sub(lambda match: self.token_to_original[match.group(0)], text)
