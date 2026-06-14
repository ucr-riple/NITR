#include <vector>

#include "item.h"
#include "ranker.h"
#include "test_support.h"

#if __has_include("ranking_reasons.h")
#include "ranking_reasons.h"
#define CASE019_HAS_RANKING_REASONS 1
#else
#define CASE019_HAS_RANKING_REASONS 0
#endif

int main() {
#if !CASE019_HAS_RANKING_REASONS
  case019_test::Fail("missing ranking_reasons.h");
#else
  const std::vector<nitr::case019::Item> items = {
      {10, "Top Match", 60, true, 1, 55, false},
      {11, "Stale Match", 67, true, 20, 40, false},
      {12, "Wrong Category", 75, false, 2, 35, false},
      {13, "Blocked Item", 99, true, 1, 90, true},
      {14, "Tie Winner", 70, true, 6, 25, false},
      {15, "Tie Loser", 68, true, 6, 35, false},
  };

  const nitr::case019::Ranker ranker;
  const auto ranked = ranker.Rank(items);

  case019_test::Expect(ranked.size() == 5,
                       "ranked result size changed unexpectedly");
  case019_test::Expect(
      case019_test::has_reason_summary<nitr::case019::RankedItem>::value,
      "RankedItem must expose reason_summary");

  if constexpr (!case019_test::has_reason_summary<
                    nitr::case019::RankedItem>::value) {
    return 1;
  } else {
    using Summary = decltype(ranked[0].reason_summary);
    case019_test::Expect(case019_test::has_summary_final_score<Summary>::value,
                         "ReasonSummary must include final_score");
    case019_test::Expect(case019_test::has_summary_positive<Summary>::value,
                         "ReasonSummary must include strongest_positive");
    case019_test::Expect(case019_test::has_summary_negative<Summary>::value,
                         "ReasonSummary must include strongest_negative");

    if constexpr (!case019_test::has_summary_final_score<Summary>::value ||
                  !case019_test::has_summary_positive<Summary>::value ||
                  !case019_test::has_summary_negative<Summary>::value) {
      return 1;
    } else {
      case019_test::Expect(ranked[0].item.id == 10,
                           "top match should remain first");
      case019_test::Expect(
          ranked[0].reason_summary.final_score == ranked[0].final_score,
          "reason summary final_score must match ranked final_score");
      case019_test::Expect(ranked[0].reason_summary.final_score == 98,
                           "top match reason summary score is incorrect");
      case019_test::Expect(ranked[0].reason_summary.strongest_positive ==
                               nitr::case019::ReasonCode::kCategoryMatch,
                           "top match strongest positive factor is incorrect");
      case019_test::Expect(
          ranked[0].reason_summary.strongest_negative ==
              nitr::case019::ReasonCode::kNone,
          "top match should not have a strongest negative factor");

      case019_test::Expect(ranked[3].item.id == 12,
                           "wrong category item should stay in fourth place");
      case019_test::Expect(ranked[3].reason_summary.final_score == 86,
                           "wrong category final score is incorrect");
      case019_test::Expect(
          ranked[3].reason_summary.strongest_positive ==
              nitr::case019::ReasonCode::kFreshnessBoost,
          "wrong category strongest positive factor is incorrect");
      case019_test::Expect(
          ranked[3].reason_summary.strongest_negative ==
              nitr::case019::ReasonCode::kCategoryMismatch,
          "wrong category strongest negative factor is incorrect");

      case019_test::Expect(
          ranked[4].item.id == 11,
          "stale match should remain last among eligible items");
      case019_test::Expect(ranked[4].reason_summary.final_score == 80,
                           "stale match final score is incorrect");
      case019_test::Expect(
          ranked[4].reason_summary.strongest_positive ==
              nitr::case019::ReasonCode::kCategoryMatch,
          "stale match strongest positive factor is incorrect");
      case019_test::Expect(
          ranked[4].reason_summary.strongest_negative ==
              nitr::case019::ReasonCode::kStalePenalty,
          "stale match strongest negative factor is incorrect");
    }
  }
#endif

  return 0;
}
