#ifndef NITR_CASE024_METRIC_RECORDER_H_
#define NITR_CASE024_METRIC_RECORDER_H_

#include <string>

namespace nitr::case024 {

struct Metric {
  std::string name;
  double value;
};

class MetricRecorder {
 public:
  virtual ~MetricRecorder() = default;

  virtual void Record(const Metric& metric) = 0;
};

}  // namespace nitr::case024

#endif  // NITR_CASE024_METRIC_RECORDER_H_
