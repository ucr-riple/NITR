#ifndef NITR_CASE024_METRIC_COLLECTOR_H_
#define NITR_CASE024_METRIC_COLLECTOR_H_

#include <vector>

#include "metric_recorder.h"

namespace nitr::case024 {

// Computes derived metrics (count, mean, max) from a batch of raw samples
// and publishes them through a MetricRecorder reference.
class MetricCollector {
 public:
  explicit MetricCollector(MetricRecorder& recorder);

  void Collect(const std::vector<double>& samples);

 private:
  MetricRecorder& recorder_;
};

}  // namespace nitr::case024

#endif  // NITR_CASE024_METRIC_COLLECTOR_H_
