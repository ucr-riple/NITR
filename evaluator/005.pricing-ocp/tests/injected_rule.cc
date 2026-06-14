#include <memory>

#include "pricing.h"

namespace nitr::case005 {

class Injected10Off final : public IRule {
 public:
  std::string Id() const override {
    return "INJECTED_10OFF_RULE";
  }

  bool Applicable(const RuleContext&) const override {
    return true;
  }

  int64_t DeltaCents(const RuleContext& ctx,
                     int64_t base_price_cents) const override {
    (void)ctx;
    return -base_price_cents / 10;  // 10%
  }
};

static const bool kRegistered = [] {
  RuleRegistry::Instance().Register("INJECTED_10OFF", [](const RuleContext&) {
    return std::make_unique<Injected10Off>();
  });
  return true;
}();

}  // namespace nitr::case005
