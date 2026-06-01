#include "monitor.h"

namespace nitr::case025 {

Report analyze(const std::vector<Event>& events, const Config& config) {
  Report report;
  for (const Event& event : events) {
    if (event.kind != EventKind::Sample) {
      continue;
    }
    if (event.value < config.low_bound || event.value > config.high_bound) {
      report.range_alerts.push_back(RangeAlert{event.channel, event.value});
    }
  }
  return report;
}

}  // namespace nitr::case025
