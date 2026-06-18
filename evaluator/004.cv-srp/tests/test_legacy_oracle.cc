#include <gtest/gtest.h>

#include <filesystem>
#include <fstream>
#include <limits>
#include <nlohmann/json.hpp>
#include <random>
#include <sstream>
#include <string>

#include "legacy_monolith.h"

namespace {

std::string DataPath(const std::string& file_name) {
#ifdef NITR_CASE_DATA_DIR
  return (std::filesystem::path(NITR_CASE_DATA_DIR) / file_name).string();
#else
  const std::filesystem::path evaluator_dir =
      std::filesystem::path(__FILE__).parent_path();
  return (evaluator_dir / "../data" / file_name).string();
#endif
}

std::string TemporaryOutputPath(const std::string& suffix) {
  static std::mt19937_64 rng(std::random_device{}());
  static std::uniform_int_distribution<unsigned long long> dist(
      0, std::numeric_limits<unsigned long long>::max());
  const auto token = std::to_string(dist(rng));
  return (std::filesystem::temp_directory_path() /
          ("case004_legacy_oracle_" + suffix + "_" + token + ".json"))
      .string();
}

std::string TemporaryInputPath(const std::string& suffix) {
  return TemporaryOutputPath(suffix);
}

void RemoveIfExists(const std::string& path) {
  std::error_code ignored;
  (void)std::filesystem::remove(path, ignored);
}

}  // namespace

TEST(LegacyOracle, OutputsForSimpleValidCase) {
  const std::string out = TemporaryOutputPath("simple");
  const auto code =
      nitr::case004::RunLegacyMonolith(DataPath("simple_ok.json"), out);
  EXPECT_NE(code, nitr::case004::ErrorCode::kInvalidJson);
  EXPECT_NE(code, nitr::case004::ErrorCode::kInvalidSchema);

  std::ifstream output(out);
  if (code == nitr::case004::ErrorCode::kOk ||
      code == nitr::case004::ErrorCode::kRejected) {
    EXPECT_TRUE(output.is_open());
    const auto out_text = [&output]() {
      std::ostringstream buffer;
      buffer << output.rdbuf();
      return buffer.str();
    }();
    const auto out_json = nlohmann::json::parse(out_text);
    EXPECT_EQ(out_json.value("decision", ""),
              code == nitr::case004::ErrorCode::kOk ? "ACCEPT" : "REJECT");
    EXPECT_TRUE(out_json.contains("metrics"));
    EXPECT_TRUE(out_json.value("metrics", nlohmann::json::object())
                    .contains("num_inliers"));
  } else {
    EXPECT_FALSE(output.is_open());
  }

  RemoveIfExists(out);
}

TEST(LegacyOracle, RejectCase) {
  const std::string out = TemporaryOutputPath("reject");
  const auto code =
      nitr::case004::RunLegacyMonolith(DataPath("reject_case.json"), out);
  EXPECT_NE(code, nitr::case004::ErrorCode::kInvalidJson);
  EXPECT_NE(code, nitr::case004::ErrorCode::kInvalidSchema);

  std::ifstream output(out);
  if (code == nitr::case004::ErrorCode::kRejected) {
    EXPECT_TRUE(output.is_open());
    const auto out_text = [&output]() {
      std::ostringstream buffer;
      buffer << output.rdbuf();
      return buffer.str();
    }();
    const auto out_json = nlohmann::json::parse(out_text);
    EXPECT_EQ(out_json.value("decision", ""), "REJECT");
    EXPECT_TRUE(out_json.contains("metrics"));
    EXPECT_TRUE(out_json["metrics"].contains("num_matches"));
    EXPECT_TRUE(out_json["metrics"].contains("num_inliers"));
  } else {
    EXPECT_FALSE(output.is_open());
    EXPECT_EQ(code, nitr::case004::ErrorCode::kEstimationFailed);
  }

  RemoveIfExists(out);
}

TEST(LegacyOracle, EstimationFailedCase) {
  const std::string out = TemporaryOutputPath("estimation_failed");
  const auto code =
      nitr::case004::RunLegacyMonolith(DataPath("estimation_failed.json"), out);
  EXPECT_EQ(code, nitr::case004::ErrorCode::kEstimationFailed);
  std::ifstream output(out);
  EXPECT_FALSE(output.is_open());

  RemoveIfExists(out);
}

TEST(LegacyOracle, InvalidSchemaAndJsonInputs) {
  const std::string invalid_schema_input = TemporaryInputPath("invalid_schema");
  const std::string invalid_json_input = TemporaryInputPath("invalid_json");
  const std::string invalid_schema_out =
      TemporaryOutputPath("invalid_schema_out");
  const std::string invalid_json_out = TemporaryOutputPath("invalid_json_out");

  {
    std::ofstream input(invalid_schema_input);
    input << "{}";
  }
  EXPECT_EQ(nitr::case004::RunLegacyMonolith(invalid_schema_input,
                                             invalid_schema_out),
            nitr::case004::ErrorCode::kInvalidSchema);
  EXPECT_FALSE(std::filesystem::exists(invalid_schema_out));

  {
    std::ofstream input(invalid_json_input);
    input << "{ this is invalid }";
  }
  EXPECT_EQ(
      nitr::case004::RunLegacyMonolith(invalid_json_input, invalid_json_out),
      nitr::case004::ErrorCode::kInvalidJson);
  EXPECT_FALSE(std::filesystem::exists(invalid_json_out));

  RemoveIfExists(invalid_schema_input);
  RemoveIfExists(invalid_json_input);
  RemoveIfExists(invalid_schema_out);
  RemoveIfExists(invalid_json_out);
}
