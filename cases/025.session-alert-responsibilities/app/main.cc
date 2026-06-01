#include <iostream>
#include <vector>

#include "monitor.h"

int main() {
  using namespace nitr::case025;

  const std::vector<Event> events = {
      {"temp", EventKind::Sample, 20.0},
      {"temp", EventKind::Sample, 80.0},
      {"valve", EventKind::Acquire, 0.0},
      {"temp", EventKind::Sample, 21.0},
  };
  const Config config{0.0, 50.0, 5.0};

  const Report report = analyze(events, config);
  std::cout << "range=" << report.range_alerts.size()
            << " drift=" << report.drift_alerts.size()
            << " leak=" << report.leak_alerts.size() << '\n';
  return 0;
}
