#include <algorithm>
#include <cstdint>
#include <exception>
#include <functional>
#include <iostream>
#include <set>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <vector>

#include "candidate.h"
#include "sampler_v1.h"
#include "selector.h"

namespace {
using nitr::case018::Candidate;

struct RefSamplerV1 {
  explicit RefSamplerV1(std::uint64_t seed)
      : state(seed ^ 0x9E3779B97F4A7C15ULL) {}

  std::size_t NextIndex(std::size_t n) {
    if (n == 0U) {
      throw std::invalid_argument("n must be > 0");
    }
    state = state * 6364136223846793005ULL + 1442695040888963407ULL;
    return static_cast<std::size_t>((state >> 32U) % n);
  }

  std::uint64_t state;
};

void Assert(bool cond, const std::string& msg) {
  if (!cond) {
    throw std::runtime_error(msg);
  }
}

std::vector<Candidate> ActivePool(const std::vector<Candidate>& candidates) {
  std::vector<Candidate> primary;
  std::vector<Candidate> fallback;

  for (const Candidate& c : candidates) {
    if (!c.eligible) {
      continue;
    }
    if (c.is_fallback) {
      fallback.push_back(c);
    } else {
      primary.push_back(c);
    }
  }
  return !primary.empty() ? primary : fallback;
}

std::vector<std::string> ReferenceReplay(
    const std::vector<Candidate>& candidates, std::size_t k,
    std::uint64_t seed) {
  std::vector<Candidate> pool = ActivePool(candidates);
  if (pool.empty() || k == 0U) {
    return {};
  }

  std::sort(pool.begin(), pool.end(),
            [](const Candidate& a, const Candidate& b) {
              if (a.score != b.score) {
                return a.score > b.score;
              }
              return a.id < b.id;
            });

  RefSamplerV1 sampler(seed);
  std::vector<Candidate> arranged;
  arranged.reserve(pool.size());

  std::size_t i = 0U;
  while (i < pool.size()) {
    std::size_t j = i + 1U;
    while (j < pool.size() && pool[j].score == pool[i].score) {
      ++j;
    }

    std::vector<Candidate> group(pool.begin() + static_cast<long>(i),
                                 pool.begin() + static_cast<long>(j));
    for (std::size_t p = group.size(); p > 1U; --p) {
      const std::size_t q = sampler.NextIndex(p);
      std::swap(group[p - 1U], group[q]);
    }

    arranged.insert(arranged.end(), group.begin(), group.end());
    i = j;
  }

  const std::size_t take = std::min(k, arranged.size());
  std::vector<std::string> out;
  out.reserve(take);
  for (std::size_t idx = 0U; idx < take; ++idx) {
    out.push_back(arranged[idx].id);
  }
  return out;
}

std::unordered_map<std::string, Candidate> AsMap(
    const std::vector<Candidate>& candidates) {
  std::unordered_map<std::string, Candidate> m;
  for (const Candidate& c : candidates) {
    m[c.id] = c;
  }
  return m;
}

void AssertPolicyInvariants(const std::vector<Candidate>& candidates,
                            std::size_t k,
                            const std::vector<std::string>& output) {
  const auto by_id = AsMap(candidates);
  std::vector<Candidate> pool = ActivePool(candidates);

  const std::size_t expected_max = std::min(k, pool.size());
  Assert(output.size() <= expected_max, "Output longer than allowed by pool/k");

  std::set<std::string> seen;
  bool pool_is_fallback = false;
  if (!pool.empty()) {
    pool_is_fallback = pool.front().is_fallback;
  }

  int prev_score = 1'000'000;
  for (const std::string& id : output) {
    const auto it = by_id.find(id);
    Assert(it != by_id.end(), "Output contains unknown candidate id");
    const Candidate& c = it->second;
    Assert(c.eligible, "Output contains ineligible candidate");
    Assert(c.is_fallback == pool_is_fallback,
           "Output violates fallback precedence");
    Assert(seen.insert(id).second, "Output contains duplicate id");
    Assert(c.score <= prev_score, "Output violates score-priority invariant");
    prev_score = c.score;
  }
}

std::vector<Candidate> FixtureCore() {
  return {
      {"a1", 100, true, false}, {"a2", 100, true, false},
      {"a3", 100, true, false}, {"b1", 90, true, false},
      {"b2", 90, true, false},  {"c1", 80, true, false},
      {"fb1", 70, true, true},  {"blocked", 120, false, false},
  };
}

void TestReplayExactSingle() {
  const std::vector<Candidate> fixture = FixtureCore();
  const auto expected = ReferenceReplay(fixture, 1U, 42U);
  const auto actual =
      nitr::case018::SelectRecommendationsReplay(fixture, 1U, 42U);
  Assert(actual == expected,
         "Replay single-pick output mismatch vs SamplerV1 contract");
}

void TestReplayExactMulti() {
  const std::vector<Candidate> fixture = FixtureCore();
  const auto expected = ReferenceReplay(fixture, 4U, 4242U);
  const auto actual =
      nitr::case018::SelectRecommendationsReplay(fixture, 4U, 4242U);
  Assert(actual == expected,
         "Replay multi-pick output mismatch vs SamplerV1 contract");
}

void TestReplayDeterminismRepeat() {
  const std::vector<Candidate> fixture = FixtureCore();
  const auto baseline =
      nitr::case018::SelectRecommendationsReplay(fixture, 5U, 9U);
  for (int i = 0; i < 10; ++i) {
    const auto next =
        nitr::case018::SelectRecommendationsReplay(fixture, 5U, 9U);
    Assert(next == baseline,
           "Replay output changed across repeated calls with same seed");
  }
}

void TestReplayKGreaterThanPool() {
  const std::vector<Candidate> fixture = FixtureCore();
  const auto expected = ReferenceReplay(fixture, 100U, 7U);
  const auto actual =
      nitr::case018::SelectRecommendationsReplay(fixture, 100U, 7U);
  Assert(actual == expected, "Replay k>pool behavior mismatch");
}

void TestFallbackAndEmpty() {
  const std::vector<Candidate> fallback_only = {
      {"p1", 100, false, false},
      {"fb1", 30, true, true},
      {"fb2", 20, true, true},
  };
  const auto out_fb =
      nitr::case018::SelectRecommendationsReplay(fallback_only, 2U, 5U);
  const auto exp_fb = ReferenceReplay(fallback_only, 2U, 5U);
  Assert(out_fb == exp_fb, "Fallback replay output mismatch");

  const std::vector<Candidate> empty = {
      {"p1", 100, false, false},
      {"fb1", 30, false, true},
  };
  const auto out_empty =
      nitr::case018::SelectRecommendationsReplay(empty, 3U, 1U);
  Assert(out_empty.empty(),
         "Replay should return empty when no eligible candidates");
}

void TestDefaultPolicyInvariants() {
  const std::vector<Candidate> fixture = FixtureCore();
  const auto out = nitr::case018::SelectRecommendations(fixture, 5U);
  AssertPolicyInvariants(fixture, 5U, out);
}

void TestPolicyEquivalenceUnderSameSampler() {
  const std::vector<Candidate> fixture = FixtureCore();

  // Policy-equivalence probe: replay path and explicit-sampler path should match.
  nitr::case018::SamplerV1 sampler(12345U);
  const auto with_sampler =
      nitr::case018::SelectRecommendationsWithSampler(fixture, 6U, sampler);
  const auto replay =
      nitr::case018::SelectRecommendationsReplay(fixture, 6U, 12345U);
  Assert(
      with_sampler == replay,
      "Replay path diverges from explicit-sampler path under same seed/stream");
}

void TestSeedChangeOnlyAffectsRandomAspect() {
  const std::vector<Candidate> fixture = FixtureCore();
  const auto out_a =
      nitr::case018::SelectRecommendationsReplay(fixture, 5U, 11U);
  const auto out_b =
      nitr::case018::SelectRecommendationsReplay(fixture, 5U, 12U);
  AssertPolicyInvariants(fixture, 5U, out_a);
  AssertPolicyInvariants(fixture, 5U, out_b);
}

}  // namespace

int main() {
  const std::vector<std::pair<std::string, std::function<void()>>> tests = {
      {"ReplayExactSingle", TestReplayExactSingle},
      {"ReplayExactMulti", TestReplayExactMulti},
      {"ReplayDeterminismRepeat", TestReplayDeterminismRepeat},
      {"ReplayKGreaterThanPool", TestReplayKGreaterThanPool},
      {"FallbackAndEmpty", TestFallbackAndEmpty},
      {"DefaultPolicyInvariants", TestDefaultPolicyInvariants},
      {"PolicyEquivalenceUnderSameSampler",
       TestPolicyEquivalenceUnderSameSampler},
      {"SeedChangeOnlyAffectsRandomAspect",
       TestSeedChangeOnlyAffectsRandomAspect},
  };

  int failed = 0;
  for (const auto& test : tests) {
    try {
      test.second();
      std::cout << "[PASS] " << test.first << "\n";
    } catch (const std::exception& ex) {
      ++failed;
      std::cout << "[FAIL] " << test.first << ": " << ex.what() << "\n";
    }
  }

  if (failed != 0) {
    std::cout << failed << " test(s) failed\n";
    return 1;
  }
  std::cout << "All evaluator tests passed\n";
  return 0;
}
