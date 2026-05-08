#include "metric_collector.h"

namespace nitr::case024 {

MetricCollector::MetricCollector(MetricRecorder& recorder) : recorder_(recorder) {}

void MetricCollector::Collect(const std::vector<double>& samples) {
  if (samples.empty()) {
    recorder_.Record({"samples.count", 0.0});
    return;
  }

  double sum = 0.0;
  double max_value = samples.front();
  for (double v : samples) {
    sum += v;
    if (v > max_value) max_value = v;
  }

  const double count = static_cast<double>(samples.size());
  recorder_.Record({"samples.count", count});
  recorder_.Record({"samples.mean", sum / count});
  recorder_.Record({"samples.max", max_value});
}

}  // namespace nitr::case024
