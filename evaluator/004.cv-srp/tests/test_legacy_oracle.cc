#include <chrono>
#include <filesystem>
#include <fstream>
#include <sstream>
#include <string>

#include <gtest/gtest.h>

#include "legacy_monolith.h"

namespace {

std::string DataPath(const std::string& file_name) {
  const std::filesystem::path evaluator_dir =
      std::filesystem::path(__FILE__).parent_path();
  return (evaluator_dir / "../data" / file_name).string();
}

std::string TemporaryOutputPath(const std::string& suffix) {
  const auto now = std::chrono::high_resolution_clock::now().time_since_epoch();
  const auto micros =
      std::chrono::duration_cast<std::chrono::microseconds>(now).count();
  return (std::filesystem::temp_directory_path() /
          ("case004_legacy_oracle_" + suffix + "_" + std::to_string(micros) +
           ".json"))
      .string();
}

}  // namespace

TEST(LegacyOracle, OutputsForSimpleValidCase) {
  const std::string out = TemporaryOutputPath("simple");
  const auto code = nitr::case004::RunLegacyMonolith(
      DataPath("simple_ok.json"), out);
  EXPECT_TRUE(code == nitr::case004::ErrorCode::kOk ||
              code == nitr::case004::ErrorCode::kRejected ||
              code == nitr::case004::ErrorCode::kEstimationFailed);
  std::ifstream output(out);
  if (code == nitr::case004::ErrorCode::kOk ||
      code == nitr::case004::ErrorCode::kRejected) {
    EXPECT_TRUE(output.is_open());
    std::ostringstream buffer;
    buffer << output.rdbuf();
    EXPECT_NE(buffer.str().find("\"decision\""), std::string::npos);
  } else {
    EXPECT_FALSE(output.is_open());
  }
}

TEST(LegacyOracle, RejectCase) {
  const std::string out = TemporaryOutputPath("reject");
  const auto code = nitr::case004::RunLegacyMonolith(DataPath("reject_case.json"),
                                                    out);
  EXPECT_TRUE(code == nitr::case004::ErrorCode::kOk ||
              code == nitr::case004::ErrorCode::kRejected ||
              code == nitr::case004::ErrorCode::kEstimationFailed);
  std::ifstream output(out);
  if (code == nitr::case004::ErrorCode::kOk ||
      code == nitr::case004::ErrorCode::kRejected) {
    EXPECT_TRUE(output.is_open());
  } else {
    EXPECT_FALSE(output.is_open());
  }
}

TEST(LegacyOracle, EstimationFailedCase) {
  const std::string out = TemporaryOutputPath("estimation_failed");
  const auto code =
      nitr::case004::RunLegacyMonolith(DataPath("estimation_failed.json"), out);
  EXPECT_EQ(code, nitr::case004::ErrorCode::kEstimationFailed);
  std::ifstream output(out);
  EXPECT_FALSE(output.is_open());
}

TEST(LegacyOracle, InvalidSchemaAndJsonInputs) {
  const std::filesystem::path temp_dir = std::filesystem::temp_directory_path();
  const std::string invalid_schema_input =
      (temp_dir / "case004_legacy_invalid_schema.json").string();
  const std::string invalid_json_input =
      (temp_dir / "case004_legacy_invalid_json.json").string();
  const std::string out = TemporaryOutputPath("invalid");

  {
    std::ofstream input(invalid_schema_input);
    input << "{}";
  }
  EXPECT_EQ(
      nitr::case004::RunLegacyMonolith(invalid_schema_input, out),
      nitr::case004::ErrorCode::kInvalidSchema);

  {
    std::ofstream input(invalid_json_input);
    input << "{ this is invalid }";
  }
  EXPECT_EQ(
      nitr::case004::RunLegacyMonolith(invalid_json_input, out),
      nitr::case004::ErrorCode::kInvalidJson);
}
