from __future__ import annotations

from dataclasses import dataclass

from src.filter_clause import FilterClause
from src.filter_rule import (
    FilterError,
    FilterErrorCode,
    FilterField,
    FilterOperator,
    FilterRule,
    FilterValue,
    FilterValueKind,
)
from src.filter_validation import (
    parse_field_name,
    parse_operator_token,
    parse_value_for_field,
)


@dataclass(frozen=True)
class FilterParseResult:
    ok: bool
    rule: FilterRule
    error: FilterError


def _make_empty_rule() -> FilterRule:
    return FilterRule(
        field=FilterField.STATUS,
        op=FilterOperator.EQUALS,
        value=FilterValue(kind=FilterValueKind.TEXT, text="", number=0),
    )


def _is_operator_char(ch: str) -> bool:
    return not ch.isalnum() and not ch.isspace() and ch != "_"


def _has_inline_operator_remainder(value: FilterValue) -> bool:
    if value.kind != FilterValueKind.TEXT:
        return False
    normalized = value.text.strip()
    return ">=" in normalized or "=" in normalized or ":" in normalized


def parse_filter_clause(clause: FilterClause) -> FilterParseResult:
    ok, field, error = parse_field_name(clause.field)
    if not ok or field is None:
        return FilterParseResult(ok=False, rule=_make_empty_rule(), error=error)

    ok, op, error = parse_operator_token(clause.op)
    if not ok or op is None:
        return FilterParseResult(ok=False, rule=_make_empty_rule(), error=error)

    ok, value, error = parse_value_for_field(field, op, clause.value)
    if not ok or value is None:
        return FilterParseResult(ok=False, rule=_make_empty_rule(), error=error)

    return FilterParseResult(
        ok=True,
        rule=FilterRule(field=field, op=op, value=value),
        error=FilterError(code=FilterErrorCode.INVALID_FIELD, message=""),
    )


def parse_inline_filter(text: str) -> FilterParseResult:
    normalized = text.strip()

    field_end = 0
    while (
        field_end < len(normalized)
        and not normalized[field_end].isspace()
        and not _is_operator_char(normalized[field_end])
    ):
        field_end += 1

    cursor = field_end
    while cursor < len(normalized) and normalized[cursor].isspace():
        cursor += 1

    op_start = cursor
    if cursor < len(normalized) and _is_operator_char(normalized[cursor]):
        while cursor < len(normalized) and _is_operator_char(normalized[cursor]):
            cursor += 1

    field = normalized[:field_end]
    op = normalized[op_start:cursor]

    while cursor < len(normalized) and normalized[cursor].isspace():
        cursor += 1

    result = parse_filter_clause(
        FilterClause(field=field, op=op, value=normalized[cursor:])
    )
    if not result.ok:
        return result

    if _has_inline_operator_remainder(result.rule.value):
        invalid_value = result.rule.value.text
        return FilterParseResult(
            ok=False,
            rule=_make_empty_rule(),
            error=FilterError(
                code=FilterErrorCode.INVALID_VALUE,
                message=f"invalid value: {invalid_value}",
            ),
        )

    return result
