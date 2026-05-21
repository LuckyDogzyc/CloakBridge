from __future__ import annotations

import re
from dataclasses import dataclass, field

from cloakbridge.domain.entities import Finding


@dataclass
class TokenMap:
    original_to_token: dict[tuple[str, str], str] = field(default_factory=dict)
    token_to_original: dict[str, str] = field(default_factory=dict)
    counters: dict[str, int] = field(default_factory=dict)

    def token_for(self, finding: Finding) -> str:
        family = finding.entity_type.token_family
        key = (family, finding.text)
        if key in self.original_to_token:
            return self.original_to_token[key]
        next_index = self.counters.get(family, 0) + 1
        self.counters[family] = next_index
        token = f"<{family}_{next_index:03d}>"
        self.original_to_token[key] = token
        self.token_to_original[token] = finding.text
        return token

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
