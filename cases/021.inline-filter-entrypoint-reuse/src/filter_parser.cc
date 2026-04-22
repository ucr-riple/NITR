#include "filter_parser.h"

#include <cctype>
#include <string>

namespace {

nitr::case021::FilterRule MakeEmptyRule() {
  nitr::case021::FilterValue value;
  value.kind = nitr::case021::FilterValueKind::kText;
  value.text = "";
  value.number = 0;

  nitr::case021::FilterRule rule;
  rule.field = nitr::case021::FilterField::kStatus;
  rule.op = nitr::case021::FilterOperator::kEquals;
  rule.value = value;
  return rule;
}

std::string Trim(const std::string& text) {
  std::size_t start = 0;
  while (start < text.size() &&
         std::isspace(static_cast<unsigned char>(text[start])) != 0) {
    ++start;
  }

  std::size_t end = text.size();
  while (end > start &&
         std::isspace(static_cast<unsigned char>(text[end - 1])) != 0) {
    --end;
  }

  return text.substr(start, end - start);
}

bool IsOperatorChar(char ch) {
  return !std::isalnum(static_cast<unsigned char>(ch)) &&
         std::isspace(static_cast<unsigned char>(ch)) == 0 && ch != '_';
}

bool HasInlineOperatorRemainder(const nitr::case021::FilterValue& value) {
  if (value.kind != nitr::case021::FilterValueKind::kText) {
    return false;
  }

  const std::string normalized = Trim(value.text);
  if (normalized.find(">=") != std::string::npos) {
    return true;
  }

  return normalized.find('=') != std::string::npos ||
         normalized.find(':') != std::string::npos;
}

}  // namespace

namespace nitr::case021 {

FilterParseResult ParseFilterClause(const FilterClause& clause) {
  FilterParseResult result;
  result.ok = false;
  result.rule = MakeEmptyRule();
  result.error = FilterError{FilterErrorCode::kInvalidField, ""};

  FilterField field;
  if (!ParseFieldName(clause.field, &field, &result.error)) {
    return result;
  }

  FilterOperator op;
  if (!ParseOperatorToken(clause.op, &op, &result.error)) {
    return result;
  }

  FilterValue value;
  if (!ParseValueForField(field, op, clause.value, &value, &result.error)) {
    return result;
  }

  result.ok = true;
  result.rule.field = field;
  result.rule.op = op;
  result.rule.value = value;
  result.error = FilterError{FilterErrorCode::kInvalidField, ""};
  return result;
}

FilterParseResult ParseInlineFilter(const std::string& text) {
  const std::string normalized = Trim(text);

  std::size_t field_end = 0;
  while (field_end < normalized.size() &&
         std::isspace(static_cast<unsigned char>(normalized[field_end])) == 0 &&
         !IsOperatorChar(normalized[field_end])) {
    ++field_end;
  }

  std::size_t cursor = field_end;
  while (cursor < normalized.size() &&
         std::isspace(static_cast<unsigned char>(normalized[cursor])) != 0) {
    ++cursor;
  }

  const std::size_t op_start = cursor;
  if (cursor < normalized.size() && IsOperatorChar(normalized[cursor])) {
    while (cursor < normalized.size() && IsOperatorChar(normalized[cursor])) {
      ++cursor;
    }
  }

  const std::string field = normalized.substr(0, field_end);
  const std::string op = normalized.substr(op_start, cursor - op_start);

  while (cursor < normalized.size() &&
         std::isspace(static_cast<unsigned char>(normalized[cursor])) != 0) {
    ++cursor;
  }

  FilterParseResult result = ParseFilterClause(
      FilterClause{field, op, normalized.substr(cursor)});
  if (!result.ok) {
    return result;
  }

  if (HasInlineOperatorRemainder(result.rule.value)) {
    const std::string invalid_value = result.rule.value.text;
    result.ok = false;
    result.rule = MakeEmptyRule();
    result.error = FilterError{FilterErrorCode::kInvalidValue, invalid_value};
  }

  return result;
}

}  // namespace nitr::case021
