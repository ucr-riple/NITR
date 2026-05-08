#include <cstdlib>
#include <fstream>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>

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

bool Check(bool condition, const std::string& message) {
  if (!condition) {
    std::cerr << message << "\n";
    return false;
  }
  return true;
}

bool ExpectRule(const nitr::case021::FilterRule& rule,
                const std::string& expected_field,
                const std::string& expected_op,
                const std::string& expected_kind,
                const std::string& expected_value, const std::string& context) {
  bool ok = true;
  ok = Check(nitr::case021::ToString(rule.field) == expected_field,
             context + ": unexpected field") &&
       ok;
  ok = Check(nitr::case021::ToString(rule.op) == expected_op,
             context + ": unexpected operator") &&
       ok;

  if (expected_kind == "integer") {
    ok = Check(rule.value.kind == nitr::case021::FilterValueKind::kInteger,
               context + ": expected integer value") &&
         ok;
    ok = Check(std::to_string(rule.value.number) == expected_value,
               context + ": unexpected integer value") &&
         ok;
  } else {
    ok = Check(rule.value.kind == nitr::case021::FilterValueKind::kText,
               context + ": expected text value") &&
         ok;
    ok = Check(rule.value.text == expected_value,
               context + ": unexpected text value") &&
         ok;
  }

  return ok;
}

std::string DataPath(const std::string& file_name) {
  return std::string(EVALUATOR_DATA_DIR) + "/" + file_name;
}

bool RunStructuredValidTests() {
  bool ok = true;
  for (const auto& row : ReadCsvRows(DataPath("structured_valid.csv"))) {
    StructuredValidCase test_case{row[0], row[1], row[2], row[3],
                                  row[4], row[5], row[6]};
    const nitr::case021::FilterParseResult result =
        nitr::case021::ParseFilterClause(nitr::case021::FilterClause{
            test_case.field, test_case.op, test_case.value});
    ok = Check(result.ok,
               "structured parse should succeed for " + test_case.field) &&
         ok;
    if (!result.ok) {
      continue;
    }
    ok =
        ExpectRule(result.rule, test_case.expected_field, test_case.expected_op,
                   test_case.value_kind, test_case.expected_value,
                   "structured case " + test_case.field) &&
        ok;
  }
  return ok;
}

bool RunInlineValidTests() {
  bool ok = true;
  for (const auto& row : ReadCsvRows(DataPath("inline_valid.csv"))) {
    InlineValidCase test_case{row[0], row[1], row[2], row[3], row[4]};
    const nitr::case021::FilterParseResult result =
        nitr::case021::ParseInlineFilter(test_case.input);
    ok = Check(result.ok,
               "inline parse should succeed for " + test_case.input) &&
         ok;
    if (!result.ok) {
      continue;
    }
    ok =
        ExpectRule(result.rule, test_case.expected_field, test_case.expected_op,
                   test_case.value_kind, test_case.expected_value,
                   "inline case " + test_case.input) &&
        ok;
  }
  return ok;
}

bool RunInlineInvalidTests() {
  bool ok = true;
  for (const auto& row : ReadCsvRows(DataPath("inline_invalid.csv"))) {
    InlineInvalidCase test_case{row[0], row[1]};
    const nitr::case021::FilterParseResult result =
        nitr::case021::ParseInlineFilter(test_case.input);
    ok = Check(!result.ok, "inline parse should fail for " + test_case.input) &&
         ok;
    if (result.ok) {
      continue;
    }
    ok = Check(result.error.code == ParseErrorCodeName(test_case.error_code),
               "unexpected error code for " + test_case.input) &&
         ok;
  }
  return ok;
}

bool RunParityTests() {
  bool ok = true;
  for (const auto& row : ReadCsvRows(DataPath("parity_cases.csv"))) {
    ParityCase test_case{row[0], row[1], row[2], row[3], row[4] == "true",
                         row[5], row[6], row[7], row[8], row[9]};

    const nitr::case021::FilterParseResult structured =
        nitr::case021::ParseFilterClause(nitr::case021::FilterClause{
            test_case.field, test_case.op, test_case.value});
    const nitr::case021::FilterParseResult inline_result =
        nitr::case021::ParseInlineFilter(test_case.input);

    ok = Check(structured.ok == test_case.expect_ok,
               "structured parity baseline mismatch for " + test_case.input) &&
         ok;
    ok = Check(inline_result.ok == structured.ok,
               "inline/structured success mismatch for " + test_case.input) &&
         ok;

    if (test_case.expect_ok) {
      if (structured.ok && inline_result.ok) {
        ok = Check(nitr::case021::ToString(inline_result.rule) ==
                       nitr::case021::ToString(structured.rule),
                   "inline/structured rule mismatch for " + test_case.input) &&
             ok;
        ok = ExpectRule(inline_result.rule, test_case.expected_field,
                        test_case.expected_op, test_case.value_kind,
                        test_case.expected_value,
                        "parity case " + test_case.input) &&
             ok;
      }
      continue;
    }

    if (!structured.ok && !inline_result.ok) {
      const nitr::case021::FilterErrorCode expected =
          ParseErrorCodeName(test_case.error_code);
      ok = Check(structured.error.code == expected,
                 "structured error mismatch for " + test_case.input) &&
           ok;
      ok = Check(inline_result.error.code == structured.error.code,
                 "inline/structured error mismatch for " + test_case.input) &&
           ok;
    }
  }
  return ok;
}

}  // namespace

int main() {
  bool ok = true;
  ok = RunStructuredValidTests() && ok;
  ok = RunInlineValidTests() && ok;
  ok = RunInlineInvalidTests() && ok;
  ok = RunParityTests() && ok;
  return ok ? EXIT_SUCCESS : EXIT_FAILURE;
}
