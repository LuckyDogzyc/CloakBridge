from __future__ import annotations

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
        restored = text
        for token, original in sorted(
            self.token_to_original.items(), key=lambda item: -len(item[0])
        ):
            restored = restored.replace(token, original)
        return restored
