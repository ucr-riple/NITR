#include <gtest/gtest.h>

#include <fstream>
#include <string>

#include "io_json.h"
#include "types.h"

namespace nitr::case004 {

static std::string WriteTempFile(const std::string& content) {
  const std::string path = "tmp_pair.json";
  std::ofstream ofs(path);
  ofs << content;
  return path;
}

TEST(IoJson, InvalidJson) {
  std::string path = WriteTempFile("{ this is not json ");
  ParseOutput p = ParsePairJsonFromFile(path);
  EXPECT_FALSE(p.input.has_value());
  EXPECT_EQ(p.err, ErrorCode::kInvalidJson);
}

TEST(IoJson, InvalidSchemaMissingFields) {
  std::string path =
      WriteTempFile(R"({"camera": {"fx":1,"fy":1,"cx":0,"cy":0}})");
  ParseOutput p = ParsePairJsonFromFile(path);
  EXPECT_FALSE(p.input.has_value());
  EXPECT_EQ(p.err, ErrorCode::kInvalidSchema);
}

}  // namespace nitr::case004
