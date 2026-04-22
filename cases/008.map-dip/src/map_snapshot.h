#pragma once
#include <memory>
#include <nlohmann/json.hpp>
#include <string>

namespace nitr::case008 {

// Abstraction: a layer provider produces a layer string based on input payload.
class ILayerProvider {
 public:
  virtual ~ILayerProvider() = default;
  virtual std::string Name() const = 0;
  virtual std::string BuildLayer(const std::string& payload) const = 0;
};

class LayerRegistry {
 public:
  using CreatorFn =
      std::unique_ptr<ILayerProvider> (*)(const nlohmann::json& layer_json);

  void Register(const std::string& type, CreatorFn fn);
  std::unique_ptr<ILayerProvider> Create(const nlohmann::json& layer_json) const;
};

LayerRegistry& GlobalLayerRegistry();

class MapSnapshotService {
 public:
  // Build snapshot according to config:
  // { "layers": [ { "type": "...", ... }, ... ] }
 std::string BuildSnapshot(const nlohmann::json& config,
                            const std::string& payload) const;
};

}  // namespace nitr::case008
