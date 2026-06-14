#include <gtest/gtest.h>

#include <chrono>
#include <filesystem>
#include <fstream>
#include <sstream>
#include <string>
#include <string_view>

#include "handover_packet_preview.h"
#include "handover_packet_writer.h"
#include "shift_tracker.h"

namespace testing {
namespace internal {

void PrintStringTo(const std::string& value, std::ostream* stream) {
  if (value.empty()) {
    *stream << "\"\"";
    return;
  }
  *stream << '"' << value << '"';
}

}  // namespace internal
}  // namespace testing

namespace {

struct PacketOutput {
  std::string preview;
  std::string saved;
  nitr::case020::HandoverPacket packet;
  bool last_row_in_progress;
};

std::string ReadFile(const std::string& path) {
  std::ifstream input(path);
  if (!input) {
    throw std::runtime_error("failed to read file: " + path);
  }
  std::ostringstream buffer;
  buffer << input.rdbuf();
  return buffer.str();
}

std::string ReadExpectedText(const std::string& filename) {
  std::filesystem::path evaluator_dir =
      std::filesystem::path(__FILE__).parent_path();
  const std::filesystem::path expected_path = evaluator_dir / filename;
  std::ifstream input(expected_path);
  if (!input) {
    throw std::runtime_error("failed to read expected fixture: " +
                             expected_path.string());
  }
  std::ostringstream buffer;
  buffer << input.rdbuf();
  return buffer.str();
}

nitr::case020::ShiftTracker BuildInProgressTracker() {
  nitr::case020::ShiftTracker tracker("SHIFT-500");
  tracker.AddCompletedTote("TOTE-100", 4);
  tracker.AddCompletedTote("TOTE-101", 3);
  tracker.StartTote("TOTE-102");
  tracker.ScanPackagesIntoCurrentTote(2);
  return tracker;
}

nitr::case020::ShiftTracker BuildClosedTracker() {
  nitr::case020::ShiftTracker tracker("SHIFT-501");
  tracker.AddCompletedTote("TOTE-200", 5);
  tracker.AddCompletedTote("TOTE-201", 1);
  tracker.StartTote("TOTE-202");
  tracker.ScanPackagesIntoCurrentTote(2);
  tracker.CloseCurrentTote();
  return tracker;
}

PacketOutput BuildPacketOutput(const nitr::case020::ShiftTracker& tracker,
                               const std::string& output_path) {
  PacketOutput result;
  result.preview = nitr::case020::BuildHandoverPacketPreview(tracker);
  result.packet = nitr::case020::SaveHandoverPacket(tracker, output_path);
  result.saved = ReadFile(output_path);
  result.last_row_in_progress = !result.packet.rows.empty() &&
                                result.packet.rows.back().from_in_progress_tote;
  return result;
}

std::string TemporaryOutputPath(const std::string& suffix) {
  const auto now = std::chrono::high_resolution_clock::now().time_since_epoch();
  const auto micros =
      std::chrono::duration_cast<std::chrono::microseconds>(now).count();
  const auto temp = std::filesystem::temp_directory_path() /
                    (suffix + "_" + std::to_string(micros) + ".txt");
  return temp.string();
}

}  // namespace

TEST(HandoverPacketFunctional, PreviewAndSaveWithInProgressTote) {
  const auto output =
      BuildPacketOutput(BuildInProgressTracker(),
                        TemporaryOutputPath("case020_with_in_progress"));

  EXPECT_EQ(
      std::string_view(output.preview),
      std::string_view("Preview for shift SHIFT-500 is not available yet.\n"
                       "Use the saved handover packet for now.\n"));
  EXPECT_EQ(std::string_view(output.saved),
            std::string_view(
                ReadExpectedText("expected_packet_with_in_progress.txt")));
  EXPECT_TRUE(output.last_row_in_progress);
  EXPECT_EQ(output.packet.summary.tote_count, 3);
  EXPECT_EQ(output.packet.summary.package_count, 9);
}

TEST(HandoverPacketFunctional, PreviewAndSaveWithoutInProgressTote) {
  const auto output = BuildPacketOutput(
      BuildClosedTracker(), TemporaryOutputPath("case020_without_in_progress"));

  EXPECT_EQ(
      std::string_view(output.preview),
      std::string_view("Preview for shift SHIFT-501 is not available yet.\n"
                       "Use the saved handover packet for now.\n"));
  EXPECT_EQ(std::string_view(output.saved),
            std::string_view(
                ReadExpectedText("expected_packet_without_in_progress.txt")));
  EXPECT_FALSE(output.last_row_in_progress);
  EXPECT_EQ(output.packet.summary.tote_count, 3);
  EXPECT_EQ(output.packet.summary.package_count, 8);
}

TEST(HandoverPacketFunctional, SequenceStability) {
  auto tracker = BuildInProgressTracker();

  auto first =
      BuildPacketOutput(tracker, TemporaryOutputPath("case020_sequence_first"));
  auto second = BuildPacketOutput(
      tracker, TemporaryOutputPath("case020_sequence_second"));

  EXPECT_EQ(first.preview, second.preview);
  EXPECT_EQ(first.saved, second.saved);
  EXPECT_EQ(first.packet.rows.size(), second.packet.rows.size());
  EXPECT_EQ(first.packet.summary.package_count,
            second.packet.summary.package_count);
}
