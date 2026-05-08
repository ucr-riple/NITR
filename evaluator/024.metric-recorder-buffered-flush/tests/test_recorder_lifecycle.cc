#include <sstream>
#include <vector>

#include "buffered_metric_recorder.h"
#include "console_metric_recorder.h"
#include "gtest/gtest.h"
#include "metric_collector.h"
#include "metric_recorder.h"

namespace {

using nitr::case024::BufferedMetricRecorder;
using nitr::case024::ConsoleMetricRecorder;
using nitr::case024::Metric;
using nitr::case024::MetricCollector;
using nitr::case024::MetricRecorder;

TEST(ConsoleMetricRecorderTest, RecordWritesEachMetricImmediately) {
  std::ostringstream out;
  ConsoleMetricRecorder recorder(out);

  recorder.Record({"requests", 1.0});
  EXPECT_FALSE(out.str().empty())
      << "ConsoleMetricRecorder must write metrics immediately, "
         "preserving its previous behavior.";

  recorder.Record({"errors", 2.0});
  const std::string output = out.str();
  EXPECT_NE(output.find("requests"), std::string::npos);
  EXPECT_NE(output.find("errors"), std::string::npos);
}

TEST(BufferedMetricRecorderTest, DefersVisibilityBeforeCapacityOrFlush) {
  std::ostringstream out;
  BufferedMetricRecorder recorder(out, /*capacity=*/8);

  recorder.Record({"a", 1.0});
  recorder.Record({"b", 2.0});
  recorder.Record({"c", 3.0});

  EXPECT_TRUE(out.str().empty())
      << "BufferedMetricRecorder must NOT write to the underlying stream "
         "until capacity is reached or Flush is called.";
}

TEST(BufferedMetricRecorderTest, FlushesWhenCapacityIsReached) {
  std::ostringstream out;
  BufferedMetricRecorder recorder(out, /*capacity=*/3);

  recorder.Record({"a", 1.0});
  recorder.Record({"b", 2.0});
  EXPECT_TRUE(out.str().empty()) << "Buffer should still hold first two metrics.";

  recorder.Record({"c", 3.0});
  const std::string output = out.str();
  EXPECT_FALSE(output.empty())
      << "Buffer should have flushed once capacity (3) was reached.";
  EXPECT_NE(output.find('a'), std::string::npos);
  EXPECT_NE(output.find('b'), std::string::npos);
  EXPECT_NE(output.find('c'), std::string::npos);
}

TEST(BufferedMetricRecorderTest, ExplicitFlushMakesQueuedMetricsVisible) {
  std::ostringstream out;
  BufferedMetricRecorder recorder(out, /*capacity=*/100);

  recorder.Record({"queued1", 10.0});
  recorder.Record({"queued2", 20.0});
  ASSERT_TRUE(out.str().empty());

  recorder.Flush();

  const std::string output = out.str();
  EXPECT_NE(output.find("queued1"), std::string::npos);
  EXPECT_NE(output.find("queued2"), std::string::npos);
}

// The keystone test: forces the polymorphic checkpoint path.
// The collector holds a MetricRecorder& reference and must be able to flush
// any concrete recorder without knowing the concrete type.
TEST(MetricCollectorTest, CheckpointFlushesUnderlyingBufferedRecorder) {
  std::ostringstream out;
  BufferedMetricRecorder recorder(out, /*capacity=*/100);

  // Wire the collector through the abstract base reference. This is the
  // production calling convention: callers do not know the concrete recorder.
  MetricRecorder& abstract_ref = recorder;
  MetricCollector collector(abstract_ref);

  const std::vector<double> samples = {1.0, 2.0, 3.0};
  collector.Collect(samples);
  EXPECT_TRUE(out.str().empty())
      << "Buffered recorder should still be holding metrics before checkpoint.";

  collector.Checkpoint();

  const std::string output = out.str();
  EXPECT_NE(output.find("samples.count"), std::string::npos)
      << "Checkpoint must make queued metrics visible through the abstract "
         "recorder reference, without the collector knowing the concrete type.";
  EXPECT_NE(output.find("samples.mean"), std::string::npos);
  EXPECT_NE(output.find("samples.max"), std::string::npos);
}

TEST(MetricCollectorTest, CheckpointIsHarmlessForImmediateRecorder) {
  std::ostringstream out;
  ConsoleMetricRecorder recorder(out);
  MetricCollector collector(recorder);

  collector.Collect({4.0, 5.0});
  const std::string before_checkpoint = out.str();
  EXPECT_FALSE(before_checkpoint.empty())
      << "Console recorder should already have published metrics during Collect.";

  // Checkpoint on an immediate-write recorder must be safe and idempotent.
  // It should not throw, must not corrupt prior output, and need not add
  // any new content.
  collector.Checkpoint();

  const std::string after_checkpoint = out.str();
  EXPECT_GE(after_checkpoint.size(), before_checkpoint.size());
  EXPECT_NE(after_checkpoint.find("samples.count"), std::string::npos);
}

}  // namespace
