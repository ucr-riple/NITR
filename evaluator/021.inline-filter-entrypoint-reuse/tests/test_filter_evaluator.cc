#include <fstream>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

#include <gtest/gtest.h>

#include "filter_clause.h"
#include "filter_parser.h"
#include "filter_rule.h"
#include "filter_validation.h"

namespace {

struct StructuredValidCase {
  std::string field;
  std::string op;
  std::string value;
  std::string expected_field;
  std::string expected_op;
  std::string value_kind;
  std::string expected_value;
};

struct InlineValidCase {
  std::string input;
  std::string expected_field;
  std::string expected_op;
  std::string value_kind;
  std::string expected_value;
};

struct InlineInvalidCase {
  std::string input;
  std::string error_code;
};

struct ParityCase {
  std::string input;
  std::string field;
  std::string op;
  std::string value;
  bool expect_ok;
  std::string expected_field;
  std::string expected_op;
  std::string value_kind;
  std::string expected_value;
  std::string error_code;
};

std::vector<std::string> SplitCsvLine(const std::string& line) {
  std::vector<std::string> parts;
  std::string current;
  std::istringstream input(line);
  while (std::getline(input, current, ',')) {
    parts.push_back(current);
  }
  return parts;
}

std::vector<std::vector<std::string>> ReadCsvRows(const std::string& path) {
  std::ifstream input(path);
  if (!input.is_open()) {
    throw std::runtime_error("failed to open fixture: " + path);
  }

  std::vector<std::vector<std::string>> rows;
  std::string line;
  bool first_line = true;
  while (std::getline(input, line)) {
    if (line.empty()) {
      continue;
    }
    if (first_line) {
      first_line = false;
      continue;
    }
    rows.push_back(SplitCsvLine(line));
  }
  return rows;
}

nitr::case021::FilterErrorCode ParseErrorCodeName(const std::string& text) {
  if (text == "invalid_field") {
    return nitr::case021::FilterErrorCode::kInvalidField;
  }
  if (text == "invalid_operator") {
    return nitr::case021::FilterErrorCode::kInvalidOperator;
  }
  if (text == "invalid_value") {
    return nitr::case021::FilterErrorCode::kInvalidValue;
  }
  throw std::runtime_error("unknown error code name: " + text);
}

void ExpectRule(const nitr::case021::FilterRule& rule,
                const std::string& expected_field,
                const std::string& expected_op,
                const std::string& expected_kind,
                const std::string& expected_value) {
  EXPECT_EQ(nitr::case021::ToString(rule.field), expected_field);
  EXPECT_EQ(nitr::case021::ToString(rule.op), expected_op);

  if (expected_kind == "integer") {
    EXPECT_EQ(rule.value.kind, nitr::case021::FilterValueKind::kInteger);
    EXPECT_EQ(std::to_string(rule.value.number), expected_value);
  } else {
    EXPECT_EQ(rule.value.kind, nitr::case021::FilterValueKind::kText);
    EXPECT_EQ(rule.value.text, expected_value);
  }
}

std::string DataPath(const std::string& file_name) {
  return std::string(EVALUATOR_DATA_DIR) + "/" + file_name;
}

TEST(FilterEvaluatorTests, StructuredValidCases) {
  for (const auto& row : ReadCsvRows(DataPath("structured_valid.csv"))) {
    ASSERT_GE(row.size(), 7u) << "structured_valid.csv must have 7+ columns";
    StructuredValidCase test_case{row[0], row[1], row[2], row[3],
                                  row[4], row[5], row[6]};
    const nitr::case021::FilterParseResult result =
        nitr::case021::ParseFilterClause(nitr::case021::FilterClause{
            test_case.field, test_case.op, test_case.value});
    EXPECT_TRUE(result.ok) << "structured parse should succeed for "
                          << test_case.field;
    if (!result.ok) {
      continue;
    }
    ExpectRule(result.rule, test_case.expected_field, test_case.expected_op,
              test_case.value_kind, test_case.expected_value);
  }
}

TEST(FilterEvaluatorTests, InlineValidCases) {
  for (const auto& row : ReadCsvRows(DataPath("inline_valid.csv"))) {
    ASSERT_GE(row.size(), 5u) << "inline_valid.csv must have 5+ columns";
    InlineValidCase test_case{row[0], row[1], row[2], row[3], row[4]};
    const nitr::case021::FilterParseResult result =
        nitr::case021::ParseInlineFilter(test_case.input);
    EXPECT_TRUE(result.ok) << "inline parse should succeed for "
                          << test_case.input;
    if (!result.ok) {
      continue;
    }
    ExpectRule(result.rule, test_case.expected_field, test_case.expected_op,
              test_case.value_kind, test_case.expected_value);
  }
}

TEST(FilterEvaluatorTests, InlineInvalidCases) {
  for (const auto& row : ReadCsvRows(DataPath("inline_invalid.csv"))) {
    ASSERT_GE(row.size(), 2u) << "inline_invalid.csv must have 2+ columns";
    InlineInvalidCase test_case{row[0], row[1]};
    const nitr::case021::FilterParseResult result =
        nitr::case021::ParseInlineFilter(test_case.input);
    EXPECT_FALSE(result.ok) << "inline parse should fail for "
                           << test_case.input;
    if (result.ok) {
      continue;
    }
    EXPECT_EQ(result.error.code, ParseErrorCodeName(test_case.error_code))
        << "unexpected error code for " + test_case.input;
  }
}

TEST(FilterEvaluatorTests, ParityBetweenStructuredAndInlineParsing) {
  for (const auto& row : ReadCsvRows(DataPath("parity_cases.csv"))) {
    ASSERT_GE(row.size(), 10u) << "parity_cases.csv must have 10+ columns";
    ParityCase test_case{row[0], row[1], row[2], row[3], row[4] == "true",
                         row[5], row[6], row[7], row[8], row[9]};

    const nitr::case021::FilterParseResult structured =
        nitr::case021::ParseFilterClause(nitr::case021::FilterClause{
            test_case.field, test_case.op, test_case.value});
    const nitr::case021::FilterParseResult inline_result =
        nitr::case021::ParseInlineFilter(test_case.input);

    EXPECT_EQ(structured.ok, test_case.expect_ok)
        << "structured parity baseline mismatch for " << test_case.input;
    EXPECT_EQ(inline_result.ok, structured.ok)
        << "inline/structured success mismatch for " << test_case.input;

    if (test_case.expect_ok) {
      if (structured.ok && inline_result.ok) {
        EXPECT_EQ(nitr::case021::ToString(inline_result.rule),
                  nitr::case021::ToString(structured.rule))
            << "inline/structured rule mismatch for " << test_case.input;
        ExpectRule(inline_result.rule, test_case.expected_field,
                  test_case.expected_op, test_case.value_kind,
                  test_case.expected_value);
      }
      continue;
    }

    if (!structured.ok && !inline_result.ok) {
      const nitr::case021::FilterErrorCode expected =
          ParseErrorCodeName(test_case.error_code);
      EXPECT_EQ(structured.error.code, expected)
          << "structured error mismatch for " << test_case.input;
      EXPECT_EQ(inline_result.error.code, structured.error.code)
          << "inline/structured error mismatch for " << test_case.input;
    }
  }
}
}  // namespace
