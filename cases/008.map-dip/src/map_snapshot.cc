#include "map_snapshot.h"

#include <stdexcept>
#include <unordered_map>

#include "providers_builtin.h"

namespace nitr::case008 {

namespace {

using RegistryStorage = std::unordered_map<std::string, LayerRegistry::CreatorFn>;

RegistryStorage& RegistryEntries() {
  static RegistryStorage entries;
  return entries;
}

}  // namespace

LayerRegistry& GlobalLayerRegistry() {
  static LayerRegistry registry;
  return registry;
}

void LayerRegistry::Register(const std::string& type, CreatorFn fn) {
  if (type.empty() || fn == nullptr) {
    return;
  }
  RegistryEntries()[type] = fn;
}

std::unique_ptr<ILayerProvider> LayerRegistry::Create(
    const nlohmann::json& layer_json) const {
  if (!layer_json.is_object() || !layer_json.contains("type") ||
      !layer_json["type"].is_string()) {
    throw std::runtime_error(
        "each layer must be an object with string field 'type'");
  }
  const std::string type = layer_json["type"].get<std::string>();

  const auto it = RegistryEntries().find(type);
  if (it == RegistryEntries().end()) {
    throw std::runtime_error("unknown layer type: " + type);
  }
  return it->second(layer_json);
}

std::string MapSnapshotService::BuildSnapshot(
    const nlohmann::json& config, const std::string& payload) const {
  RegisterBuiltinLayerProviders();
  if (!config.is_object() || !config.contains("layers") ||
      !config["layers"].is_array()) {
    throw std::runtime_error(
        "config must be an object with array field 'layers'");
  }

  // Output format (stable for tests):
  // SNAPSHOT
  // <layer_name>:<layer_value>
  // ...
  std::string out = "SNAPSHOT\n";
  for (const auto& layer_json : config["layers"]) {
    std::unique_ptr<ILayerProvider> p = GlobalLayerRegistry().Create(layer_json);
    out += p->Name();
    out += ":";
    out += p->BuildLayer(payload);
    out += "\n";
  }
  return out;
}

}  // namespace nitr::case008
