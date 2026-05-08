#include <algorithm>
#include <memory>
#include <nlohmann/json.hpp>
#include <string>

#include "map_snapshot.h"

namespace nitr::case008 {

// Expected in refactored solution:
class LayerRegistry {
 public:
  using CreatorFn =
      std::unique_ptr<ILayerProvider> (*)(const nlohmann::json& layer_json);
  void Register(const std::string& type, CreatorFn fn);
};

LayerRegistry& GlobalLayerRegistry();

class ReversePayloadProvider final : public ILayerProvider {
 public:
  std::string Name() const override {
    return "reverse_payload";
  }
  std::string BuildLayer(const std::string& payload) const override {
    std::string s = payload;
    std::reverse(s.begin(), s.end());
    return s;
  }
};

static std::unique_ptr<ILayerProvider> CreateReverse(const nlohmann::json&) {
  return std::make_unique<ReversePayloadProvider>();
}

void RegisterReversePayloadLayer() {
  GlobalLayerRegistry().Register("reverse_payload", &CreateReverse);
}

}  // namespace nitr::case008
