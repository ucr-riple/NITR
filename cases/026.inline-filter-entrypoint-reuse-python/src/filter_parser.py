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
    return FilterParseResult(
        ok=False,
        rule=_make_empty_rule(),
        error=FilterError(
            code=FilterErrorCode.INVALID_OPERATOR,
            message=f"inline parsing not implemented: {normalized}",
        ),
    )
