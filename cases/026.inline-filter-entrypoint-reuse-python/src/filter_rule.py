from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class FilterField(str, Enum):
    STATUS = "status"
    PRIORITY = "priority"
    OWNER = "owner"


class FilterOperator(str, Enum):
    EQUALS = "="
    GREATER_EQUAL = ">="
    CONTAINS = ":"


class FilterValueKind(str, Enum):
    TEXT = "text"
    INTEGER = "integer"


class FilterErrorCode(str, Enum):
    INVALID_FIELD = "invalid_field"
    INVALID_OPERATOR = "invalid_operator"
    INVALID_VALUE = "invalid_value"


@dataclass(frozen=True)
class FilterError:
    code: FilterErrorCode
    message: str


@dataclass(frozen=True)
class FilterValue:
    kind: FilterValueKind
    text: str
    number: int


@dataclass(frozen=True)
class FilterRule:
    field: FilterField
    op: FilterOperator
    value: FilterValue

    def __str__(self) -> str:
        if self.value.kind == FilterValueKind.INTEGER:
            value_text = str(self.value.number)
        else:
            value_text = self.value.text
        return f"{self.field.value} {self.op.value} {value_text}"
