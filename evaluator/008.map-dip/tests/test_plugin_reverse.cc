#include <iostream>
#include <nlohmann/json.hpp>
#include <string>

#include "map_snapshot.h"

// Plugin TU will define this function and call GlobalLayerRegistry().Register(...).
namespace nitr::case008 {
void RegisterReversePayloadLayer();
}  // namespace nitr::case008

static int g_failures = 0;

static void ExpectEq(const std::string& got, const std::string& expected,
                     const char* name) {
  if (got != expected) {
    std::cerr << "[FAIL] " << name << "\n"
              << "  got:\n"
              << got << "  expected:\n"
              << expected;
    g_failures++;
  } else {
    std::cerr << "[ OK ] " << name << "\n";
  }
}

static nlohmann::json MakeCfg() {
  nlohmann::json::object_t cfg;
  nlohmann::json::array_t layers;

  nlohmann::json::object_t l1;
  l1.emplace("type", "reverse_payload");
  layers.emplace_back(nlohmann::json(std::move(l1)));

  cfg.emplace("layers", nlohmann::json(std::move(layers)));
  return nlohmann::json(std::move(cfg));
}

int main() {
  using nitr::case008::MapSnapshotService;

  nitr::case008::RegisterReversePayloadLayer();

  MapSnapshotService svc;
  const std::string payload = "abcd";
  std::string out = svc.BuildSnapshot(MakeCfg(), payload);

  const std::string expected =
      "SNAPSHOT\n"
      "reverse_payload:dcba\n";
  ExpectEq(out, expected, "plugin_reverse_payload");

  if (g_failures != 0) {
    std::cerr << g_failures << " test(s) failed.\n";
    return 1;
  }
  std::cerr << "All tests passed.\n";
  return 0;
}
