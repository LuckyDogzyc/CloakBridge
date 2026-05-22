from __future__ import annotations

import re
from dataclasses import dataclass, field

from cloakbridge.domain.entities import EntityType, Finding


READABLE_PROJECT_ALIASES = ("xxx项目", "yyy项目", "zzz项目")
READABLE_IP_ALIASES = ("aa.bb.cc.dd", "ee.ff.gg.hh", "ii.jj.kk.ll")
STRUCTURED_FAMILY_CODES = {
    EntityType.PROJECT: "PRJ",
    EntityType.COMPANY: "ORG",
    EntityType.PERSON: "PER",
    EntityType.DEPARTMENT: "DEPT",
    EntityType.SERVER: "SRV",
    EntityType.HOSTNAME: "HOST",
    EntityType.DEVICE: "DEV",
}
ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"


@dataclass
class TokenMap:
    original_to_token: dict[tuple[str, str], str] = field(default_factory=dict)
    token_to_original: dict[str, str] = field(default_factory=dict)
    counters: dict[str, int] = field(default_factory=dict)
    replacement_style: str = "placeholder"
    octet_aliases: dict[str, str] = field(default_factory=dict)

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

    def register_alias_group(
        self,
        entity_type: EntityType,
        canonical: str,
        aliases: list[str],
    ) -> str:
        code = self._structured_entity_code(entity_type)
        group_index = self.counters.get(code, 0) + 1
        self.counters[code] = group_index
        group_token = f"[[{code}:{group_index:03d}]]"
        self.token_to_original[group_token] = canonical

        for surface_index, alias in enumerate(aliases, start=1):
            token = f"[[{code}:{group_index:03d}#{surface_index:03d}]]"
            self.original_to_token[(entity_type.token_family, alias)] = token
            self.token_to_original[token] = alias
        return group_token

    def _allocate_token(self, finding: Finding, family: str, index: int) -> str:
        if self.replacement_style != "readable":
            if self.replacement_style == "structured":
                return self._allocate_structured_token(finding)
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

    def _allocate_structured_token(self, finding: Finding) -> str:
        if finding.entity_type is EntityType.IP_ADDRESS:
            return f"[[IP:{self._pseudonymize_ip(finding.text)}]]"
        if finding.entity_type is EntityType.IP_PREFIX:
            return f"[[IP_PREFIX:{self._pseudonymize_prefix(finding.text)}.*]]"
        if finding.entity_type is EntityType.IP_RANGE:
            return f"[[IP_RANGE:{self._pseudonymize_range(finding.text)}]]"
        if finding.entity_type in STRUCTURED_FAMILY_CODES:
            self.register_alias_group(finding.entity_type, canonical=finding.text, aliases=[finding.text])
            return self.original_to_token[(finding.entity_type.token_family, finding.text)]
        return f"[[{finding.entity_type.token_family}:{self.counters.get(finding.entity_type.token_family, 1):03d}]]"

    def _structured_entity_code(self, entity_type: EntityType) -> str:
        return STRUCTURED_FAMILY_CODES.get(entity_type, entity_type.token_family)

    def _pseudonymize_ip(self, value: str) -> str:
        ip, separator, cidr = value.partition("/")
        parts = ip.split(".")
        prefix = ".".join(self._octet_alias(position, part) for position, part in enumerate(parts[:3]))
        host = f"{int(parts[3]):03d}"
        if separator:
            return f"{prefix}.{host}/{cidr}"
        return f"{prefix}.{host}"

    def _pseudonymize_prefix(self, value: str) -> str:
        parts = value.split(".")
        return ".".join(self._octet_alias(position, part) for position, part in enumerate(parts[:3]))

    def _pseudonymize_range(self, value: str) -> str:
        prefix, start, end = self._parse_ip_range(value)
        return f"{self._pseudonymize_prefix(prefix)}.{start:03d}-{end:03d}"

    def _parse_ip_range(self, value: str) -> tuple[str, int, int]:
        start_ip, end_text = value.split("-", 1)
        start_parts = start_ip.split(".")
        prefix = ".".join(start_parts[:3])
        start = int(start_parts[3])
        end = int(end_text.split(".")[-1])
        return prefix, start, end

    def _octet_alias(self, position: int, value: str) -> str:
        if value not in self.octet_aliases:
            self.octet_aliases[value] = self._letters_for_index(len(self.octet_aliases) + 1)
        return self.octet_aliases[value]

    def _letters_for_index(self, index: int) -> str:
        result = ""
        while index:
            index -= 1
            result = ALPHABET[index % len(ALPHABET)] + result
            index //= len(ALPHABET)
        return result

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
