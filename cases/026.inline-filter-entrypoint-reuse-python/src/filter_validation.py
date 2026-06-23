from __future__ import annotations

from src.filter_rule import (
    FilterError,
    FilterErrorCode,
    FilterField,
    FilterOperator,
    FilterValue,
    FilterValueKind,
)


def _trim(text: str) -> str:
    return text.strip()


def _make_error(code: FilterErrorCode, detail: str) -> FilterError:
    if code == FilterErrorCode.INVALID_FIELD:
        return FilterError(code=code, message=f"invalid field: {detail}")
    if code == FilterErrorCode.INVALID_OPERATOR:
        return FilterError(code=code, message=f"invalid operator: {detail}")
    return FilterError(code=code, message=f"invalid value: {detail}")


def _is_integer(text: str) -> bool:
    return bool(text) and text.isdigit()


def parse_field_name(text: str) -> tuple[bool, FilterField | None, FilterError | None]:
    normalized = _trim(text)
    if normalized == "status":
        return True, FilterField.STATUS, None
    if normalized == "priority":
        return True, FilterField.PRIORITY, None
    if normalized == "owner":
        return True, FilterField.OWNER, None
    return False, None, _make_error(FilterErrorCode.INVALID_FIELD, normalized)


def parse_operator_token(
    text: str,
) -> tuple[bool, FilterOperator | None, FilterError | None]:
    normalized = _trim(text)
    if normalized == "=":
        return True, FilterOperator.EQUALS, None
    if normalized == ">=":
        return True, FilterOperator.GREATER_EQUAL, None
    if normalized == ":":
        return True, FilterOperator.CONTAINS, None
    return False, None, _make_error(FilterErrorCode.INVALID_OPERATOR, normalized)


def parse_value_for_field(
    field: FilterField,
    op: FilterOperator,
    text: str,
) -> tuple[bool, FilterValue | None, FilterError | None]:
    normalized = _trim(text)
    if not normalized:
        return False, None, _make_error(FilterErrorCode.INVALID_VALUE, normalized)

    if field == FilterField.PRIORITY:
        if op == FilterOperator.CONTAINS:
            return False, None, _make_error(FilterErrorCode.INVALID_OPERATOR, op.value)
        if not _is_integer(normalized):
            return False, None, _make_error(FilterErrorCode.INVALID_VALUE, normalized)
        return (
            True,
            FilterValue(
                kind=FilterValueKind.INTEGER,
                text=normalized,
                number=int(normalized),
            ),
            None,
        )

    if op == FilterOperator.GREATER_EQUAL:
        return False, None, _make_error(FilterErrorCode.INVALID_OPERATOR, op.value)

    return (
        True,
        FilterValue(kind=FilterValueKind.TEXT, text=normalized, number=0),
        None,
    )
