#include "session_manager.h"

#include <cstdint>
#include <memory>
#include <string>

#include <gtest/gtest.h>

#include "time_source.h"

namespace {

class ManualTimeSource final : public nitr::case009::TimeSource {
 public:
  explicit ManualTimeSource(std::int64_t now_seconds)
      : now_seconds_(now_seconds) {}

  std::int64_t NowSeconds() const override {
    return now_seconds_;
  }

  void AdvanceSeconds(std::int64_t delta_seconds) {
    now_seconds_ += delta_seconds;
  }

 private:
  std::int64_t now_seconds_;
};

TEST(Case009SessionManager, CreatedSessionIsImmediatelyValid) {
  auto clock = std::make_shared<ManualTimeSource>(100);
  nitr::case009::SessionManager manager(10, clock);

  EXPECT_TRUE(manager.CreateSession("s1"));
  EXPECT_TRUE(manager.IsValid("s1"));
}

TEST(Case009SessionManager, ExpiresAtBoundary) {
  auto clock = std::make_shared<ManualTimeSource>(100);
  nitr::case009::SessionManager manager(10, clock);

  EXPECT_TRUE(manager.CreateSession("s1"));
  clock->AdvanceSeconds(9);
  EXPECT_TRUE(manager.IsValid("s1"));

  clock->AdvanceSeconds(1);
  EXPECT_FALSE(manager.IsValid("s1"));
}

TEST(Case009SessionManager, RefreshRestartsWindow) {
  auto clock = std::make_shared<ManualTimeSource>(100);
  nitr::case009::SessionManager manager(10, clock);

  EXPECT_TRUE(manager.CreateSession("s1"));
  clock->AdvanceSeconds(5);
  EXPECT_TRUE(manager.RefreshSession("s1"));

  clock->AdvanceSeconds(9);
  EXPECT_TRUE(manager.IsValid("s1"));

  clock->AdvanceSeconds(1);
  EXPECT_FALSE(manager.IsValid("s1"));
}

TEST(Case009SessionManager, CannotRefreshExpiredSession) {
  auto clock = std::make_shared<ManualTimeSource>(100);
  nitr::case009::SessionManager manager(10, clock);

  EXPECT_TRUE(manager.CreateSession("s1"));
  clock->AdvanceSeconds(10);
  EXPECT_FALSE(manager.RefreshSession("s1"));
}

TEST(Case009SessionManager, RemoveInvalidatesSession) {
  auto clock = std::make_shared<ManualTimeSource>(100);
  nitr::case009::SessionManager manager(10, clock);

  EXPECT_TRUE(manager.CreateSession("s1"));
  EXPECT_TRUE(manager.RemoveSession("s1"));
  EXPECT_FALSE(manager.IsValid("s1"));
}

}  // namespace
