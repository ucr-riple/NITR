#include <iostream>
#include <vector>

#include "console_metric_recorder.h"
#include "metric_collector.h"

int main() {
  nitr::case024::ConsoleMetricRecorder recorder(std::cout);
  nitr::case024::MetricCollector collector(recorder);

  const std::vector<double> request_latencies_ms = {12.0, 18.0, 9.5, 22.0, 15.5};
  collector.Collect(request_latencies_ms);

  return 0;
}
