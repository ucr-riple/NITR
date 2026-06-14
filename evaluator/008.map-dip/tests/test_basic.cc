#include <nlohmann/json.hpp>
#include <string>

#include <gtest/gtest.h>

#include "map_snapshot.h"

static nlohmann::json MakeCfg() {
  nlohmann::json::object_t cfg;
  nlohmann::json::array_t layers;

  nlohmann::json::object_t l1;
  l1.emplace("type", "geometry");
  layers.emplace_back(nlohmann::json(std::move(l1)));

  nlohmann::json::object_t l2;
  l2.emplace("type", "semantics");
  layers.emplace_back(nlohmann::json(std::move(l2)));

  cfg.emplace("layers", nlohmann::json(std::move(layers)));
  return nlohmann::json(std::move(cfg));
}

TEST(Case008MapDip, BasicLayersBuildSnapshot) {
  using nitr::case008::MapSnapshotService;

  const std::string payload = "  foo bar42  \n";
  MapSnapshotService svc;

  std::string out = svc.BuildSnapshot(MakeCfg(), payload);

  // alnum in "  foo bar42  \n" -> foo(3)+bar42(5)=8
  const std::string expected =
      "SNAPSHOT\n"
      "geometry:alnum_count=8\n"
      "semantics:first_token=foo\n";

  EXPECT_EQ(out, expected);
}
