#include <iostream>
#include <string>

#include "query_result.h"
#include "query_service.h"
#include "snapshot_store.h"

namespace {

int g_failures = 0;

void Expect(bool condition, const std::string& message) {
  if (!condition) {
    ++g_failures;
    std::cerr << "[FAIL] " << message << "\n";
  }
}

void ExpectStatus(const nitr::case017::QueryResult& result,
                  nitr::case017::QueryStatus expected,
                  const std::string& message) {
  Expect(result.status == expected, message);
}

void TestBaselineQueryBehavior() {
  nitr::case017::SnapshotStore store;
  nitr::case017::QueryService query(store);

  store.RegisterSnapshot("v1", {{"k", "one"}, {"x", "1"}});
  store.ActivateSnapshot("v1");

  const auto result = query.Lookup("k");
  ExpectStatus(result, nitr::case017::QueryStatus::kFound,
               "baseline: lookup should find key in active snapshot");
  Expect(result.value == "one",
         "baseline: found value should be from active snapshot");
  Expect(result.served_version == "v1",
         "baseline: served version should report active snapshot version");
}

void TestActivateReplaceBehavior() {
  nitr::case017::SnapshotStore store;
  nitr::case017::QueryService query(store);

  store.RegisterSnapshot("v1", {{"name", "alpha"}});
  store.RegisterSnapshot("v2", {{"name", "beta"}});

  Expect(store.ActivateSnapshot("v1"), "replace: activating v1 should succeed");
  auto result = query.Lookup("name");
  ExpectStatus(result, nitr::case017::QueryStatus::kFound,
               "replace: v1 should be query-visible after activation");
  Expect(result.value == "alpha", "replace: v1 value mismatch");

  Expect(store.ActivateSnapshot("v2"), "replace: activating v2 should succeed");
  result = query.Lookup("name");
  ExpectStatus(result, nitr::case017::QueryStatus::kFound,
               "replace: v2 should be query-visible after replacement");
  Expect(result.value == "beta",
         "replace: query should not return stale v1 value");
  Expect(result.served_version == "v2", "replace: served version should be v2");
}

void TestResetAndNoActiveBehavior() {
  nitr::case017::SnapshotStore store;
  nitr::case017::QueryService query(store);

  store.RegisterSnapshot("v1", {{"color", "blue"}});
  store.ActivateSnapshot("v1");
  ExpectStatus(query.Lookup("color"), nitr::case017::QueryStatus::kFound,
               "reset: query before reset should be found");

  store.ResetActiveSnapshot();
  auto result = query.Lookup("color");
  ExpectStatus(result, nitr::case017::QueryStatus::kNoActiveSnapshot,
               "reset: query after reset should report no active snapshot");
  Expect(result.value.empty(),
         "reset: no-active result should not return value");

  store.ResetActiveSnapshot();
  result = query.Lookup("color");
  ExpectStatus(result, nitr::case017::QueryStatus::kNoActiveSnapshot,
               "reset: repeated reset should remain no-active");
}

void TestUnknownActivationDoesNotReplaceActive() {
  nitr::case017::SnapshotStore store;
  nitr::case017::QueryService query(store);

  store.RegisterSnapshot("v1", {{"city", "rome"}});
  Expect(store.ActivateSnapshot("v1"),
         "unknown: activating known snapshot should succeed");

  const bool activated_unknown = store.ActivateSnapshot("missing-version");
  Expect(!activated_unknown,
         "unknown: activating unknown snapshot should fail");

  const auto result = query.Lookup("city");
  ExpectStatus(result, nitr::case017::QueryStatus::kFound,
               "unknown: failed activation must keep previous active snapshot");
  Expect(result.value == "rome",
         "unknown: active snapshot should remain unchanged");
}

void TestDuplicateRegistrationRejected() {
  nitr::case017::SnapshotStore store;
  nitr::case017::QueryService query(store);

  const bool first = store.RegisterSnapshot("v1", {{"id", "first"}});
  const bool second = store.RegisterSnapshot("v1", {{"id", "second"}});

  Expect(first, "dup: first registration should succeed");
  Expect(!second, "dup: duplicate registration should be rejected");

  store.ActivateSnapshot("v1");
  const auto result = query.Lookup("id");
  ExpectStatus(result, nitr::case017::QueryStatus::kFound,
               "dup: registered snapshot should be query-visible");
  Expect(result.value == "first",
         "dup: duplicate registration must not replace payload");
}

void TestRepeatedTransitionsAndIsolation() {
  nitr::case017::SnapshotStore store;
  nitr::case017::QueryService query(store);

  store.RegisterSnapshot("v1", {{"shared", "A"}});
  store.RegisterSnapshot("v2", {{"shared", "B"}});
  store.RegisterSnapshot("v3", {{"shared", "C"}});

  Expect(store.ActivateSnapshot("v1"), "seq: activate v1 should succeed");
  auto result = query.Lookup("shared");
  ExpectStatus(result, nitr::case017::QueryStatus::kFound,
               "seq: v1 lookup should be found");
  Expect(result.value == "A", "seq: v1 value mismatch");

  Expect(store.ActivateSnapshot("v2"), "seq: activate v2 should succeed");
  result = query.Lookup("shared");
  Expect(result.value == "B",
         "seq: after v1->v2, query must not return v1 value");

  Expect(store.ActivateSnapshot("v3"), "seq: activate v3 should succeed");
  result = query.Lookup("shared");
  Expect(result.value == "C",
         "seq: after v2->v3, query must not return older value");

  store.ResetActiveSnapshot();
  result = query.Lookup("shared");
  ExpectStatus(result, nitr::case017::QueryStatus::kNoActiveSnapshot,
               "seq: reset should hide all previously active snapshots");

  Expect(store.ActivateSnapshot("v2"),
         "seq: activate v2 after reset should succeed");
  result = query.Lookup("shared");
  Expect(result.value == "B",
         "seq: reset->reactivate should use newly active snapshot");
}

}  // namespace

int main() {
  TestBaselineQueryBehavior();
  TestActivateReplaceBehavior();
  TestResetAndNoActiveBehavior();
  TestUnknownActivationDoesNotReplaceActive();
  TestDuplicateRegistrationRejected();
  TestRepeatedTransitionsAndIsolation();

  if (g_failures == 0) {
    std::cout << "All lifecycle tests passed.\n";
    return 0;
  }

  std::cerr << g_failures << " lifecycle test(s) failed.\n";
  return 1;
}
