from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class EntityType(StrEnum):
    PERSON = "PERSON"
    COMPANY = "COMPANY"
    DEPARTMENT = "DEPARTMENT"
    PROJECT = "PROJECT"
    PROJECT_CODE = "PROJECT_CODE"
    IP_ADDRESS = "IP_ADDRESS"
    HOSTNAME = "HOSTNAME"
    DOMAIN = "DOMAIN"
    URL = "URL"
    EMAIL = "EMAIL"
    MOBILE_PHONE = "MOBILE_PHONE"
    LANDLINE = "LANDLINE"
    NATIONAL_ID = "NATIONAL_ID"
    BANK_CARD = "BANK_CARD"
    CREDIT_CODE = "CREDIT_CODE"
    CONTRACT = "CONTRACT"
    DRAWING = "DRAWING"
    DEVICE = "DEVICE"
    SERVER = "SERVER"
    CUSTOM = "CUSTOM"

    @property
    def token_family(self) -> str:
        return {
            EntityType.IP_ADDRESS: "IP",
            EntityType.MOBILE_PHONE: "PHONE",
            EntityType.LANDLINE: "PHONE",
            EntityType.NATIONAL_ID: "ID",
        }.get(self, self.value)


@dataclass(frozen=True, slots=True)
class Finding:
    text: str
    entity_type: EntityType
    start: int
    end: int
    source: str
    confidence: float

    def overlaps(self, other: "Finding") -> bool:
        return self.start < other.end and other.start < self.end
