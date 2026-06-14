#include <gtest/gtest.h>

#include <vector>

#include "monitor.h"

using namespace nitr::case025;

TEST(SessionAlertTest, DetectsRangeAlerts) {
  const Config cfg{0.0, 50.0, 100.0};
  const std::vector<Event> events = {
      {"temp", EventKind::Sample, 20.0},  // in range
      {"temp", EventKind::Sample, 60.0},  // above high_bound
      {"temp", EventKind::Sample, -5.0},  // below low_bound
  };
  const Report r = analyze(events, cfg);

  EXPECT_EQ(r.range_alerts.size(), 2u);
  EXPECT_EQ(r.range_alerts[0].channel, "temp");
  EXPECT_EQ(r.range_alerts[0].value, 60.0);
  EXPECT_EQ(r.range_alerts[1].channel, "temp");
  EXPECT_EQ(r.range_alerts[1].value, -5.0);
  EXPECT_TRUE(r.drift_alerts.empty());
  EXPECT_TRUE(r.leak_alerts.empty());
}

TEST(SessionAlertTest, DetectsDriftAlertsWithPerChannelBaseline) {
  const Config cfg{-1000.0, 1000.0, 5.0};
  const std::vector<Event> events = {
      {"a", EventKind::Sample, 10.0},   // baseline a = 10
      {"a", EventKind::Sample, 12.0},   // diff 2, no drift
      {"a", EventKind::Sample, 20.0},   // diff 10, drift
      {"b", EventKind::Sample, 100.0},  // baseline b = 100
      {"b", EventKind::Sample, 108.0},  // diff 8, drift
      {"a", EventKind::Sample, 4.0},    // diff 6, drift
  };
  const Report r = analyze(events, cfg);
  EXPECT_TRUE(r.range_alerts.empty());
  EXPECT_TRUE(r.leak_alerts.empty());
  EXPECT_EQ(r.drift_alerts.size(), 3u);
  EXPECT_EQ(r.drift_alerts[0].channel, "a");
  EXPECT_EQ(r.drift_alerts[0].value, 20.0);
  EXPECT_EQ(r.drift_alerts[0].baseline, 10.0);
  EXPECT_EQ(r.drift_alerts[1].channel, "b");
  EXPECT_EQ(r.drift_alerts[1].value, 108.0);
  EXPECT_EQ(r.drift_alerts[1].baseline, 100.0);
  EXPECT_EQ(r.drift_alerts[2].channel, "a");
  EXPECT_EQ(r.drift_alerts[2].value, 4.0);
  EXPECT_EQ(r.drift_alerts[2].baseline, 10.0);
}

TEST(SessionAlertTest, DetectsLeaksAndSortsByChannel) {
  const Config cfg{-1000.0, 1000.0, 1000.0};
  const std::vector<Event> events = {
      {"x", EventKind::Acquire, 0.0}, {"y", EventKind::Acquire, 0.0},
      {"x", EventKind::Release, 0.0},  // x balanced
      {"z", EventKind::Acquire, 0.0}, {"z", EventKind::Acquire, 0.0},
      {"z", EventKind::Release, 0.0},  // z still open (2 acquire, 1 release)
      {"m", EventKind::Sample, 1.0},   // a sample must not affect leaks
  };
  const Report r = analyze(events, cfg);
  EXPECT_EQ(r.leak_alerts.size(), 2u);
  EXPECT_EQ(r.leak_alerts[0].channel, "y");
  EXPECT_EQ(r.leak_alerts[1].channel, "z");
}

TEST(SessionAlertTest, EnforcesMixedScenarioAndDeterminism) {
  const Config cfg{0.0, 100.0, 10.0};
  const std::vector<Event> events = {
      {"p", EventKind::Acquire, 0.0}, {"p", EventKind::Sample, 50.0},
      {"p", EventKind::Sample, 150.0},  // range (>100) and drift (>10)
      {"q", EventKind::Sample, -3.0},   // range (<0), baseline q = -3
      {"p", EventKind::Release, 0.0},   // p balanced
      {"q", EventKind::Acquire, 0.0},   // q opened, never released -> leak
  };
  const Report r1 = analyze(events, cfg);
  const Report r2 = analyze(events, cfg);

  EXPECT_EQ(r1.range_alerts.size(), 2u);
  EXPECT_EQ(r1.range_alerts[0].channel, "p");
  EXPECT_EQ(r1.range_alerts[0].value, 150.0);
  EXPECT_EQ(r1.range_alerts[1].channel, "q");
  EXPECT_EQ(r1.range_alerts[1].value, -3.0);

  EXPECT_EQ(r1.drift_alerts.size(), 1u);
  EXPECT_EQ(r1.drift_alerts[0].channel, "p");
  EXPECT_EQ(r1.drift_alerts[0].value, 150.0);
  EXPECT_EQ(r1.drift_alerts[0].baseline, 50.0);

  EXPECT_EQ(r1.leak_alerts.size(), 1u);
  EXPECT_EQ(r1.leak_alerts[0].channel, "q");

  EXPECT_EQ(r2.range_alerts.size(), r1.range_alerts.size());
  EXPECT_EQ(r2.drift_alerts.size(), r1.drift_alerts.size());
  EXPECT_EQ(r2.leak_alerts.size(), r1.leak_alerts.size());
  EXPECT_EQ(r2.drift_alerts[0].value, r1.drift_alerts[0].value);
  EXPECT_EQ(r2.leak_alerts[0].channel, r1.leak_alerts[0].channel);
}
