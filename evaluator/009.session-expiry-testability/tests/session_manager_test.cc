#include "session_manager.h"

#include <cassert>
#include <cstdint>
#include <memory>
#include <string>

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

void TestCreateIsImmediatelyValid() {
  auto clock = std::make_shared<ManualTimeSource>(100);
  nitr::case009::SessionManager manager(10, clock);

  assert(manager.CreateSession("s1"));
  assert(manager.IsValid("s1"));
}

void TestExpiresAtBoundary() {
  auto clock = std::make_shared<ManualTimeSource>(100);
  nitr::case009::SessionManager manager(10, clock);

  assert(manager.CreateSession("s1"));
  clock->AdvanceSeconds(9);
  assert(manager.IsValid("s1"));

  clock->AdvanceSeconds(1);
  assert(!manager.IsValid("s1"));
}

void TestRefreshRestartsWindow() {
  auto clock = std::make_shared<ManualTimeSource>(100);
  nitr::case009::SessionManager manager(10, clock);

  assert(manager.CreateSession("s1"));
  clock->AdvanceSeconds(5);
  assert(manager.RefreshSession("s1"));

  clock->AdvanceSeconds(9);
  assert(manager.IsValid("s1"));

  clock->AdvanceSeconds(1);
  assert(!manager.IsValid("s1"));
}

void TestCannotRefreshExpiredSession() {
  auto clock = std::make_shared<ManualTimeSource>(100);
  nitr::case009::SessionManager manager(10, clock);

  assert(manager.CreateSession("s1"));
  clock->AdvanceSeconds(10);
  assert(!manager.RefreshSession("s1"));
}

void TestRemoveInvalidatesSession() {
  auto clock = std::make_shared<ManualTimeSource>(100);
  nitr::case009::SessionManager manager(10, clock);

  assert(manager.CreateSession("s1"));
  assert(manager.RemoveSession("s1"));
  assert(!manager.IsValid("s1"));
}

}  // namespace

int main() {
  TestCreateIsImmediatelyValid();
  TestExpiresAtBoundary();
  TestRefreshRestartsWindow();
  TestCannotRefreshExpiredSession();
  TestRemoveInvalidatesSession();
  return 0;
}
