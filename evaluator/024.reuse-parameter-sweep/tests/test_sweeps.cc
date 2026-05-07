#include <cmath>
#include <gtest/gtest.h>
#include <vector>
#include "runner.h"
#include "sweeps.h"

using namespace nitr::case024;

// ── Helpers ──────────────────────────────────────────────────────────────────

static TrialParams make_base(int seed = 1) {
  TrialParams p{};
  p.seed = seed;
  p.learning_rate = 0.01;
  p.batch_size = 32;
  p.warmup_steps = 0;
  return p;
}

// ── Existing sweeps (must pass on starter code) ───────────────────────────────

TEST(SweepLearningRate, ProducesOneResultPerLR) {
  auto r = sweep_learning_rate(make_base(), {0.001, 0.01, 0.1});
  EXPECT_EQ(r.configs.size(), 3u);
  EXPECT_EQ(r.results.size(), 3u);
}

TEST(SweepLearningRate, BestIdxMinimisesLoss) {
  auto r = sweep_learning_rate(make_base(7), {0.0001, 0.001, 0.01, 0.1});
  ASSERT_EQ(r.results.size(), 4u);
  for (size_t i = 0; i < r.results.size(); ++i) {
    EXPECT_LE(r.results[r.best_idx].loss, r.results[i].loss);
  }
}

TEST(SweepLearningRate, SummaryCorrect) {
  auto r = sweep_learning_rate(make_base(3), {0.001, 0.01, 0.1});
  ASSERT_EQ(r.results.size(), 3u);
  double mn = r.results[0].loss, mx = r.results[0].loss, sum = 0.0;
  for (auto& res : r.results) {
    sum += res.loss;
    if (res.loss < mn) { mn = res.loss; }
    if (res.loss > mx) { mx = res.loss; }
  }
  EXPECT_NEAR(r.summary.mean, sum / 3.0, 1e-12);
  EXPECT_NEAR(r.summary.min_loss, mn, 1e-12);
  EXPECT_NEAR(r.summary.max_loss, mx, 1e-12);
}

TEST(SweepBatchSizeXLR, ProducesCartesianProduct) {
  auto r = sweep_batch_size_x_lr(make_base(2), {16, 32}, {0.001, 0.01, 0.1});
  EXPECT_EQ(r.results.size(), 6u);
  EXPECT_EQ(r.configs.size(), 6u);
}

TEST(SweepBatchSizeXLR, BestIdxMinimisesLoss) {
  auto r = sweep_batch_size_x_lr(make_base(4), {16, 32, 64}, {0.001, 0.01, 0.1});
  ASSERT_EQ(r.results.size(), 9u);
  for (size_t i = 0; i < r.results.size(); ++i) {
    EXPECT_LE(r.results[r.best_idx].loss, r.results[i].loss);
  }
}

// ── New sweep (must pass after correct implementation) ────────────────────────

TEST(SweepWarmupXLR, ProducesCartesianProduct) {
  auto r = sweep_warmup_x_lr(make_base(5), {0, 50, 100}, {0.001, 0.01});
  ASSERT_EQ(r.results.size(), 6u);
  ASSERT_EQ(r.configs.size(), 6u);
}

TEST(SweepWarmupXLR, Deterministic) {
  auto r1 = sweep_warmup_x_lr(make_base(9), {0, 100}, {0.01, 0.1});
  auto r2 = sweep_warmup_x_lr(make_base(9), {0, 100}, {0.01, 0.1});
  ASSERT_EQ(r1.results.size(), 4u);
  ASSERT_EQ(r2.results.size(), 4u);
  for (size_t i = 0; i < r1.results.size(); ++i) {
    EXPECT_DOUBLE_EQ(r1.results[i].loss, r2.results[i].loss);
  }
}

TEST(SweepWarmupXLR, BestIdxMinimisesLoss) {
  auto r = sweep_warmup_x_lr(make_base(11), {0, 50, 100, 200}, {0.001, 0.01, 0.1});
  ASSERT_EQ(r.results.size(), 12u);
  for (size_t i = 0; i < r.results.size(); ++i) {
    EXPECT_LE(r.results[r.best_idx].loss, r.results[i].loss);
  }
}

TEST(SweepWarmupXLR, ConfigsVaryBothAxes) {
  std::vector<int>    ws = {0, 50};
  std::vector<double> lr = {0.001, 0.01, 0.1};
  auto r = sweep_warmup_x_lr(make_base(13), ws, lr);
  ASSERT_EQ(r.configs.size(), 6u);
  for (const auto& cfg : r.configs) {
    EXPECT_EQ(cfg.seed, make_base(13).seed);
    EXPECT_EQ(cfg.batch_size, make_base(13).batch_size);
  }
  for (int w : ws) {
    for (double l : lr) {
      int found = 0;
      for (const auto& cfg : r.configs) {
        if (cfg.warmup_steps == w && std::fabs(cfg.learning_rate - l) < 1e-15) {
          ++found;
        }
      }
      EXPECT_EQ(found, 1) << "pair (ws=" << w << ", lr=" << l << ") not found exactly once";
    }
  }
}

TEST(SweepWarmupXLR, SummaryCorrect) {
  auto r = sweep_warmup_x_lr(make_base(17), {0, 100}, {0.01, 0.1});
  ASSERT_EQ(r.results.size(), 4u);
  double mn = r.results[0].loss, mx = r.results[0].loss, sum = 0.0;
  for (auto& res : r.results) {
    sum += res.loss;
    if (res.loss < mn) { mn = res.loss; }
    if (res.loss > mx) { mx = res.loss; }
  }
  EXPECT_NEAR(r.summary.mean, sum / 4.0, 1e-12);
  EXPECT_NEAR(r.summary.min_loss, mn, 1e-12);
  EXPECT_NEAR(r.summary.max_loss, mx, 1e-12);
}
