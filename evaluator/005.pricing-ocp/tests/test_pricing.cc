#include <gtest/gtest.h>

#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <fstream>
#include <stdexcept>
#include <string>
#include <vector>

#include "pricing.h"

namespace {

#if defined(_WIN32)
static void SetEnv(const std::string& k, const std::string& v) {
  _putenv_s(k.c_str(), v.c_str());
}
static void UnsetEnv(const std::string& k) {
  _putenv_s(k.c_str(), "");
}
#else
static void SetEnv(const std::string& k, const std::string& v) {
  setenv(k.c_str(), v.c_str(), 1);
}
static void UnsetEnv(const std::string& k) {
  unsetenv(k.c_str());
}
#endif

static bool WriteTextFile(const std::string& path, const std::string& content) {
  std::ofstream ofs(path);
  if (!ofs.is_open()) {
    return false;
  }
  ofs << content;
  return true;
}

struct ScopedCwdRulesJson {
  explicit ScopedCwdRulesJson(const std::string& content)
      : path_("rules.json"), active_(false) {
    // Best effort: overwrite rules.json in cwd for this test.
    if (WriteTextFile(path_, content)) {
      active_ = true;
    }
  }
  ~ScopedCwdRulesJson() {
    if (active_) {
      std::remove(path_.c_str());
    }
  }
  std::string path_;
  bool active_;
};

static nitr::case005::Order MakeOrderDollars(
    double subtotal, bool is_member, int items,
    std::vector<std::string> coupons = {}) {
  nitr::case005::Order o;
  o.subtotal_cents = static_cast<int64_t>(llround(subtotal * 100.0));
  o.is_member = is_member;
  o.items = items;
  o.coupons = std::move(coupons);
  return o;
}

static void ExpectRuntimeError(const std::function<void()>& fn,
                               const std::string& expected_code) {
  try {
    fn();
    FAIL() << "Expected runtime_error: " << expected_code;
  } catch (const std::runtime_error& e) {
    EXPECT_STREQ(e.what(), expected_code.c_str());
  }
}

}  // namespace

// ---------- m1 ----------

TEST(PricingOCP, M1_NoRulesApplied) {
  auto o = MakeOrderDollars(120.0, /*is_member=*/false, /*items=*/1);
  auto r = nitr::case005::ComputeFinalPrice(o, 1);
  EXPECT_EQ(r.final_price_cents, 12000);
  EXPECT_TRUE(r.applied_rules.empty());
}

TEST(PricingOCP, M1_Items20Off_AppliesAt10Items) {
  auto o = MakeOrderDollars(120.0, /*is_member=*/false, /*items=*/10);
  auto r = nitr::case005::ComputeFinalPrice(o, 1);
  EXPECT_EQ(r.final_price_cents, 10000);  // 120 - 20
  EXPECT_NE(
      std::find(r.applied_rules.begin(), r.applied_rules.end(), "ITEMS_20OFF"),
      r.applied_rules.end());
}

TEST(PricingOCP, M1_Member10P_Applies) {
  auto o = MakeOrderDollars(120.0, /*is_member=*/true, /*items=*/0);
  auto r = nitr::case005::ComputeFinalPrice(o, 1);
  // percent is expected to be based on subtotal (the intended case behavior)
  EXPECT_EQ(r.final_price_cents, 10800);  // 120 - 12
  EXPECT_NE(
      std::find(r.applied_rules.begin(), r.applied_rules.end(), "MEMBER_10P"),
      r.applied_rules.end());
}

TEST(PricingOCP, M1_BothApply) {
  auto o = MakeOrderDollars(120.0, /*is_member=*/true, /*items=*/10);
  auto r = nitr::case005::ComputeFinalPrice(o, 1);
  // 120 - 20 - 12 = 88
  EXPECT_EQ(r.final_price_cents, 8800);
}

// ---------- m2 ----------

TEST(PricingOCP, M2_CouponSave5) {
  auto o = MakeOrderDollars(100.0, false, 0, {"SAVE5"});
  auto r = nitr::case005::ComputeFinalPrice(o, 2);
  EXPECT_EQ(r.final_price_cents, 9500);
  EXPECT_NE(
      std::find(r.applied_rules.begin(), r.applied_rules.end(), "COUPON_SAVE5"),
      r.applied_rules.end());
}

TEST(PricingOCP, M2_CouponSave10P) {
  auto o = MakeOrderDollars(100.0, false, 0, {"SAVE10P"});
  auto r = nitr::case005::ComputeFinalPrice(o, 2);
  EXPECT_EQ(r.final_price_cents, 9000);
  EXPECT_NE(std::find(r.applied_rules.begin(), r.applied_rules.end(),
                      "COUPON_SAVE10P"),
            r.applied_rules.end());
}

// ---------- m3 selection ----------

TEST(PricingOCP, M3_GroupExclusivity_PicksHigherPriorityCoupon) {
  auto o = MakeOrderDollars(120.0, true, 10, {"SAVE5", "SAVE10P"});
  auto r = nitr::case005::ComputeFinalPrice(o, 3);

  // In COUPON group, only COUPON_SAVE10P should remain.
  EXPECT_NE(std::find(r.applied_rules.begin(), r.applied_rules.end(),
                      "COUPON_SAVE10P"),
            r.applied_rules.end());
  EXPECT_EQ(
      std::find(r.applied_rules.begin(), r.applied_rules.end(), "COUPON_SAVE5"),
      r.applied_rules.end());
}

// ---------- m4 runtime rules ----------

TEST(PricingOCP, M4_RuntimeRule_LoadsFromCwdRulesJson) {
  UnsetEnv("NITR_RULES");
  ScopedCwdRulesJson f(R"JSON(
{
  "rules": [
    {
      "id": "BLACKFRIDAY_30P",
      "type": "percent",
      "value": 0.30,
      "priority": 100,
      "group": "COUPON",
      "disables_member": true,
      "when": { "coupon": "BLACKFRIDAY", "is_member": true, "min_items": 5 }
    }
  ]
}
)JSON");

  auto o = MakeOrderDollars(100.0, true, 12, {"BLACKFRIDAY", "SAVE10P"});
  auto r = nitr::case005::ComputeFinalPrice(o, 4);

  // Expected: select BLACKFRIDAY_30P over COUPON_SAVE10P, and disables_member drops MEMBER_10P.
  // Also ITEMS_20OFF applies.
  EXPECT_EQ(r.final_price_cents, 5000);  // 100 - 20 - 30
  EXPECT_NE(std::find(r.applied_rules.begin(), r.applied_rules.end(),
                      "BLACKFRIDAY_30P"),
            r.applied_rules.end());
  EXPECT_EQ(std::find(r.applied_rules.begin(), r.applied_rules.end(),
                      "COUPON_SAVE10P"),
            r.applied_rules.end());
  EXPECT_EQ(
      std::find(r.applied_rules.begin(), r.applied_rules.end(), "MEMBER_10P"),
      r.applied_rules.end());
  EXPECT_NE(
      std::find(r.applied_rules.begin(), r.applied_rules.end(), "ITEMS_20OFF"),
      r.applied_rules.end());
}

TEST(PricingOCP, M4_InvalidRulesJson_BadPercentOutOfRange) {
  // Force loading by creating rules.json in cwd.
  UnsetEnv("NITR_RULES");
  ScopedCwdRulesJson f(R"JSON(
{
  "rules": [
    { "id": "BAD", "type": "percent", "value": 1.5, "priority": 0 }
  ]
}
)JSON");

  auto o = MakeOrderDollars(100.0, false, 0, {});
  ExpectRuntimeError([&] { (void)nitr::case005::ComputeFinalPrice(o, 4); },
                     "ERR_INVALID_SCHEMA");
}

TEST(PricingOCP, M4_InvalidRulesJson_BadType) {
  UnsetEnv("NITR_RULES");
  ScopedCwdRulesJson f(R"JSON(
{
  "rules": [
    { "id": "BAD", "type": "bogus", "value": 0.1, "priority": 0 }
  ]
}
)JSON");

  auto o = MakeOrderDollars(100.0, false, 0, {});
  ExpectRuntimeError([&] { (void)nitr::case005::ComputeFinalPrice(o, 4); },
                     "ERR_INVALID_SCHEMA");
}

TEST(PricingOCP, M4_InvalidRulesJson_MissingId) {
  UnsetEnv("NITR_RULES");
  ScopedCwdRulesJson f(R"JSON(
{
  "rules": [
    { "type": "flat", "value": 5.0, "priority": 0 }
  ]
}
)JSON");

  auto o = MakeOrderDollars(100.0, false, 0, {});
  ExpectRuntimeError([&] { (void)nitr::case005::ComputeFinalPrice(o, 4); },
                     "ERR_INVALID_SCHEMA");
}

TEST(PricingOCP, InjectedRuleWorks) {
  nitr::case005::Order o;
  o.subtotal_cents = 10000;  // $100
  o.is_member = false;
  o.items = 0;
  o.coupons = {"INJECTED_10OFF"};

  auto r = nitr::case005::ComputeFinalPrice(o, /*milestone=*/4);

  // 10% off => $90
  EXPECT_EQ(r.final_price_cents, 9000);
  EXPECT_NE(std::find(r.applied_rules.begin(), r.applied_rules.end(),
                      "INJECTED_10OFF_RULE"),
            r.applied_rules.end());
}
