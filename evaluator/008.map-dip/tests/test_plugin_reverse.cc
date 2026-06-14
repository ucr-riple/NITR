#include <nlohmann/json.hpp>
#include <string>

#include <gtest/gtest.h>

#include "map_snapshot.h"

// Plugin TU will define this function and call GlobalLayerRegistry().Register(...).
namespace nitr::case008 {
void RegisterReversePayloadLayer();
}  // namespace nitr::case008

static nlohmann::json MakeCfg() {
  nlohmann::json::object_t cfg;
  nlohmann::json::array_t layers;

  nlohmann::json::object_t l1;
  l1.emplace("type", "reverse_payload");
  layers.emplace_back(nlohmann::json(std::move(l1)));

  cfg.emplace("layers", nlohmann::json(std::move(layers)));
  return nlohmann::json(std::move(cfg));
}

TEST(Case008MapDip, PluginReversePayload) {
  using nitr::case008::MapSnapshotService;

  nitr::case008::RegisterReversePayloadLayer();

  MapSnapshotService svc;
  const std::string payload = "abcd";
  std::string out = svc.BuildSnapshot(MakeCfg(), payload);

  const std::string expected =
      "SNAPSHOT\n"
      "reverse_payload:dcba\n";

  EXPECT_EQ(out, expected);
}
