#include <cstdlib>
#include <iostream>
#include <vector>

#include "item.h"
#include "ranker.h"

namespace {

void Expect(bool condition, const char* message) {
  if (!condition) {
    std::cerr << message << "\n";
    std::exit(1);
  }
}

}  // namespace

int main() {
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

  Expect(ranked.size() == 5,
         "blocked items should be excluded from ranking results");
  Expect(ranked[0].item.id == 10, "top match should rank first");
  Expect(ranked[1].item.id == 14,
         "tie winner should rank ahead on base score tie-break");
  Expect(ranked[2].item.id == 15, "tie loser should follow after tie-break");
  Expect(ranked[3].item.id == 12,
         "wrong category item should still be ranked if not blocked");
  Expect(ranked[4].item.id == 11,
         "stale item should rank last among eligible items");

  Expect(ranked[0].final_score == 98,
         "top match score should match the current formula");
  Expect(ranked[1].final_score == ranked[2].final_score,
         "tie-case items should share the same final score");

  return 0;
}
