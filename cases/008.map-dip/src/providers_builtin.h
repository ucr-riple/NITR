#pragma once
#include <string>

#include "map_snapshot.h"

namespace nitr::case008 {

void RegisterBuiltinLayerProviders();

class GeometryProvider final : public ILayerProvider {
 public:
  std::string Name() const override {
    return "geometry";
  }
  std::string BuildLayer(const std::string& payload) const override;
};

class SemanticsProvider final : public ILayerProvider {
 public:
  std::string Name() const override {
    return "semantics";
  }
  std::string BuildLayer(const std::string& payload) const override;
};

}  // namespace nitr::case008
