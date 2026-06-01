#ifndef NITR_CASE_025_MONITOR_H
#define NITR_CASE_025_MONITOR_H

#include <string>
#include <vector>

namespace nitr::case025 {

enum class EventKind { Sample, Acquire, Release };

// One telemetry event from a monitoring session.  `value` is meaningful only
// when `kind == Sample`.
struct Event {
  std::string channel;
  EventKind kind = EventKind::Sample;
  double value = 0.0;
};

struct Config {
  double low_bound = 0.0;
  double high_bound = 0.0;
  double drift_tolerance = 0.0;
};

struct RangeAlert {
  std::string channel;
  double value;
};

struct DriftAlert {
  std::string channel;
  double value;
  double baseline;
};

struct LeakAlert {
  std::string channel;
};

struct Report {
  std::vector<RangeAlert> range_alerts;
  std::vector<DriftAlert> drift_alerts;
  std::vector<LeakAlert> leak_alerts;
};

Report analyze(const std::vector<Event>& events, const Config& config);

}  // namespace nitr::case025

#endif  // NITR_CASE_025_MONITOR_H
