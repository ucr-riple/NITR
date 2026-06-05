#include "buffered_metric_recorder.h"

namespace nitr::case024 {

BufferedMetricRecorder::BufferedMetricRecorder(std::ostream& out,
                                               std::size_t capacity)
    : out_(out), capacity_(capacity == 0 ? 1 : capacity) {
  buffer_.reserve(capacity_);
}

void BufferedMetricRecorder::Record(const Metric& metric) {
  buffer_.push_back(metric);
  if (buffer_.size() >= capacity_) {
    Flush();
  }
}

void BufferedMetricRecorder::Flush() {
  for (const Metric& metric : buffer_) {
    out_ << metric.name << '=' << metric.value << '\n';
  }
  out_.flush();
  buffer_.clear();
}

}  // namespace nitr::case024
