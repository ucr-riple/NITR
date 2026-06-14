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

#if __has_include("ranking_inspect.h")
#include "ranking_inspect.h"
#define CASE019_HAS_RANKING_INSPECT 1
#else
#define CASE019_HAS_RANKING_INSPECT 0
#endif

int main() {
#if !CASE019_HAS_RANKING_REASONS
  case019_test::Fail("missing ranking_reasons.h");
#elif !CASE019_HAS_RANKING_INSPECT
  case019_test::Fail("missing ranking_inspect.h");
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

  case019_test::Expect(
      case019_test::has_inspect_method<nitr::case019::Ranker>::value,
      "Ranker must provide Inspect(items, id)");
  case019_test::Expect(
      case019_test::has_compare_method<nitr::case019::Ranker>::value,
      "Ranker must provide Compare(items, winner_id, loser_id)");

  if constexpr (!case019_test::has_inspect_method<
                    nitr::case019::Ranker>::value ||
                !case019_test::has_compare_method<
                    nitr::case019::Ranker>::value) {
    return 1;
  } else {
    const auto blocked = ranker.Inspect(items, 13);
    using Inspection = decltype(blocked);
    case019_test::Expect(case019_test::has_status_field<Inspection>::value,
                         "inspection result must include status");
    case019_test::Expect(case019_test::has_inspection_score<Inspection>::value,
                         "inspection result must include final_score");
    case019_test::Expect(
        case019_test::has_inspection_positive<Inspection>::value,
        "inspection result must include strongest_positive");
    case019_test::Expect(
        case019_test::has_inspection_negative<Inspection>::value,
        "inspection result must include strongest_negative");
    case019_test::Expect(case019_test::has_lost_on_tie_break<Inspection>::value,
                         "inspection result must include lost_on_tie_break");
    case019_test::Expect(
        case019_test::has_tie_break_against_id<Inspection>::value,
        "inspection result must include tie_break_against_id");

    if constexpr (!case019_test::has_status_field<Inspection>::value ||
                  !case019_test::has_inspection_score<Inspection>::value ||
                  !case019_test::has_inspection_positive<Inspection>::value ||
                  !case019_test::has_inspection_negative<Inspection>::value ||
                  !case019_test::has_lost_on_tie_break<Inspection>::value ||
                  !case019_test::has_tie_break_against_id<Inspection>::value) {
      return 1;
    } else {
      case019_test::Expect(
          blocked.status == nitr::case019::InspectionStatus::kBlocked,
          "blocked item inspection status is incorrect");
      case019_test::Expect(
          blocked.strongest_positive == nitr::case019::ReasonCode::kNone,
          "blocked item should not report a positive factor");
      case019_test::Expect(
          blocked.strongest_negative == nitr::case019::ReasonCode::kNone,
          "blocked item should not report a negative factor");
      case019_test::Expect(!blocked.lost_on_tie_break,
                           "blocked item should not report tie-break loss");

      const auto tie_loser = ranker.Inspect(items, 15);
      case019_test::Expect(
          tie_loser.status == nitr::case019::InspectionStatus::kRanked,
          "tie loser should be reported as ranked");
      case019_test::Expect(tie_loser.final_score == 94,
                           "tie loser inspection score is incorrect");
      case019_test::Expect(tie_loser.lost_on_tie_break,
                           "tie loser should report tie-break loss");
      case019_test::Expect(
          tie_loser.tie_break_against_id == 14,
          "tie loser should identify the winner of the tie-break");
      case019_test::Expect(tie_loser.strongest_positive ==
                               nitr::case019::ReasonCode::kCategoryMatch,
                           "tie loser strongest positive factor is incorrect");
      case019_test::Expect(
          tie_loser.strongest_negative == nitr::case019::ReasonCode::kNone,
          "tie loser should not report a negative factor");

      const auto missing = ranker.Inspect(items, 404);
      case019_test::Expect(
          missing.status == nitr::case019::InspectionStatus::kNotFound,
          "unknown item must report not found");

      const auto comparison = ranker.Compare(items, 14, 15);
      using Comparison = decltype(comparison);
      case019_test::Expect(case019_test::has_status_field<Comparison>::value,
                           "comparison result must include status");
      case019_test::Expect(case019_test::has_winner_id<Comparison>::value,
                           "comparison result must include winner_id");
      case019_test::Expect(case019_test::has_loser_id<Comparison>::value,
                           "comparison result must include loser_id");
      case019_test::Expect(
          case019_test::has_decided_by_tie_break<Comparison>::value,
          "comparison result must include decided_by_tie_break");
      case019_test::Expect(case019_test::has_decisive_reason<Comparison>::value,
                           "comparison result must include decisive_reason");

      if constexpr (!case019_test::has_status_field<Comparison>::value ||
                    !case019_test::has_winner_id<Comparison>::value ||
                    !case019_test::has_loser_id<Comparison>::value ||
                    !case019_test::has_decided_by_tie_break<
                        Comparison>::value ||
                    !case019_test::has_decisive_reason<Comparison>::value) {
        return 1;
      } else {
        case019_test::Expect(
            comparison.status == nitr::case019::ComparisonStatus::kOk,
            "tie-break comparison should be supported");
        case019_test::Expect(comparison.winner_id == 14,
                             "comparison winner id is incorrect");
        case019_test::Expect(comparison.loser_id == 15,
                             "comparison loser id is incorrect");
        case019_test::Expect(comparison.decided_by_tie_break,
                             "comparison should report tie-break decision");
        case019_test::Expect(comparison.decisive_reason ==
                                 nitr::case019::ReasonCode::kBaseScoreTieBreak,
                             "comparison decisive reason is incorrect");

        const auto blocked_comparison = ranker.Compare(items, 10, 13);
        case019_test::Expect(
            blocked_comparison.status ==
                nitr::case019::ComparisonStatus::kNotApplicable,
            "comparison with a blocked item should be not applicable");
      }
    }
  }
#endif

  return 0;
}
