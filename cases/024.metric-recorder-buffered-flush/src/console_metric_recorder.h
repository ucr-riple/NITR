#ifndef NITR_CASE024_CONSOLE_METRIC_RECORDER_H_
#define NITR_CASE024_CONSOLE_METRIC_RECORDER_H_

#include <ostream>

#include "metric_recorder.h"

namespace nitr::case024 {

class ConsoleMetricRecorder : public MetricRecorder {
 public:
  explicit ConsoleMetricRecorder(std::ostream& out);

  void Record(const Metric& metric) override;

 private:
  std::ostream& out_;
};

}  // namespace nitr::case024

#endif  // NITR_CASE024_CONSOLE_METRIC_RECORDER_H_
