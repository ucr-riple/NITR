#ifndef NITR_CASE024_BUFFERED_METRIC_RECORDER_H_
#define NITR_CASE024_BUFFERED_METRIC_RECORDER_H_

#include <cstddef>
#include <ostream>
#include <vector>

#include "metric_recorder.h"

namespace nitr::case024 {

class BufferedMetricRecorder : public MetricRecorder {
 public:
  BufferedMetricRecorder(std::ostream& out, std::size_t capacity);

  void Record(const Metric& metric) override;
  void Flush() override;

 private:
  std::ostream& out_;
  std::size_t capacity_;
  std::vector<Metric> buffer_;
};

}  // namespace nitr::case024

#endif  // NITR_CASE024_BUFFERED_METRIC_RECORDER_H_
