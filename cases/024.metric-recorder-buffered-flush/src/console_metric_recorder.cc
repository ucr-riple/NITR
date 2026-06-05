#include "console_metric_recorder.h"

namespace nitr::case024 {

ConsoleMetricRecorder::ConsoleMetricRecorder(std::ostream& out) : out_(out) {}

void ConsoleMetricRecorder::Record(const Metric& metric) {
  out_ << metric.name << '=' << metric.value << '\n';
}

void ConsoleMetricRecorder::Flush() { out_.flush(); }

}  // namespace nitr::case024
